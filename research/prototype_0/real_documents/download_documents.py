"""Retrieve selected original research documents and record their provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
HOSTS = {"www.sec.gov", "www.govinfo.gov"}
MAX_BYTES = 32 * 1024 * 1024


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in HOSTS:
        raise ValueError("Only approved official HTTPS source hosts are allowed")


def validate_document(data: bytes, kind: str) -> None:
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Document is empty or exceeds the size limit")
    if kind == "pdf":
        if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-2048:]:
            raise ValueError("Response is not a complete PDF")
    elif kind == "html":
        prefix = data[:16384].lower()
        if b"<html" not in prefix and b"<!doctype html" not in prefix:
            raise ValueError("Response does not appear to be HTML")
        if any(marker in prefix for marker in (
            b"request rate threshold exceeded",
            b"your request originates from an undeclared automated tool",
            b"access denied",
        )):
            raise ValueError("Source returned an access restriction")
    else:
        raise ValueError("Unknown document format")


def fetch(source: dict, user_agent: str, output: Path) -> dict:
    url = source["url"]
    validate_url(url)
    filename = source["filename"]
    if Path(filename).name != filename or filename in {"", ".", ".."}:
        raise ValueError("Invalid local filename")
    request = Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity"})
    with urlopen(request, timeout=60) as response:
        final_url = response.geturl()
        validate_url(final_url)
        if response.status != 200:
            raise ValueError(f"Unexpected HTTP status: {response.status}")
        data = response.read(MAX_BYTES + 1)
        content_type = response.headers.get("Content-Type")
    validate_document(data, source["format"])
    digest = hashlib.sha256(data).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    destination = output / filename
    if destination.exists() and destination.read_bytes() != data:
        raise ValueError(f"Existing file differs from the retrieved source: {filename}")
    destination.write_bytes(data)
    record = {
        **source,
        "resolved_url": final_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "content_type": content_type,
        "bytes": len(data),
        "sha256": digest,
        "availability_verified": False,
        "rights_review": "pending",
    }
    (output / f"{filename}.metadata.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-agent", required=True, help="Genuine organization and contact email")
    parser.add_argument("--format", choices=("pdf", "html"))
    parser.add_argument("--source", help="Source ID from sources.json")
    parser.add_argument("--output", type=Path, default=ROOT / "local_documents")
    args = parser.parse_args()
    if "@" not in args.user_agent or "example.com" in args.user_agent.lower():
        parser.error("Supply a genuine contact email in the user agent")
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))["sources"]
    selected = [
        source for source in sources
        if (args.format is None or source["format"] == args.format)
        and (args.source is None or source["id"] == args.source)
    ]
    if not selected:
        parser.error("No sources match the requested filters")
    errors = 0
    for source in selected:
        try:
            record = fetch(source, args.user_agent, args.output)
            print(f"{record['filename']}: {record['bytes']} bytes, SHA-256 {record['sha256']}")
        except (HTTPError, URLError, OSError, ValueError) as exc:
            print(f"{source['id']}: {exc}")
            errors += 1
            if isinstance(exc, HTTPError) and exc.code in (403, 429, 503):
                print("Stopping after a source access restriction. Use the official browser link.")
                break
        time.sleep(1.0)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Checks for source catalog integrity and document validation."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "real_documents"
sys.path.insert(0, str(ROOT))
from download_documents import validate_document, validate_url


class RealDocumentTests(unittest.TestCase):
    def test_catalog_contains_original_pdf_and_html_sources(self):
        catalog = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
        sources = catalog["sources"]
        self.assertEqual(len(sources), len({source["id"] for source in sources}))
        self.assertEqual(len(sources), len({source["filename"] for source in sources}))
        self.assertEqual({source["format"] for source in sources}, {"html", "pdf"})
        for source in sources:
            validate_url(source["url"])
            validate_url(source["index_url"])
            self.assertTrue(source["filename"].endswith("." + source["format"]))

    def test_pdf_signature_and_completion_required(self):
        validate_document(b"%PDF-1.4\nexample\n%%EOF\n", "pdf")
        for data in (b"", b"<html>Access denied</html>", b"%PDF-1.4"):
            with self.assertRaises(ValueError):
                validate_document(data, "pdf")

    def test_html_access_restrictions_rejected(self):
        validate_document(b"<!DOCTYPE html><html><body>Filing</body></html>", "html")
        with self.assertRaises(ValueError):
            validate_document(b"<html>Request Rate Threshold Exceeded</html>", "html")

    def test_unapproved_hosts_rejected(self):
        for url in ("http://www.sec.gov/test", "https://www.sec.gov.example.com/test"):
            with self.assertRaises(ValueError):
                validate_url(url)


if __name__ == "__main__":
    unittest.main()

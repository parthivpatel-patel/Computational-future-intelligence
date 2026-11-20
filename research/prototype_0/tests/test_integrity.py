"""Adversarial tests for evidence validity and reproducibility."""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototype import analyze, citation, event_sentences, read_data, visible_documents, when


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.docs, self.relations, self.portfolio = read_data()
        self.as_of = "2026-02-12T12:00:00Z"

    def run_analysis(self, *, documents=None, relations=None, portfolio=None, as_of=None):
        return analyze(
            documents if documents is not None else self.docs,
            relations if relations is not None else self.relations,
            portfolio if portfolio is not None else self.portfolio,
            as_of if as_of is not None else self.as_of,
        )

    def test_relationship_quote_must_name_both_parties(self):
        relations = copy.deepcopy(self.relations)
        relations[0]["source_quote"] = "The supply relationship is described here solely for a synthetic software test."
        result = self.run_analysis(relations=relations)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["rejected_unverifiable_relationships_or_events"], 1)

    def test_relationship_quote_must_not_be_negated(self):
        docs = copy.deepcopy(self.docs)
        relations = copy.deepcopy(self.relations)
        docs[0]["body"] = "Northstar Pumps does not purchase anything from Acme Components."
        relations[0]["source_quote"] = docs[0]["body"]
        self.assertEqual(self.run_analysis(documents=docs, relations=relations)["findings"], [])

    def test_relationship_quote_must_not_be_conditional(self):
        docs = copy.deepcopy(self.docs)
        relations = copy.deepcopy(self.relations)
        docs[0]["body"] = "Northstar Pumps might buy components from Acme Components."
        relations[0]["source_quote"] = docs[0]["body"]
        self.assertEqual(self.run_analysis(documents=docs, relations=relations)["findings"], [])

    def test_relationship_direction_is_checked(self):
        documents = copy.deepcopy(self.docs)
        relations = copy.deepcopy(self.relations)
        documents[0]["body"] = "Northstar Pumps supplies Acme Components with valves."
        relations[0]["source_quote"] = documents[0]["body"]
        self.assertEqual(self.run_analysis(documents=documents, relations=relations)["findings"], [])

    def test_unrelated_mentions_are_not_supplier_evidence(self):
        documents = copy.deepcopy(self.docs)
        relations = copy.deepcopy(self.relations)
        documents[0]["body"] = "Northstar Pumps competes with Acme Components in the same industry."
        relations[0]["source_quote"] = documents[0]["body"]
        self.assertEqual(self.run_analysis(documents=documents, relations=relations)["findings"], [])

    def test_supplier_first_direction_is_supported(self):
        documents = copy.deepcopy(self.docs)
        relations = copy.deepcopy(self.relations)
        documents[0]["body"] = "Acme Components supplies precision valves to Northstar Pumps."
        relations[0]["source_quote"] = documents[0]["body"]
        self.assertEqual(len(self.run_analysis(documents=documents, relations=relations)["findings"]), 1)

    def test_no_entity_substring_match(self):
        docs = copy.deepcopy(self.docs)
        docs[1]["body"] = "Acme Components Incorporated halted operations at its campus."
        self.assertEqual(self.run_analysis(documents=docs)["findings"], [])

    def test_conditionals_do_not_become_events(self):
        for text in (
            "If Acme Components halted operations, parts would be delayed.",
            "Acme Components might have disrupted production.",
            "Acme Components denied it suspended operations.",
            "There is no evidence Acme Components disrupted production.",
            "A hypothetical scenario assumes Acme Components shut down the plant.",
            "Acme Components planned to close its facility next year.",
        ):
            with self.subTest(text=text):
                docs = copy.deepcopy(self.docs)
                docs[1]["body"] = text
                self.assertEqual(self.run_analysis(documents=docs)["findings"], [])

    def test_exact_quotes_and_content_fingerprints(self):
        findings = self.run_analysis()["findings"]
        self.assertEqual(len(findings), 1)
        for ref in findings[0]["evidence"].values():
            source = next(d for d in self.docs if d["id"] == ref["document_id"])
            self.assertEqual(source["body"][ref["start"]:ref["end"]], ref["quote"])
            self.assertEqual(hashlib.sha256(source["body"].encode()).hexdigest(), ref["source_sha256"])
            self.assertLessEqual(when(ref["available_at"]), when(self.as_of))
            self.assertLessEqual(when(ref["published_at"]), when(ref["available_at"]))

    def test_empty_and_repeated_quotes_are_not_valid_evidence(self):
        doc = {"id": "x", "title": "x", "url": "synthetic://x", "body": "repeat repeat", "published_at": self.as_of, "available_at": self.as_of, "data_kind": "synthetic_example"}
        self.assertIsNone(citation(doc, ""))
        self.assertIsNone(citation(doc, " "))
        self.assertIsNone(citation(doc, "repeat"))

    def test_duplicate_relationships_do_not_repeat_findings(self):
        relations = self.relations + copy.deepcopy(self.relations)
        result = self.run_analysis(relations=relations)
        self.assertEqual(len(result["findings"]), 1)

    def test_duplicate_documents_rejected_even_if_not_yet_available(self):
        docs = self.docs + [copy.deepcopy(self.docs[-1])]
        with self.assertRaisesRegex(ValueError, "Duplicate document id"):
            self.run_analysis(documents=docs)

    def test_duplicate_holdings_rejected(self):
        portfolio = self.portfolio + copy.deepcopy(self.portfolio)
        with self.assertRaisesRegex(ValueError, "Duplicate portfolio company"):
            self.run_analysis(portfolio=portfolio)

    def test_nonpositive_or_nonfinite_holdings_rejected(self):
        for shares in (0, -2, float("nan"), float("inf"), True, "100"):
            with self.subTest(shares=shares):
                portfolio = copy.deepcopy(self.portfolio)
                portfolio[0]["shares"] = shares
                with self.assertRaisesRegex(ValueError, "shares must be"):
                    self.run_analysis(portfolio=portfolio)

    def test_reject_unknown_or_non_synthetic_provenance(self):
        docs = copy.deepcopy(self.docs)
        docs[1]["data_kind"] = "external_source"
        with self.assertRaisesRegex(ValueError, "synthetic sources only"):
            self.run_analysis(documents=docs)

    def test_publication_must_precede_availability(self):
        docs = copy.deepcopy(self.docs)
        docs[1]["published_at"] = "2026-02-11T09:00:00Z"
        with self.assertRaisesRegex(ValueError, "available before publication"):
            self.run_analysis(documents=docs)

    def test_unknown_relation_types_do_not_generate_findings(self):
        relations = copy.deepcopy(self.relations)
        relations[0]["relation_type"] = "competes_with"
        self.assertEqual(self.run_analysis(relations=relations)["findings"], [])

    def test_iso_offsets_represent_same_instant(self):
        self.assertEqual(when("2026-02-12T12:00:00Z"), when("2026-02-12T07:00:00-05:00"))
        self.assertEqual(self.run_analysis(as_of="2026-02-12T07:00:00-05:00")["findings"],
                         self.run_analysis()["findings"])

    def test_document_and_relationship_order_do_not_change_results(self):
        ordered = self.run_analysis()
        reversed_order = self.run_analysis(
            documents=list(reversed(self.docs)), relations=list(reversed(self.relations))
        )
        self.assertEqual(ordered, reversed_order)

    def test_finding_ids_are_stable_across_replay(self):
        first = self.run_analysis()["findings"]
        second = self.run_analysis()["findings"]
        self.assertEqual(first, second)

    def test_json_fixture_schema_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for filename in ("documents.json", "relationships.json", "portfolio.json"):
                (folder / filename).write_text(json.dumps({"invalid": "root"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "list of JSON objects"):
                read_data(folder)

    def test_precise_as_of_cutoff_boundary(self):
        self.assertEqual(self.run_analysis(as_of="2026-02-10T08:59:59Z")["findings"], [])
        self.assertEqual(len(self.run_analysis(as_of="2026-02-10T09:00:00Z")["findings"]), 1)


if __name__ == "__main__":
    unittest.main()

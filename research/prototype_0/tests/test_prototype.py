import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prototype import analyze, read_data


class PrototypeTests(unittest.TestCase):
    def setUp(self):
        self.docs, self.relations, self.portfolio = read_data()

    def query(self, as_of="2026-02-12T12:00:00Z", docs=None, relations=None):
        return analyze(docs if docs is not None else self.docs,
                       relations if relations is not None else self.relations,
                       self.portfolio, as_of)

    def test_visible_event_and_relationship_produce_cited_finding(self):
        result = self.query()
        self.assertEqual(len(result["findings"]), 1)
        finding = result["findings"][0]
        self.assertEqual(finding["portfolio_ticker"], "NSTP-SYNTHETIC")
        for item in finding["evidence"].values():
            document = next(d for d in self.docs if d["id"] == item["document_id"])
            self.assertEqual(document["body"][item["start"]:item["end"]], item["quote"])

    def test_no_future_information_in_historical_replay(self):
        result = self.query("2026-02-09T12:00:00Z")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["visible_document_count"], 1)
        self.assertEqual(len(self.query()["findings"]), 1)

    def test_missing_relationship_quote_abstains(self):
        relations = copy.deepcopy(self.relations)
        relations[0]["source_quote"] = "This sentence is not in the document."
        result = self.query(relations=relations)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["rejected_unverifiable_relationships_or_events"], 1)

    def test_unrelated_document_does_not_trigger(self):
        docs = [d for d in self.docs if d["id"] != "synthetic-plant-event"]
        self.assertEqual(self.query(docs=docs)["findings"], [])

    def test_unavailable_relationship_cannot_be_used(self):
        docs = copy.deepcopy(self.docs)
        docs[0]["available_at"] = "2026-02-15T10:00:00Z"
        docs[0]["published_at"] = "2026-02-15T08:00:00Z"
        self.assertEqual(self.query(docs=docs)["findings"], [])

    def test_negated_event_is_not_finding(self):
        docs = copy.deepcopy(self.docs)
        docs[1]["body"] = "Acme Components reported no disrupted deliveries to customers."
        self.assertEqual(self.query(docs=docs)["findings"], [])

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            self.query("2026-02-12T12:00:00")

    def test_data_are_marked_synthetic(self):
        self.assertTrue(all(d["data_kind"] == "synthetic_example" for d in self.docs))
        self.assertTrue(all(d["url"].startswith("synthetic://") for d in self.docs))


if __name__ == "__main__":
    unittest.main()

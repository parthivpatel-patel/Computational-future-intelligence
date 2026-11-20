"""Synthetic regression cases and evaluation harness safeguards."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate_baseline import evaluate


class EvaluationTests(unittest.TestCase):
    def test_synthetic_regression_dataset_passes(self):
        report = evaluate()
        self.assertGreaterEqual(report["total_cases"], 20)
        self.assertEqual(report["failures"], [])
        self.assertGreater(report["true_positive"], 0)
        self.assertGreater(report["true_negative"], 0)

    def test_benchmark_detects_misclassified_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps([{
                "id": "known_mismatch", "subject": "Acme Components",
                "sentence": "Acme Components halted production.", "expected": False,
            }]), encoding="utf-8")
            report = evaluate(path)
            self.assertEqual(report["failures"][0]["id"], "known_mismatch")
            self.assertEqual(report["false_positive"], 1)

    def test_benchmark_requires_boolean_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps([{
                "id": "case", "subject": "Acme Components",
                "sentence": "Acme Components halted production.", "expected": 1,
            }]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "boolean"):
                evaluate(path)


if __name__ == "__main__":
    unittest.main()

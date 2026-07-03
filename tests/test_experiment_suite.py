import csv
import os
import tempfile
import unittest

from algorithms.baseline import BaselineRouting
from experiments.experiment_config import ExperimentConfig
from experiments.experiment_suite import ExperimentSuite
from experiments.report_generator import ExperimentReportGenerator


class ExperimentSuiteTests(unittest.TestCase):
    def test_config_yields_expected_configurations(self):
        config = ExperimentConfig(
            node_counts=[10, 20],
            failure_probabilities=[0.0, 0.1],
            packet_count=5,
            trials=2,
            routing_strategy=BaselineRouting,
            random_seed=7,
        )

        configurations = list(config.iter_configurations())
        self.assertEqual(len(configurations), 4)
        self.assertEqual(configurations[0]["node_count"], 10)
        self.assertEqual(configurations[0]["failure_probability"], 0.0)

    def test_suite_writes_trial_and_summary_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = ExperimentConfig(
                node_counts=[3],
                failure_probabilities=[0.0],
                packet_count=2,
                trials=2,
                routing_strategy=BaselineRouting,
                random_seed=11,
                output_dir=tmp_dir,
            )
            suite = ExperimentSuite(config=config)
            summary_rows = suite.run()

            self.assertEqual(len(summary_rows), 1)
            trial_csv = os.path.join(tmp_dir, "baselinerouting_n3_p0.0.csv")
            summary_csv = os.path.join(tmp_dir, "summary_baselinerouting_n3_p0.0.csv")
            self.assertTrue(os.path.exists(trial_csv))
            self.assertTrue(os.path.exists(summary_csv))

            with open(trial_csv, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertIn("Trial", rows[0].keys())

    def test_report_generator_prints_summary(self):
        report = ExperimentReportGenerator()
        summary = {
            "strategy": "Baseline",
            "nodes": 10,
            "failure_probability": 0.1,
            "packet_delivery_ratio": {"mean": 50.0, "ci95": 5.0},
            "average_hop_count": {"mean": 3.5},
            "repairs": {"mean": 1.0},
        }

        formatted = report.render_summary(summary)
        self.assertIn("Strategy : Baseline", formatted)
        self.assertIn("Nodes : 10", formatted)
        self.assertIn("95% CI", formatted)

    def test_suite_uses_sample_variance_and_stddev_for_summary_statistics(self):
        config = ExperimentConfig(
            node_counts=[3],
            failure_probabilities=[0.0],
            packet_count=1,
            trials=1,
            routing_strategy=BaselineRouting,
            output_dir=".",
        )
        suite = ExperimentSuite(config=config)

        self.assertEqual(suite._variance([1.0, 2.0, 3.0]), 1.0)
        self.assertEqual(suite._stddev([1.0, 2.0, 3.0]), 1.0)
        self.assertAlmostEqual(suite._confidence_interval([1.0, 2.0, 3.0]), 1.1316065276116665, places=12)


if __name__ == "__main__":
    unittest.main()

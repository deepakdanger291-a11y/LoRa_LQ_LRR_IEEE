import unittest

from metrics.metrics import Metrics
from core.packet import PacketOutcome


class MetricsStatisticsTests(unittest.TestCase):
    def test_hop_statistics_are_computed_from_delivered_packets(self):
        metrics = Metrics()
        metrics.record_outcome(PacketOutcome.DELIVERED, hops=2)
        metrics.record_outcome(PacketOutcome.RECOVERED, hops=4)
        metrics.record_outcome(PacketOutcome.DELIVERED, hops=6)

        self.assertEqual(metrics.mean_hop_count(), 4.0)
        self.assertEqual(metrics.variance_hop_count(), 4.0)
        self.assertAlmostEqual(metrics.stddev_hop_count(), 1.632993161855452)

    def test_hop_statistics_return_zero_when_no_delivered_packets_exist(self):
        metrics = Metrics()

        self.assertEqual(metrics.mean_hop_count(), 0.0)
        self.assertEqual(metrics.variance_hop_count(), 0.0)
        self.assertEqual(metrics.stddev_hop_count(), 0.0)


if __name__ == "__main__":
    unittest.main()

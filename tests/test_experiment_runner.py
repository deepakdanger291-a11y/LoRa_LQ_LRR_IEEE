import unittest

from algorithms.routing_strategy import RoutingStrategy
from core.packet import Packet
from experiments.experiment_runner import ExperimentRunner


class StatefulStrategy(RoutingStrategy):
    def __init__(self):
        self.calls = 0

    def route_packet(self, network, packet: Packet, destination: str) -> bool:
        self.calls += 1
        packet.visit(packet.source)
        packet.visit(destination)
        packet.mark_delivered()
        return True


class ExperimentRunnerTests(unittest.TestCase):
    def test_runner_uses_a_fresh_strategy_instance_per_trial(self):
        strategy = StatefulStrategy()
        runner = ExperimentRunner(trials=2)

        runner.run_experiments(
            node_count=3,
            packet_count=1,
            failure_probability=0.0,
            random_seed=11,
            routing_strategy=strategy,
        )

        self.assertEqual(strategy.calls, 0)


if __name__ == "__main__":
    unittest.main()

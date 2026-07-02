import unittest

from algorithms.routing_strategy import RoutingStrategy
from core.packet import Packet
from experiments.experiment_context import (
    DestinationPolicy,
    ExperimentContext,
    FailureSchedule,
    LinkSpec,
    NodeSpec,
    PacketSchedule,
    PacketSpec,
    RoutingStateSpec,
    RouteSpec,
    SourcePolicy,
    TopologySpec,
)
from network.network import Network
from simulation.simulation_engine import SimulationEngine


class DummyStrategy(RoutingStrategy):
    def route_packet(self, network, packet: Packet, destination: str) -> bool:
        packet.visit(packet.source)
        packet.visit(destination)
        packet.mark_delivered()
        return True


class ExperimentContextTests(unittest.TestCase):
    def test_simulation_engine_uses_context_to_build_runtime_state(self):
        context = ExperimentContext(
            trial_id=1,
            node_count=2,
            packet_count=1,
            failure_probability=0.0,
            random_seed=7,
            topology=TopologySpec(
                topology_id="tiny",
                nodes=(NodeSpec("1"), NodeSpec("2")),
                links=(LinkSpec("1", "2", 0.9, True),),
            ),
            routing_state=RoutingStateSpec(
                routes=(RouteSpec(destination="2", primary_next_hop="2", backup_next_hop=None, primary_quality=0.9),)
            ),
            failure_schedule=FailureSchedule(events=()),
            packet_schedule=PacketSchedule(
                packets=(PacketSpec(packet_id=1, source="1", destination="2", payload="ctx", generation_step=0),)
            ),
            source_policy=SourcePolicy(mode="fixed", candidates=("1",)),
            destination_policy=DestinationPolicy(mode="fixed", candidates=("2",)),
            experiment_duration=1,
        )

        engine = SimulationEngine(network=None, strategy=DummyStrategy(), context=context)
        result = engine.run(packet_count=None, failure_probability=0.0)

        self.assertEqual(result.packets_sent, 1)
        self.assertEqual(result.packets_delivered, 1)
        self.assertIsNotNone(engine.network.routing_table.get_route("2"))


if __name__ == "__main__":
    unittest.main()

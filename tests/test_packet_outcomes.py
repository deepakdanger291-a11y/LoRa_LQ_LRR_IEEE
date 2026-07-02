import unittest

from algorithms.baseline import BaselineRouting
from algorithms.lq_lrr import LQLocalRouteRepair
from core.packet import Packet, PacketOutcome
from core.node import Node
from network.network import Network


class PacketOutcomeTests(unittest.TestCase):
    def test_baseline_marks_dropped(self):
        packet = Packet(packet_id=1, source="A", destination="C", payload="x")
        strategy = BaselineRouting()
        strategy.route_packet(None, packet, "C")
        self.assertEqual(packet.outcome, PacketOutcome.DROPPED)

    def test_lq_lrr_marks_unreachable_without_route(self):
        network = Network()
        network.add_node(Node("A"))
        network.add_node(Node("B"))
        packet = Packet(packet_id=2, source="A", destination="C", payload="x")
        strategy = LQLocalRouteRepair(network.routing_table)
        strategy.route_packet(network, packet, "C")
        self.assertEqual(packet.outcome, PacketOutcome.UNREACHABLE)

    def test_lq_lrr_marks_recovered_after_repair(self):
        network = Network()
        network.add_node(Node("A"))
        network.add_node(Node("B"))
        network.add_node(Node("C"))
        network.connect("A", "B", 0.95)
        network.connect("B", "C", 0.92)
        network.routing_table.add_route("C", "B", "C", 0.95, 0.92)
        network.disconnect("B", "C")
        packet = Packet(packet_id=3, source="A", destination="C", payload="x")
        strategy = LQLocalRouteRepair(network.routing_table)
        strategy.route_packet(network, packet, "C")
        self.assertEqual(packet.outcome, PacketOutcome.RECOVERED)

    def test_lq_lrr_marks_failed_when_repair_fails(self):
        network = Network()
        network.add_node(Node("A"))
        network.add_node(Node("B"))
        network.add_node(Node("C"))
        network.connect("A", "B", 0.95)
        network.routing_table.add_route("C", "B", None, 0.95, 0.0)
        packet = Packet(packet_id=4, source="A", destination="C", payload="x")
        strategy = LQLocalRouteRepair(network.routing_table)
        strategy.route_packet(network, packet, "C")
        self.assertEqual(packet.outcome, PacketOutcome.FAILED)


if __name__ == "__main__":
    unittest.main()

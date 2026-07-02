import unittest

from algorithms.routing_strategy import RoutingStrategy
from core.packet import Packet
from network.network import Network
from core.node import Node


class DummyStrategy(RoutingStrategy):
    def route_packet(self, network, packet: Packet, destination: str) -> bool:
        packet.visit(packet.source)
        packet.visit(destination)
        packet.mark_delivered()
        return True


class PacketLifecycleTests(unittest.TestCase):
    def test_reusing_the_same_packet_object_does_not_leak_history(self):
        network = Network()
        network.add_node(Node("A"))
        network.add_node(Node("B"))
        network.add_node(Node("C"))
        network.connect("A", "B", 0.95)
        network.connect("B", "C", 0.92)
        network.routing_table.add_route(
            destination="C",
            primary="B",
            backup=None,
            primary_quality=0.95,
            backup_quality=0.0,
        )
        network.set_routing_strategy(DummyStrategy())

        packet = Packet(packet_id=1, source="A", destination="C", payload="test")

        network.send_packet(packet, "C")
        self.assertEqual(packet.path, ["A", "C"])
        self.assertEqual(packet.hop_count, 2)
        self.assertTrue(packet.delivered)

        network.send_packet(packet, "C")
        self.assertEqual(packet.path, ["A", "C"])
        self.assertEqual(packet.hop_count, 2)
        self.assertTrue(packet.delivered)


if __name__ == "__main__":
    unittest.main()

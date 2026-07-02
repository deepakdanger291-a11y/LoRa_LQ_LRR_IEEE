from core.packet import Packet
from algorithms.routing_strategy import RoutingStrategy


class BaselineRouting(RoutingStrategy):
    """Baseline routing strategy that preserves the original behavior."""

    def route_packet(self, network, packet: Packet, destination: str) -> bool:
        """Route a packet using the baseline behavior."""
        print("\n===== BASELINE ROUTING =====")

        print("\nSending Packet...")

        packet.visit("A")
        packet.visit("B")

        print("Packet reached Node A")
        print("Packet reached Node B")

        print("\n*** LINK FAILURE DETECTED ***")
        print("B -> C is unavailable")

        print("\nPacket Dropped!")

        return False

    def send_packet(self, packet: Packet):
        """Backward-compatible wrapper for the original baseline API."""
        return self.route_packet(None, packet, packet.destination)
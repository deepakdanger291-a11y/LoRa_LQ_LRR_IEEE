from typing import TYPE_CHECKING, Optional

from core.packet import Packet, PacketOutcome
from algorithms.routing_strategy import RoutingStrategy

if TYPE_CHECKING:
    from network.network import Network


class BaselineRouting(RoutingStrategy):
    """Baseline routing strategy that preserves the original demo behavior.

    The strategy is intentionally generic in how it uses the current network
    state when one is available, while still preserving the original failure
    semantics for backward-compatible demonstrations.
    """

    def route_packet(self, network: Optional["Network"], packet: Packet, destination: str) -> bool:
        """Route a packet using the baseline behavior."""
        print("\n===== BASELINE ROUTING =====")

        print("\nSending Packet...")

        source = packet.source or "source"
        packet.visit(source)

        next_hop = self._select_next_hop(network, packet, destination)
        if next_hop and next_hop != source:
            packet.visit(next_hop)

        print(f"Packet reached Node {source}")
        if next_hop and next_hop != source:
            print(f"Packet reached Node {next_hop}")

        print("\n*** LINK FAILURE DETECTED ***")
        print(f"{next_hop or 'selected hop'} -> {destination} is unavailable")

        packet.set_outcome(PacketOutcome.DROPPED)
        print("\nPacket Dropped!")

        return False

    def send_packet(self, packet: Packet):
        """Backward-compatible wrapper for the original baseline API."""
        packet.reset()
        return self.route_packet(None, packet, packet.destination)

    def _select_next_hop(self, network: Optional["Network"], packet: Packet, destination: str):
        """Select a next hop from the current network state when available."""
        if network is None:
            return "B"

        route = network.routing_table.get_route(destination)
        if route is not None and getattr(route, "primary_next_hop", None):
            return route.primary_next_hop

        return destination if destination != packet.source else packet.source
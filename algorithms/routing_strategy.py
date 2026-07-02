"""Abstract interface for routing strategies used by the simulator."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.packet import Packet
    from network.network import Network


class RoutingStrategy(ABC):
    """Define the contract for routing behavior in the simulator."""

    @abstractmethod
    def route_packet(self, network: "Network", packet: "Packet", destination: str) -> bool:
        """Route a packet toward a destination and update its state."""
        raise NotImplementedError

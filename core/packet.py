"""
Packet model for the LoRa Mesh Network Simulator.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PacketOutcome(str, Enum):
    """Explicit final outcomes for a packet transmission."""

    DELIVERED = "DELIVERED"
    DROPPED = "DROPPED"
    FAILED = "FAILED"
    RECOVERED = "RECOVERED"
    UNREACHABLE = "UNREACHABLE"


@dataclass
class Packet:
    """
    Represents a packet travelling through the mesh network.
    """

    packet_id: int
    source: str
    destination: str
    payload: str

    current_node: str = ""
    hop_count: int = 0
    delivered: bool = False
    outcome: Optional[PacketOutcome] = None

    path: List[str] = field(default_factory=list)

    def visit(self, node_id: str):
        """
        Record that the packet has reached a node.
        """
        self.current_node = node_id
        self.path.append(node_id)
        self.hop_count += 1

    def mark_delivered(self):
        """
        Mark the packet as successfully delivered.
        """
        self.set_outcome(PacketOutcome.DELIVERED)

    def set_outcome(self, outcome: PacketOutcome):
        """Set the explicit final outcome for the packet."""
        if isinstance(outcome, str):
            outcome = PacketOutcome(outcome)
        self.outcome = outcome
        self.delivered = outcome in {PacketOutcome.DELIVERED, PacketOutcome.RECOVERED}

    def reset(self):
        """Reset transient transmission state so the packet can be reused safely."""
        self.current_node = ""
        self.hop_count = 0
        self.delivered = False
        self.outcome = None
        self.path = []

    def __str__(self):
        return (
            f"Packet("
            f"id={self.packet_id}, "
            f"src={self.source}, "
            f"dst={self.destination}, "
            f"hops={self.hop_count}, "
            f"delivered={self.delivered})"
        )
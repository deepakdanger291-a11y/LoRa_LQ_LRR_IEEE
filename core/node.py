"""
Node model for the LoRa Mesh Network Simulator.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from core.packet import Packet


@dataclass
class Node:
    """
    Represents one mesh node.
    """

    node_id: str

    neighbours: Dict[str, float] = field(default_factory=dict)
    received_packets: List[int] = field(default_factory=list)

    def add_neighbour(self, neighbour: str, link_quality: float):
        """
        Add or update a neighbouring node.
        """
        self.neighbours[neighbour] = link_quality

    def receive_packet(self, packet: Packet):
        """
        Receive a packet.
        """
        packet.visit(self.node_id)
        self.received_packets.append(packet.packet_id)

    def has_neighbour(self, neighbour: str) -> bool:
        return neighbour in self.neighbours

    def get_link_quality(self, neighbour: str):

        return self.neighbours.get(neighbour, 0.0)

    def __str__(self):

        return (
            f"Node("
            f"id={self.node_id}, "
            f"neighbours={list(self.neighbours.keys())}"
            f")"
        )
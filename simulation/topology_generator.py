"""Utilities for generating random connected mesh topologies."""

import random
from typing import Optional

from core.link import Link
from core.node import Node
from network.network import Network


class TopologyGenerator:
    """Generate random connected mesh topologies for simulation experiments.

    The generator builds a network with a configurable number of nodes,
    random connectivity, and random link quality values. It also guarantees
    that the generated topology is connected by repairing any disconnected
    components with additional links.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize the generator with an optional random seed."""
        self.random = random.Random(seed)

    def generate_topology(
        self,
        num_nodes: int,
        connection_probability: float,
        min_link_quality: float,
        max_link_quality: float,
        seed: Optional[int] = None,
    ) -> Network:
        """Create a connected network topology.

        Args:
            num_nodes: Total number of nodes to create.
            connection_probability: Probability of creating a link between
                any pair of nodes during the initial random pass.
            min_link_quality: Minimum quality assigned to a generated link.
            max_link_quality: Maximum quality assigned to a generated link.
            seed: Optional seed used to override the generator's default seed.

        Returns:
            A fully initialized Network object containing generic nodes and
            links.
        """
        if num_nodes <= 0:
            raise ValueError("num_nodes must be greater than zero")
        if not 0.0 <= connection_probability <= 1.0:
            raise ValueError("connection_probability must be between 0 and 1")
        if min_link_quality > max_link_quality:
            raise ValueError("min_link_quality cannot exceed max_link_quality")

        if seed is not None:
            self.random = random.Random(seed)

        network = Network()
        if not hasattr(network, "links"):
            network.links = []

        for node_id in range(1, num_nodes + 1):
            network.add_node(Node(str(node_id)))

        node_ids = [str(node_id) for node_id in range(1, num_nodes + 1)]

        for index, source in enumerate(node_ids):
            for destination in node_ids[index + 1 :]:
                if self.random.random() < connection_probability:
                    quality = self.random.uniform(min_link_quality, max_link_quality)
                    self._add_link(network, source, destination, quality)

        self._ensure_connectivity(network, node_ids)
        return network

    def _add_link(self, network: Network, source: str, destination: str, quality: float) -> None:
        """Add a bidirectional link between two nodes."""
        if source == destination:
            return

        network.nodes[source].add_neighbour(destination, quality)
        network.nodes[destination].add_neighbour(source, quality)

        link = Link(source, destination, quality, True, 0)
        network.links.append(link)

    def _ensure_connectivity(self, network: Network, node_ids: list[str]) -> None:
        """Ensure the generated topology is connected by adding links if needed."""
        visited = set()
        stack = [node_ids[0]]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for neighbour in network.nodes[current].neighbours:
                if neighbour not in visited:
                    stack.append(neighbour)

        if len(visited) == len(node_ids):
            return

        for source in node_ids:
            if source in visited:
                continue

            for destination in node_ids:
                if destination in visited and destination != source:
                    quality = self.random.uniform(0.5, 1.0)
                    self._add_link(network, source, destination, quality)
                    visited.add(source)
                    break

            if len(visited) == len(node_ids):
                break

    def __str__(self) -> str:
        """Return a short description of the generator."""
        return "TopologyGenerator"

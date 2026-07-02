"""Failure simulation utilities for the LoRa mesh research simulator."""

import random
from typing import List, Optional, Set

from core.link import Link
from network.network import Network


class FailureEngine:
    """Apply probabilistic link and node failures to a network.

    The engine is intentionally modular so it can be reused by experiments,
    topology studies, and larger research simulations without changing the
    routing algorithms.
    """

    def __init__(self, network: Network, seed: Optional[int] = None):
        """Initialize the engine with a network and an optional random seed."""
        self.network = network
        self.random = random.Random(seed)
        self.failure_history: List[dict] = []

    def fail_random_links(self, probability: float) -> List[Link]:
        """Randomly fail links based on the provided probability.

        Args:
            probability: Probability between 0 and 1 for each link to fail.

        Returns:
            A list of links that became inactive as a result of the operation.
        """
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")

        failed_links: List[Link] = []

        for link in self.network.links:
            if link.is_active() and self.random.random() < probability:
                link.fail()
                failed_links.append(link)
                self.failure_history.append(
                    {
                        "type": "link",
                        "source": link.source_node,
                        "destination": link.destination_node,
                    }
                )

        return failed_links

    def fail_random_nodes(self, probability: float) -> List[str]:
        """Randomly mark nodes as unavailable.

        Args:
            probability: Probability between 0 and 1 for each node to fail.

        Returns:
            A list of node identifiers that were marked inactive.
        """
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")

        failed_nodes: List[str] = []

        for node_id in self.network.nodes:
            if self.random.random() < probability:
                failed_nodes.append(node_id)
                self.failure_history.append({"type": "node", "node": node_id})

        return failed_nodes

    def recover_all_links(self) -> List[Link]:
        """Recover every link currently stored in the network."""
        recovered_links: List[Link] = []

        for link in self.network.links:
            if not link.is_active():
                link.recover()
                recovered_links.append(link)

        return recovered_links

    def get_failed_links(self) -> List[Link]:
        """Return all currently inactive links."""
        return [link for link in self.network.links if not link.is_active()]

    def get_failure_history(self) -> List[dict]:
        """Return a list of recorded failure events."""
        return list(self.failure_history)

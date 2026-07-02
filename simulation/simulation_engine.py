"""Simulation engine for running packet-level experiments on a network."""

from dataclasses import dataclass
from typing import List, Optional

from algorithms.routing_strategy import RoutingStrategy
from core.packet import Packet
from network.network import Network
from simulation.failure_engine import FailureEngine
from metrics.metrics import Metrics


@dataclass
class ExperimentResult:
    """Store aggregate results from a completed simulation run."""

    packets_sent: int
    packets_delivered: int
    packets_failed: int
    packet_delivery_ratio: float
    average_hop_count: float
    repairs: int
    failed_links: int


class SimulationEngine:
    """Run automated packet transmissions over a network.

    The engine accepts a network instance and a routing strategy, applies
    optional random failures before each transmission, and collects metrics for
    research-style experiments. It preserves the original simple behavior while
    relying on the current network state and the selected routing strategy.
    """

    def __init__(self, network: Network, strategy: RoutingStrategy):
        """Initialize the engine with a network and a routing strategy."""
        self.network = network
        self.strategy = strategy
        self.failure_engine = FailureEngine(network)
        self.metrics = Metrics()

    def run(
        self,
        packet_count: int,
        failure_probability: float = 0.0,
        source_node: Optional[str] = None,
        destination_nodes: Optional[List[str]] = None,
        seed: Optional[int] = None,
        payload: str = "sim",
    ) -> ExperimentResult:
        """Run a simulation over a configurable number of packets.

        Args:
            packet_count: Number of packets to transmit.
            failure_probability: Probability of link failure before each send.
            source_node: Optional source node for generated packets.
            destination_nodes: Optional list of destination candidates.
            seed: Optional seed for deterministic behavior.

        Returns:
            An ExperimentResult containing the aggregate outcomes.
        """
        if packet_count <= 0:
            raise ValueError("packet_count must be greater than zero")
        if not 0.0 <= failure_probability <= 1.0:
            raise ValueError("failure_probability must be between 0 and 1")

        if seed is not None:
            self.failure_engine = FailureEngine(self.network, seed=seed)

        if source_node is None:
            source_node = self._select_source_node()
        if destination_nodes is None:
            destination_nodes = self._select_destination_nodes(source_node)

        for packet_id in range(1, packet_count + 1):
            self.failure_engine.fail_random_links(failure_probability)

            source = source_node
            destination = self._select_destination(destination_nodes, source)
            packet = Packet(packet_id=packet_id, source=source, destination=destination, payload=payload)

            self._send_packet(packet, destination)

        return self._build_result()

    def _send_packet(self, packet: Packet, destination: str) -> None:
        """Send one packet using the selected routing strategy."""
        self.metrics.packet_sent()

        previous_route = self.network.routing_table.get_route(destination)
        previous_primary_hop = getattr(previous_route, "primary_next_hop", None)

        success = self.strategy.route_packet(self.network, packet, destination)
        if success:
            updated_route = self.network.routing_table.get_route(destination)
            updated_primary_hop = getattr(updated_route, "primary_next_hop", None)
            if updated_primary_hop != previous_primary_hop:
                self.metrics.repair_success()
            self.metrics.packet_delivered(packet.hop_count)
        else:
            self.metrics.packet_failed()

    def _should_repair(self, route) -> bool:
        """Return whether a repair should be attempted before delivery."""
        if getattr(route, "primary_next_hop", None) is None:
            return False
        if route.primary_next_hop not in self.network.nodes:
            return True
        return False

    def _select_source_node(self) -> str:
        """Select the first available node as the default source."""
        if not self.network.nodes:
            raise ValueError("network must contain at least one node")
        return next(iter(self.network.nodes))

    def _select_destination_nodes(self, source_node: str) -> List[str]:
        """Return candidate destinations excluding the source node."""
        return [node_id for node_id in self.network.nodes if node_id != source_node]

    def _select_destination(self, destination_nodes: List[str], source_node: str) -> str:
        """Select a destination node from the available candidates."""
        if not destination_nodes:
            raise ValueError("network must contain at least two nodes")
        if len(destination_nodes) == 1:
            return destination_nodes[0]
        return destination_nodes[(self.failure_engine.random.randrange(len(destination_nodes)))]

    def _build_result(self) -> ExperimentResult:
        """Build an aggregate result object from the collected metrics."""
        total_packets = self.metrics.total_packets
        delivered_packets = self.metrics.delivered_packets
        failed_packets = self.metrics.failed_packets
        average_hops = (
            self.metrics.total_hops / delivered_packets
            if delivered_packets > 0
            else 0.0
        )

        return ExperimentResult(
            packets_sent=total_packets,
            packets_delivered=delivered_packets,
            packets_failed=failed_packets,
            packet_delivery_ratio=(delivered_packets / total_packets * 100 if total_packets else 0.0),
            average_hop_count=average_hops,
            repairs=self.metrics.route_repairs,
            failed_links=len(self.failure_engine.get_failed_links()),
        )

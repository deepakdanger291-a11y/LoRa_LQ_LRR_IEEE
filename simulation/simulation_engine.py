"""Simulation engine for running packet-level experiments on a network."""

from dataclasses import dataclass
from typing import List, Optional

from algorithms.routing_strategy import RoutingStrategy
from core.node import Node
from core.packet import Packet, PacketOutcome
from core.routing_table import RouteEntry
from network.network import Network
from simulation.failure_engine import FailureEngine
from metrics.metrics import Metrics
from experiments.experiment_context import ExperimentContext


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

    def __init__(
        self,
        network: Optional[Network],
        strategy: RoutingStrategy,
        context: Optional[ExperimentContext] = None,
    ):
        """Initialize the engine with a network and a routing strategy."""
        if context is not None:
            context.validate()
            self.context = context
            self.network = self._build_network_from_context(context)
        else:
            if network is None:
                raise ValueError("network must be provided when no context is supplied")
            self.context = None
            self.network = network

        self.strategy = strategy
        self.failure_engine = FailureEngine(self.network)
        self.metrics = Metrics()

    def run(
        self,
        packet_count: Optional[int] = None,
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
        if packet_count is None and self.context is None:
            raise ValueError("packet_count must be provided when no context is supplied")
        if packet_count is None:
            packet_count = len(self.context.packet_schedule.packets)

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

            if self.context is not None:
                packet_spec = self.context.packet_schedule.packets[packet_id - 1]
                packet = Packet(
                    packet_id=packet_spec.packet_id,
                    source=packet_spec.source,
                    destination=packet_spec.destination,
                    payload=packet_spec.payload,
                )
                source = packet.source
                destination = packet.destination

            self._send_packet(packet, destination)

        return self._build_result()

    def _send_packet(self, packet: Packet, destination: str) -> None:
        """Send one packet using the selected routing strategy."""
        packet.reset()
        self.metrics.packet_sent()

        previous_route = self.network.routing_table.get_route(destination)
        previous_primary_hop = getattr(previous_route, "primary_next_hop", None)

        success = self.strategy.route_packet(self.network, packet, destination)
        if success:
            updated_route = self.network.routing_table.get_route(destination)
            updated_primary_hop = getattr(updated_route, "primary_next_hop", None)
            if updated_primary_hop != previous_primary_hop:
                self.metrics.repair_success()
            if packet.outcome is None:
                packet.set_outcome(PacketOutcome.DELIVERED)
            self.metrics.record_outcome(packet.outcome, packet.hop_count)
        else:
            if packet.outcome is None:
                packet.set_outcome(PacketOutcome.FAILED)
            self.metrics.record_outcome(packet.outcome, packet.hop_count)

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

    def _build_network_from_context(self, context: ExperimentContext) -> Network:
        """Create a network instance from an immutable experiment context."""
        network = Network()
        for node_spec in context.topology.nodes:
            network.add_node(Node(node_spec.node_id))

        for link_spec in context.topology.links:
            network.connect(link_spec.source, link_spec.destination, link_spec.quality)
            if not link_spec.initial_active:
                network.disconnect(link_spec.source, link_spec.destination)

        for route_spec in context.routing_state.routes:
            network.routing_table.add_route(
                destination=route_spec.destination,
                primary=route_spec.primary_next_hop,
                backup=route_spec.backup_next_hop,
                primary_quality=route_spec.primary_quality,
                backup_quality=route_spec.backup_quality,
            )

        network.routing_table.routes = {
            destination: RouteEntry(
                destination=route.destination,
                primary_next_hop=route.primary_next_hop,
                backup_next_hop=route.backup_next_hop,
                primary_quality=route.primary_quality,
                backup_quality=route.backup_quality,
            )
            for destination, route in network.routing_table.routes.items()
        }

        return network

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

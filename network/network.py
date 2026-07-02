from core.link import Link
from core.node import Node
from core.packet import Packet, PacketOutcome
from core.routing_table import RoutingTable
from algorithms.lq_lrr import LQLocalRouteRepair
from algorithms.routing_strategy import RoutingStrategy
from metrics.metrics import Metrics


class Network:
    """Represent a mesh network with nodes, links, routing, and metrics.

    The class remains backward compatible with the original simulator entry
    points while now using the current topology state and a pluggable routing
    strategy for packet forwarding.
    """

    def __init__(self):
        """Initialize an empty network with routing and metrics support."""
        self.nodes = {}
        self.links = []

        self.routing_table = RoutingTable()

        self.repair = LQLocalRouteRepair(self.routing_table)

        self.metrics = Metrics()

    def add_node(self, node: Node):
        """Register a node in the network."""
        self.nodes[node.node_id] = node

    def connect(self, node1: str, node2: str, quality: float):
        """Create or update a bidirectional link between two nodes."""
        self.nodes[node1].add_neighbour(node2, quality)
        self.nodes[node2].add_neighbour(node1, quality)

        link = self._get_link(node1, node2)
        if link is None:
            self.links.append(Link(node1, node2, quality, True, 0))
        else:
            link.link_quality = quality
            link.recover()

    def disconnect(self, node1: str, node2: str):
        """Remove adjacency and mark the corresponding link inactive."""
        if node2 in self.nodes[node1].neighbours:
            del self.nodes[node1].neighbours[node2]

        if node1 in self.nodes[node2].neighbours:
            del self.nodes[node2].neighbours[node1]

        link = self._get_link(node1, node2)
        if link is not None:
            link.fail()

    def _get_link(self, node1: str, node2: str):
        """Return an existing link between two nodes, if present."""
        for link in self.links:
            if {link.source_node, link.destination_node} == {node1, node2}:
                return link
        return None

    def _is_link_active(self, node1: str, node2: str) -> bool:
        """Return whether a link between two nodes is currently active."""
        link = self._get_link(node1, node2)
        return link is not None and link.is_active()

    def send_packet(self, packet: Packet, destination: str):
        """Send a packet through the network and update metrics."""
        packet.reset()
        self.metrics.packet_sent()

        route = self.routing_table.get_route(destination)
        if route is None:
            print("No Route Found")
            packet.set_outcome(PacketOutcome.UNREACHABLE)
            self.metrics.record_outcome(packet.outcome, packet.hop_count)
            return

        print("\nSending Packet...")
        print(f"Destination : {destination}")
        print(f"Primary Route : {route.primary_next_hop}")

        success = False
        previous_primary_hop = getattr(route, "primary_next_hop", None)
        if self.repair is not None:
            success = self.repair.route_packet(self, packet, destination)
            updated_route = self.routing_table.get_route(destination)
            updated_primary_hop = getattr(updated_route, "primary_next_hop", None)
            if success and updated_primary_hop != previous_primary_hop:
                self.metrics.repair_success()

        if not success:
            if packet.outcome is None:
                packet.set_outcome(PacketOutcome.FAILED)
            self.metrics.record_outcome(packet.outcome, packet.hop_count)
            return

        if packet.outcome is None:
            packet.set_outcome(PacketOutcome.DELIVERED)
        self.metrics.record_outcome(packet.outcome, packet.hop_count)

        print("\nPacket Delivered Successfully")
        print(packet)
        print("Path :", " -> ".join(packet.path))
        print("Hop Count :", packet.hop_count)

    def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """Set the routing strategy used by the network."""
        self.repair = strategy
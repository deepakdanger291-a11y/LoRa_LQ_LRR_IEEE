from core.packet import Packet, PacketOutcome
from algorithms.routing_strategy import RoutingStrategy
from core.routing_table import RoutingTable


class LQLocalRouteRepair(RoutingStrategy):
    """LQ-LRR routing strategy that preserves the original repair behavior.

    The implementation remains compatible with the existing route table format,
    but it now consults the current network state before forwarding so it can
    repair a route when the selected next hop is no longer usable.
    """

    def __init__(self, routing_table):
        self.routing_table = routing_table

    def route_packet(self, network, packet: Packet, destination: str) -> bool:
        """Route a packet using the LQ-LRR strategy."""
        if self.routing_table is None:
            self.routing_table = network.routing_table if network is not None else RoutingTable()

        route = self.routing_table.get_route(destination)

        if route is None:
            print("No Route Available")
            packet.set_outcome(PacketOutcome.UNREACHABLE)
            return False

        if route.primary_next_hop is None:
            print("No Route Available")
            packet.set_outcome(PacketOutcome.UNREACHABLE)
            return False

        repaired = False
        if network is not None:
            next_hop = route.primary_next_hop
            if next_hop != destination and not network._is_link_active(next_hop, destination):
                repaired_route = self.repair(destination)
                route = self.routing_table.get_route(destination)
                if repaired_route is None or route is None or route.primary_next_hop is None:
                    print("Repair Failed")
                    packet.set_outcome(PacketOutcome.FAILED)
                    return False
                repaired = True

        packet.visit(packet.source)
        packet.visit(route.primary_next_hop)
        packet.visit(destination)
        if repaired:
            packet.set_outcome(PacketOutcome.RECOVERED)
        else:
            packet.mark_delivered()
        return True

    def repair(self, destination):
        """Repair a route by switching the backup next hop into the primary slot."""
        route = self.routing_table.get_route(destination)

        if route is None:
            print("No Route Available")
            return None

        if route.backup_next_hop is None:
            print("No Backup Route")
            return None

        print("\nLOCAL ROUTE REPAIR")

        print("--------------------------------")

        print("Destination :", destination)

        print("Primary :", route.primary_next_hop)

        print("Backup  :", route.backup_next_hop)

        print("\nSwitching to Backup Route...")

        route.primary_next_hop = route.backup_next_hop
        route.primary_quality = route.backup_quality

        route.backup_next_hop = None
        route.backup_quality = 0.0

        print("Repair Successful")

        return route
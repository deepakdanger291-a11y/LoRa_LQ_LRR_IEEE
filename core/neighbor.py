from core.node import Node
from core.packet import Packet
from algorithms.lq_lrr import LQLocalRouteRepair
from core.routing_table import RoutingTable


class Network:

    def __init__(self):

        self.nodes = {}
        self.routing_table = RoutingTable()
        self.repair = LQLocalRouteRepair(self.routing_table)

    def add_node(self, node: Node):

        self.nodes[node.node_id] = node

    def connect(self, node1, node2, quality):

        self.nodes[node1].add_neighbour(node2, quality)
        self.nodes[node2].add_neighbour(node1, quality)

    def disconnect(self, node1, node2):

        if node2 in self.nodes[node1].neighbours:
            del self.nodes[node1].neighbours[node2]

        if node1 in self.nodes[node2].neighbours:
            del self.nodes[node2].neighbours[node1]

    def send_packet(self, packet: Packet, destination: str):

        route = self.routing_table.get_route(destination)

        if route is None:

            print("No Route")
            return

        current = route.primary_next_hop

        print(f"\nSending packet towards {destination}")
        print(f"Using Primary Route : {current}")

        if not self.nodes["B"].has_neighbour("C"):

            print("\nLINK FAILURE DETECTED")
            print("B -> C is DOWN")

            self.repair.repair(destination)

            route = self.routing_table.get_route(destination)

            current = route.primary_next_hop

            print(f"\nNew Route Selected : {current}")

        print("\nPacket Delivered Successfully")
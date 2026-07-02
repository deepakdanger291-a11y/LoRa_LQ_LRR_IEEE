from core.node import Node
from core.packet import Packet
from network.network import Network


network = Network()

network.add_node(Node("A"))
network.add_node(Node("B"))
network.add_node(Node("C"))
network.add_node(Node("D"))

network.connect("A", "B", 0.95)
network.connect("B", "C", 0.92)
network.connect("B", "D", 0.85)
network.connect("D", "C", 0.82)

network.routing_table.add_route(
    destination="C",
    primary="B",
    backup="D",
    primary_quality=0.92,
    backup_quality=0.82
)

packet = Packet(
    packet_id=1,
    source="A",
    destination="C",
    payload="IEEE Test"
)

print("\n===== NORMAL TRANSMISSION =====")
network.send_packet(packet, "C")

print("\n\n===== SIMULATING LINK FAILURE =====")

network.disconnect("B", "C")

network.send_packet(packet, "C")

print("\n")
network.metrics.print_report()
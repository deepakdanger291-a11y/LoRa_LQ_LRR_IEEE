import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.packet import Packet
from algorithms.baseline import BaselineRouting
from network.network import Network
from core.node import Node


print("=" * 60)
print("LQ-LRR vs BASELINE")
print("=" * 60)

packet = Packet(
    packet_id=1,
    source="A",
    destination="C",
    payload="IEEE"
)

baseline = BaselineRouting()

baseline.send_packet(packet)

print("\n" + "=" * 60)

network = Network()

network.add_node(Node("A"))
network.add_node(Node("B"))
network.add_node(Node("C"))
network.add_node(Node("D"))

network.connect("A", "B", 0.95)
network.connect("B", "D", 0.85)
network.connect("D", "C", 0.82)

network.routing_table.add_route(
    destination="C",
    primary="B",
    backup="D",
    primary_quality=0.95,
    backup_quality=0.82
)

network.disconnect("B", "C")

packet2 = Packet(
    packet_id=2,
    source="A",
    destination="C",
    payload="IEEE"
)

network.send_packet(packet2, "C")
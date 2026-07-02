from core.packet import PacketOutcome


class Metrics:

    def __init__(self):
        self.total_packets = 0
        self.delivered_packets = 0
        self.failed_packets = 0
        self.total_hops = 0
        self.route_repairs = 0
        self.dropped_packets = 0
        self.recovered_packets = 0
        self.unreachable_packets = 0

    def packet_sent(self):
        self.total_packets += 1

    def packet_delivered(self, hops):
        self.record_outcome(PacketOutcome.DELIVERED, hops)

    def packet_failed(self):
        self.record_outcome(PacketOutcome.FAILED)

    def record_outcome(self, outcome, hops=0):
        if isinstance(outcome, str):
            outcome = PacketOutcome(outcome)

        if outcome == PacketOutcome.DELIVERED:
            self.delivered_packets += 1
            self.total_hops += hops
        elif outcome == PacketOutcome.RECOVERED:
            self.recovered_packets += 1
            self.delivered_packets += 1
            self.total_hops += hops
        elif outcome == PacketOutcome.DROPPED:
            self.dropped_packets += 1
            self.failed_packets += 1
        elif outcome == PacketOutcome.FAILED:
            self.failed_packets += 1
        elif outcome == PacketOutcome.UNREACHABLE:
            self.unreachable_packets += 1
            self.failed_packets += 1

    def repair_success(self):
        self.route_repairs += 1

    def print_report(self):

        print("\n" + "=" * 60)
        print("SIMULATION REPORT")
        print("=" * 60)

        print(f"Packets Sent        : {self.total_packets}")
        print(f"Packets Delivered   : {self.delivered_packets}")
        print(f"Packets Failed      : {self.failed_packets}")
        print(f"Packets Dropped     : {self.dropped_packets}")
        print(f"Packets Recovered   : {self.recovered_packets}")
        print(f"Packets Unreachable : {self.unreachable_packets}")

        if self.delivered_packets > 0:
            print(
                f"Average Hop Count   : "
                f"{self.total_hops/self.delivered_packets:.2f}"
            )

        print(f"Route Repairs       : {self.route_repairs}")

        pdr = (
            self.delivered_packets /
            self.total_packets * 100
            if self.total_packets else 0
        )

        print(f"Packet Delivery (%) : {pdr:.2f}")
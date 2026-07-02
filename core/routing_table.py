from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RouteEntry:
    destination: str
    primary_next_hop: str
    backup_next_hop: Optional[str]
    primary_quality: float
    backup_quality: float = 0.0


class RoutingTable:

    def __init__(self):
        self.routes: Dict[str, RouteEntry] = {}

    def add_route(
        self,
        destination: str,
        primary: str,
        backup: Optional[str],
        primary_quality: float,
        backup_quality: float = 0.0,
    ):

        self.routes[destination] = RouteEntry(
            destination=destination,
            primary_next_hop=primary,
            backup_next_hop=backup,
            primary_quality=primary_quality,
            backup_quality=backup_quality,
        )

    def get_route(self, destination: str):

        return self.routes.get(destination)

    def remove_route(self, destination: str):

        if destination in self.routes:
            del self.routes[destination]

    def has_route(self, destination: str):

        return destination in self.routes

    def print_table(self):

        print("\nRouting Table")
        print("-" * 80)

        print(
            f"{'Dest':8}"
            f"{'Primary':12}"
            f"{'Backup':12}"
            f"{'P_Quality':12}"
            f"{'B_Quality'}"
        )

        print("-" * 80)

        for route in self.routes.values():

            print(
                f"{route.destination:8}"
                f"{route.primary_next_hop:12}"
                f"{str(route.backup_next_hop):12}"
                f"{route.primary_quality:<12.2f}"
                f"{route.backup_quality:.2f}"
            )
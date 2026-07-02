"""Link model for the LoRa mesh network simulator."""

from dataclasses import dataclass


@dataclass
class Link:
    """Represent a bidirectional network link between two nodes.

    The link stores its endpoints, link quality, current activity state,
    and how many times it has failed. It is intentionally lightweight so it
    can be used by topology generation, failure simulation, and routing logic.
    """

    source_node: str
    destination_node: str
    link_quality: float
    active: bool = True
    failure_count: int = 0

    def fail(self) -> None:
        """Mark the link as inactive and record a failure event."""
        self.active = False
        self.failure_count += 1

    def recover(self) -> None:
        """Mark the link as active again."""
        self.active = True

    def is_active(self) -> bool:
        """Return whether the link is currently available."""
        return self.active

    def __str__(self) -> str:
        """Return a readable summary of the link state."""
        status = "active" if self.active else "inactive"
        return (
            f"Link({self.source_node} -> {self.destination_node}, "
            f"quality={self.link_quality:.2f}, status={status}, "
            f"failures={self.failure_count})"
        )

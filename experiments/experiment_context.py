"""Immutable experiment context and supporting specification classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class NodeSpec:
    """Describe a single node in a topology specification."""

    node_id: str


@dataclass(frozen=True)
class LinkSpec:
    """Describe a single link in a topology specification."""

    source: str
    destination: str
    quality: float
    initial_active: bool = True


@dataclass(frozen=True)
class TopologySpec:
    """Describe a topology used by an experiment."""

    topology_id: str
    nodes: Tuple[NodeSpec, ...]
    links: Tuple[LinkSpec, ...]


@dataclass(frozen=True)
class RouteSpec:
    """Describe a single route entry in the routing state."""

    destination: str
    primary_next_hop: str
    backup_next_hop: Optional[str] = None
    primary_quality: float = 0.0
    backup_quality: float = 0.0


@dataclass(frozen=True)
class RoutingStateSpec:
    """Describe the initial routing state for an experiment."""

    routes: Tuple[RouteSpec, ...]


@dataclass(frozen=True)
class FailureEvent:
    """Describe a single failure event for an experiment step."""

    step: int
    kind: str
    target: str
    probability: Optional[float] = None


@dataclass(frozen=True)
class FailureSchedule:
    """Describe the ordered failure events for an experiment."""

    events: Tuple[FailureEvent, ...]


@dataclass(frozen=True)
class PacketSpec:
    """Describe a single packet in an experiment packet schedule."""

    packet_id: int
    source: str
    destination: str
    payload: str
    generation_step: int


@dataclass(frozen=True)
class PacketSchedule:
    """Describe the ordered packet schedule for an experiment."""

    packets: Tuple[PacketSpec, ...]


@dataclass(frozen=True)
class SourcePolicy:
    """Describe how the experiment selects sources."""

    mode: str = "fixed"
    candidates: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DestinationPolicy:
    """Describe how the experiment selects destinations."""

    mode: str = "fixed"
    candidates: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExperimentContext:
    """Immutable experiment definition used to build deterministic runtime state."""

    trial_id: int
    node_count: int
    packet_count: int
    failure_probability: float
    random_seed: int
    topology: TopologySpec
    routing_state: RoutingStateSpec
    failure_schedule: FailureSchedule
    packet_schedule: PacketSchedule
    source_policy: SourcePolicy
    destination_policy: DestinationPolicy
    experiment_duration: int

    def validate(self) -> None:
        """Validate the experiment context before simulation execution."""
        errors: List[str] = []

        if self.node_count <= 0:
            errors.append("node_count must be greater than zero")
        if self.packet_count <= 0:
            errors.append("packet_count must be greater than zero")
        if not 0.0 <= self.failure_probability <= 1.0:
            errors.append("failure_probability must be between 0 and 1")
        if self.experiment_duration <= 0:
            errors.append("experiment_duration must be greater than zero")

        node_ids = [node.node_id for node in self.topology.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("topology contains duplicate node identifiers")

        if len(node_ids) != self.node_count:
            errors.append("topology node count does not match node_count")

        node_set = set(node_ids)
        for link in self.topology.links:
            if link.source == link.destination:
                errors.append(f"self-loop link detected: {link.source}")
            if link.source not in node_set or link.destination not in node_set:
                errors.append(f"invalid link target: {link.source} -> {link.destination}")

        if len(self.topology.links) != len({(link.source, link.destination) for link in self.topology.links}):
            errors.append("topology contains duplicate links")

        if not self._is_connected(node_ids, self.topology.links):
            errors.append("topology is disconnected")

        route_destinations = [route.destination for route in self.routing_state.routes]
        if len(route_destinations) != len(set(route_destinations)):
            errors.append("routing_state contains duplicate destinations")

        for route in self.routing_state.routes:
            if route.destination not in node_set:
                errors.append(f"route destination does not exist: {route.destination}")
            if route.primary_next_hop not in node_set:
                errors.append(f"primary hop does not exist: {route.primary_next_hop}")
            if route.backup_next_hop is not None and route.backup_next_hop not in node_set:
                errors.append(f"backup hop does not exist: {route.backup_next_hop}")

        for event in self.failure_schedule.events:
            if event.step < 0 or event.step >= self.experiment_duration:
                errors.append(f"failure event step out of range: {event.step}")
            if event.kind not in {"link", "node"}:
                errors.append(f"unsupported failure event kind: {event.kind}")
            if event.kind == "link" and event.target not in node_set:
                errors.append(f"failure event target is not a known node: {event.target}")

        for packet in self.packet_schedule.packets:
            if packet.source not in node_set:
                errors.append(f"packet source does not exist: {packet.source}")
            if packet.destination not in node_set:
                errors.append(f"packet destination does not exist: {packet.destination}")
            if packet.generation_step < 0 or packet.generation_step >= self.experiment_duration:
                errors.append(f"packet generation_step out of range: {packet.generation_step}")

        if errors:
            raise ValueError("ExperimentContext validation failed:\n- " + "\n- ".join(errors))

    def _is_connected(self, node_ids: List[str], links: Tuple[LinkSpec, ...]) -> bool:
        """Return whether the topology is connected."""
        if len(node_ids) <= 1:
            return True

        adjacency = {node_id: set() for node_id in node_ids}
        for link in links:
            adjacency[link.source].add(link.destination)
            adjacency[link.destination].add(link.source)

        visited = set()
        stack = [node_ids[0]]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for neighbour in adjacency[current]:
                if neighbour not in visited:
                    stack.append(neighbour)

        return len(visited) == len(node_ids)

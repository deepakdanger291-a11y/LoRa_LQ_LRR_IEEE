"""Reusable experiment configuration for the IEEE-style evaluation suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Sequence, Type, Union

from algorithms.baseline import BaselineRouting
from algorithms.lq_lrr import LQLocalRouteRepair
from algorithms.routing_strategy import RoutingStrategy


@dataclass
class ExperimentConfig:
    """Configuration for one experiment sweep over multiple settings."""

    node_counts: Sequence[int]
    failure_probabilities: Sequence[float]
    packet_count: int = 100
    trials: int = 30
    routing_strategy: Union[Type[RoutingStrategy], RoutingStrategy] = BaselineRouting
    random_seed: Optional[int] = None
    output_dir: str = "experiment_outputs"

    def __post_init__(self) -> None:
        if not self.node_counts:
            raise ValueError("node_counts must not be empty")
        if not self.failure_probabilities:
            raise ValueError("failure_probabilities must not be empty")
        if self.packet_count <= 0:
            raise ValueError("packet_count must be greater than zero")
        if self.trials <= 0:
            raise ValueError("trials must be greater than zero")
        if not all(count > 0 for count in self.node_counts):
            raise ValueError("all node counts must be greater than zero")
        if not all(0.0 <= probability <= 1.0 for probability in self.failure_probabilities):
            raise ValueError("failure probabilities must be between 0 and 1")

    def iter_configurations(self) -> Iterator[dict]:
        """Yield one configuration per node/failure-probability pair."""
        for node_count in self.node_counts:
            for failure_probability in self.failure_probabilities:
                yield {
                    "node_count": node_count,
                    "packet_count": self.packet_count,
                    "failure_probability": failure_probability,
                    "trials": self.trials,
                    "routing_strategy": self.routing_strategy,
                    "random_seed": self.random_seed,
                }

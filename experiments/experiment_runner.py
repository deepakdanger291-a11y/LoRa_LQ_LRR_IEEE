"""Experiment runner for repeated simulator trials."""

from typing import List, Optional, Sequence, Type, Union

from algorithms.baseline import BaselineRouting
from algorithms.lq_lrr import LQLocalRouteRepair
from algorithms.routing_strategy import RoutingStrategy
from simulation.simulation_engine import ExperimentResult, SimulationEngine
from simulation.topology_generator import TopologyGenerator


class ExperimentRunner:
    """Run repeated experiments with configurable simulation parameters.

    The runner does not change the simulator architecture. It simply composes
    the existing topology generator, failure engine, simulation engine, and
    routing strategies into a reusable experiment workflow.
    """

    def __init__(self, trials: int = 1):
        """Initialize the runner with the number of trials to execute."""
        if trials <= 0:
            raise ValueError("trials must be greater than zero")
        self.trials = trials

    def run_experiments(
        self,
        node_count: int,
        packet_count: int,
        failure_probability: float,
        random_seed: Optional[int],
        routing_strategy: Union[Type[RoutingStrategy], RoutingStrategy],
    ) -> List[ExperimentResult]:
        """Run repeated trials and collect the aggregated per-trial results.

        Args:
            node_count: Number of nodes in each generated topology.
            packet_count: Packets to simulate per trial.
            failure_probability: Probability of link failure per transmission.
            random_seed: Optional seed used to reproduce the run.
            routing_strategy: A routing strategy class or instance.

        Returns:
            A list of ExperimentResult objects, one per trial.
        """
        if node_count <= 0:
            raise ValueError("node_count must be greater than zero")
        if packet_count <= 0:
            raise ValueError("packet_count must be greater than zero")
        if not 0.0 <= failure_probability <= 1.0:
            raise ValueError("failure_probability must be between 0 and 1")

        strategy_instance = self._resolve_strategy(routing_strategy)
        results: List[ExperimentResult] = []

        for trial_index in range(self.trials):
            trial_seed = None if random_seed is None else random_seed + trial_index
            topology_generator = TopologyGenerator(seed=trial_seed)
            network = topology_generator.generate_topology(
                num_nodes=node_count,
                connection_probability=0.5,
                min_link_quality=0.6,
                max_link_quality=0.95,
                seed=trial_seed,
            )

            simulation_engine = SimulationEngine(network, strategy_instance)
            result = simulation_engine.run(
                packet_count=packet_count,
                failure_probability=failure_probability,
                source_node=None,
                destination_nodes=None,
                seed=trial_seed,
            )
            results.append(result)

        return results

    def summarize_results(self, results: Sequence[ExperimentResult]) -> dict:
        """Aggregate a sequence of trial results into summary statistics."""
        if not results:
            raise ValueError("results must not be empty")

        delivery_ratio = sum(result.packet_delivery_ratio for result in results) / len(results)
        average_hop_count = sum(result.average_hop_count for result in results) / len(results)
        repairs = sum(result.repairs for result in results)
        failed_links = sum(result.failed_links for result in results)

        return {
            "trials": len(results),
            "packet_delivery_ratio": delivery_ratio,
            "average_hop_count": average_hop_count,
            "repairs": repairs,
            "failed_links": failed_links,
        }

    def _resolve_strategy(self, routing_strategy: Union[Type[RoutingStrategy], RoutingStrategy]) -> RoutingStrategy:
        """Return a strategy instance from either a class or an instance."""
        if isinstance(routing_strategy, RoutingStrategy):
            return routing_strategy

        if issubclass(routing_strategy, RoutingStrategy):
            if routing_strategy is BaselineRouting:
                return BaselineRouting()
            if routing_strategy is LQLocalRouteRepair:
                return LQLocalRouteRepair(None)
            return routing_strategy()

        raise TypeError("routing_strategy must be a RoutingStrategy instance or class")

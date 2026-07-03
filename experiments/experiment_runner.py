"""Experiment runner for repeated simulator trials."""

import copy
from typing import List, Optional, Sequence, Type, Union

from algorithms.baseline import BaselineRouting
from algorithms.lq_lrr import LQLocalRouteRepair
from algorithms.routing_strategy import RoutingStrategy
from core.routing_table import RoutingTable
from experiments.experiment_context import (
    DestinationPolicy,
    ExperimentContext,
    FailureSchedule,
    LinkSpec,
    NodeSpec,
    PacketSchedule,
    PacketSpec,
    RoutingStateSpec,
    RouteSpec,
    SourcePolicy,
    TopologySpec,
)
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
            self._initialize_routing_state(network)

            strategy_instance = self._resolve_strategy(routing_strategy)
            self._seed_strategy_with_network(strategy_instance, network)
            context = self._build_context(trial_index, node_count, packet_count, failure_probability, trial_seed, network)
            simulation_engine = SimulationEngine(None, strategy_instance, context=context)
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

    def _build_context(
        self,
        trial_index: int,
        node_count: int,
        packet_count: int,
        failure_probability: float,
        random_seed: Optional[int],
        network,
    ) -> ExperimentContext:
        """Build an immutable experiment context from the current network state."""
        node_specs = tuple(NodeSpec(node_id) for node_id in sorted(network.nodes))
        link_specs = tuple(
            LinkSpec(link.source_node, link.destination_node, link.link_quality, link.is_active())
            for link in network.links
        )
        route_specs = []
        for destination in sorted(network.nodes):
            route = network.routing_table.get_route(destination)
            if route is None:
                continue

            route_specs.append(
                RouteSpec(
                    destination=destination,
                    primary_next_hop=route.primary_next_hop,
                    backup_next_hop=route.backup_next_hop,
                    primary_quality=route.primary_quality,
                    backup_quality=route.backup_quality,
                )
            )

        packet_specs = tuple(
            PacketSpec(
                packet_id=index,
                source=node_specs[0].node_id,
                destination=node_specs[-1].node_id if len(node_specs) > 1 else node_specs[0].node_id,
                payload="sim",
                generation_step=index - 1,
            )
            for index in range(1, packet_count + 1)
        )

        return ExperimentContext(
            trial_id=trial_index,
            node_count=node_count,
            packet_count=packet_count,
            failure_probability=failure_probability,
            random_seed=random_seed if random_seed is not None else 0,
            topology=TopologySpec(
                topology_id=f"trial-{trial_index}",
                nodes=node_specs,
                links=link_specs,
            ),
            routing_state=RoutingStateSpec(routes=tuple(route_specs)),
            failure_schedule=FailureSchedule(events=()),
            packet_schedule=PacketSchedule(packets=packet_specs),
            source_policy=SourcePolicy(mode="fixed", candidates=(node_specs[0].node_id,)),
            destination_policy=DestinationPolicy(mode="fixed", candidates=(node_specs[-1].node_id if len(node_specs) > 1 else node_specs[0].node_id,)),
            experiment_duration=max(1, packet_count),
        )

    def _initialize_routing_state(self, network) -> None:
        """Populate the network's routing table from the generated topology."""
        node_ids = sorted(network.nodes)
        for destination in node_ids:
            if network.routing_table.get_route(destination) is not None:
                continue

            candidate_hops = [
                neighbour
                for neighbour in sorted(network.nodes[destination].neighbours)
                if neighbour != destination
            ]
            if candidate_hops:
                primary_next_hop = candidate_hops[0]
                primary_quality = network.nodes[destination].get_link_quality(primary_next_hop)
            else:
                primary_next_hop = next((node_id for node_id in node_ids if node_id != destination), destination)
                primary_quality = 0.0

            network.routing_table.add_route(
                destination=destination,
                primary=primary_next_hop,
                backup=None,
                primary_quality=primary_quality,
                backup_quality=0.0,
            )

    def _seed_strategy_with_network(self, strategy: RoutingStrategy, network) -> None:
        """Initialize a strategy's routing table from the network state when available."""
        if isinstance(strategy, LQLocalRouteRepair):
            strategy.routing_table = RoutingTable()
            for destination, route in network.routing_table.routes.items():
                strategy.routing_table.add_route(
                    destination=destination,
                    primary=route.primary_next_hop,
                    backup=route.backup_next_hop,
                    primary_quality=route.primary_quality,
                    backup_quality=route.backup_quality,
                )

    def _resolve_strategy(self, routing_strategy: Union[Type[RoutingStrategy], RoutingStrategy]) -> RoutingStrategy:
        """Return a fresh strategy instance from either a class or an instance."""
        if isinstance(routing_strategy, RoutingStrategy):
            return copy.deepcopy(routing_strategy)

        if isinstance(routing_strategy, type) and issubclass(routing_strategy, RoutingStrategy):
            if routing_strategy is BaselineRouting:
                return BaselineRouting()
            if routing_strategy is LQLocalRouteRepair:
                return LQLocalRouteRepair(RoutingTable())
            return routing_strategy()

        raise TypeError("routing_strategy must be a RoutingStrategy instance or class")

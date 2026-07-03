"""Reusable experiment suite for running and exporting simulator trials."""

from __future__ import annotations

import csv
import os
from typing import Any, Dict, List, Optional, Sequence, Union

from algorithms.baseline import BaselineRouting
from algorithms.lq_lrr import LQLocalRouteRepair
from algorithms.routing_strategy import RoutingStrategy
from experiments.experiment_config import ExperimentConfig
from experiments.experiment_runner import ExperimentRunner
from simulation.simulation_engine import ExperimentResult


class ExperimentSuite:
    """Run an experiment sweep and export CSV results for each configuration."""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.runner = ExperimentRunner(trials=config.trials)
        os.makedirs(self.config.output_dir, exist_ok=True)

    def run(self) -> List[Dict[str, Any]]:
        """Execute all configurations and write CSV outputs."""
        summaries: List[Dict[str, Any]] = []

        for settings in self.config.iter_configurations():
            trial_results = self.runner.run_experiments(
                node_count=settings["node_count"],
                packet_count=settings["packet_count"],
                failure_probability=settings["failure_probability"],
                random_seed=settings["random_seed"],
                routing_strategy=settings["routing_strategy"],
            )
            summary = self._summarize_trial_results(settings, trial_results)
            summaries.append(summary)
            self._write_trial_csv(settings, trial_results)
            self._write_summary_csv(settings, summary)

        return summaries

    def _summarize_trial_results(self, settings: Dict[str, Any], results: Sequence[ExperimentResult]) -> Dict[str, Any]:
        values = [result.packet_delivery_ratio for result in results]
        hops = [result.average_hop_count for result in results]
        repairs = [result.repairs for result in results]

        strategy_name = self._strategy_name(settings["routing_strategy"])
        summary = {
            "strategy": strategy_name,
            "nodes": settings["node_count"],
            "packets": settings["packet_count"],
            "failure_probability": settings["failure_probability"],
            "trials": len(results),
            "packet_delivery_ratio": {
                "mean": self._mean(values),
                "median": self._median(values),
                "variance": self._variance(values),
                "stddev": self._stddev(values),
                "min": min(values),
                "max": max(values),
                "ci95": self._confidence_interval(values),
            },
            "average_hop_count": {
                "mean": self._mean(hops),
                "median": self._median(hops),
                "variance": self._variance(hops),
                "stddev": self._stddev(hops),
                "min": min(hops),
                "max": max(hops),
                "ci95": self._confidence_interval(hops),
            },
            "repairs": {
                "mean": self._mean(repairs),
                "median": self._median(repairs),
                "variance": self._variance(repairs),
                "stddev": self._stddev(repairs),
                "min": min(repairs),
                "max": max(repairs),
                "ci95": self._confidence_interval(repairs),
            },
        }
        return summary

    def _write_trial_csv(self, settings: Dict[str, Any], results: Sequence[ExperimentResult]) -> None:
        strategy_name = self._strategy_name(settings["routing_strategy"])
        filename = os.path.join(
            self.config.output_dir,
            f"{strategy_name.lower()}_n{settings['node_count']}_p{settings['failure_probability']}.csv",
        )
        with open(filename, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "Trial",
                    "Nodes",
                    "Packets",
                    "FailureProbability",
                    "RoutingStrategy",
                    "PacketsSent",
                    "PacketsDelivered",
                    "PacketsDropped",
                    "PacketsRecovered",
                    "PacketsFailed",
                    "PacketsUnreachable",
                    "AverageHopCount",
                    "Variance",
                    "StandardDeviation",
                    "PacketDeliveryRatio",
                    "Repairs",
                ],
            )
            writer.writeheader()
            for index, result in enumerate(results, start=1):
                writer.writerow(
                    {
                        "Trial": index,
                        "Nodes": settings["node_count"],
                        "Packets": settings["packet_count"],
                        "FailureProbability": settings["failure_probability"],
                        "RoutingStrategy": strategy_name,
                        "PacketsSent": result.packets_sent,
                        "PacketsDelivered": result.packets_delivered,
                        "PacketsDropped": result.packets_dropped,
                        "PacketsRecovered": result.packets_recovered,
                        "PacketsFailed": result.packets_failed,
                        "PacketsUnreachable": result.packets_unreachable,
                        "AverageHopCount": result.average_hop_count,
                        "Variance": result.variance,
                        "StandardDeviation": result.standard_deviation,
                        "PacketDeliveryRatio": result.packet_delivery_ratio,
                        "Repairs": result.repairs,
                    }
                )

    def _write_summary_csv(self, settings: Dict[str, Any], summary: Dict[str, Any]) -> None:
        strategy_name = self._strategy_name(settings["routing_strategy"])
        filename = os.path.join(
            self.config.output_dir,
            f"summary_{strategy_name.lower()}_n{settings['node_count']}_p{settings['failure_probability']}.csv",
        )
        with open(filename, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["Metric", "Mean", "Median", "Variance", "StandardDeviation", "Minimum", "Maximum", "CI95"])
            writer.writeheader()
            for metric_name, values in (
                ("PacketDeliveryRatio", summary["packet_delivery_ratio"]),
                ("AverageHopCount", summary["average_hop_count"]),
                ("Repairs", summary["repairs"]),
            ):
                writer.writerow(
                    {
                        "Metric": metric_name,
                        "Mean": values["mean"],
                        "Median": values["median"],
                        "Variance": values["variance"],
                        "StandardDeviation": values["stddev"],
                        "Minimum": values["min"],
                        "Maximum": values["max"],
                        "CI95": values["ci95"],
                    }
                )

    def _strategy_name(self, strategy: Union[Type[RoutingStrategy], RoutingStrategy]) -> str:
        if isinstance(strategy, type):
            return strategy.__name__
        return strategy.__class__.__name__

    def _mean(self, values: Sequence[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def _median(self, values: Sequence[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        middle = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return ordered[middle]
        return (ordered[middle - 1] + ordered[middle]) / 2.0

    def _variance(self, values: Sequence[float]) -> float:
        if len(values) <= 1:
            return 0.0
        mean_value = self._mean(values)
        return sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)

    def _stddev(self, values: Sequence[float]) -> float:
        if len(values) <= 1:
            return 0.0
        return self._variance(values) ** 0.5

    def _confidence_interval(self, values: Sequence[float]) -> float:
        if len(values) <= 1:
            return 0.0
        stddev = self._stddev(values)
        return 1.96 * stddev / (len(values) ** 0.5)

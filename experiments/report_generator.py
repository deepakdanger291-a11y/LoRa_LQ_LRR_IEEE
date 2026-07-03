"""Simple IEEE-style report generator for experiment summaries."""

from __future__ import annotations

from typing import Dict, Any


class ExperimentReportGenerator:
    """Render compact experiment summaries suitable for console reporting."""

    def render_summary(self, summary: Dict[str, Any]) -> str:
        lines = [
            "====================================================",
            "EXPERIMENT SUMMARY",
            "====================================================",
            "",
            f"Strategy : {summary['strategy']}",
            "",
            f"Trials : {summary.get('trials', 1)}",
            "",
            f"Nodes : {summary['nodes']}",
            "",
            f"Failure Probability : {summary['failure_probability']}",
            "",
            "Packet Delivery Ratio :",
            f"Mean : {summary['packet_delivery_ratio']['mean']:.2f} %",
            "",
            f"95% CI : {summary['packet_delivery_ratio']['ci95']:.2f}",
            "",
            "Average Hop Count :",
            f"Mean : {summary['average_hop_count']['mean']:.2f}",
            "",
            "Repairs :",
            f"Mean : {summary['repairs']['mean']:.2f}",
            "",
            "====================================================",
        ]
        return "\n".join(lines)

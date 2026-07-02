# LoRa LQ-LRR IEEE Simulator

Current Version: v0.5

## Completed

- Packet Model
- Node Model
- Routing Table
- Baseline Routing
- LQ-LRR Algorithm
- Metrics
- Link Abstraction
- Topology Generator
- Failure Engine
- Simulation Engine
- Experiment Runner
- Routing Strategy Interface

## Phase 1 Architecture Notes

- core/packet.py: Represents packets moving through the network and records traversal state.
- core/node.py: Represents mesh nodes and their local neighbour relationships.
- core/routing_table.py: Stores primary and backup routing choices for destinations.
- algorithms/baseline.py: Preserves the original baseline routing behavior while using the current network context when available.
- algorithms/lq_lrr.py: Preserves the original LQ-LRR route repair behavior while consulting the current topology during forwarding.
- algorithms/routing_strategy.py: Defines the shared interface used by routing strategies.
- network/network.py: Coordinates nodes, links, routing state, and packet delivery while preserving compatibility with the original entry points.
- simulation/simulation_engine.py: Executes packet transmissions and collects experiment metrics using the selected routing strategy.
- simulation/topology_generator.py: Builds connected random topologies for simulation experiments.
- simulation/failure_engine.py: Applies probabilistic link failures in a reusable way.
- experiments/experiment_runner.py: Runs repeated experiments and aggregates per-trial outcomes.

Status:
Architecture Complete
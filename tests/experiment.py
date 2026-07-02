from random import random

TOTAL_PACKETS = 1000
FAILURE_PROBABILITY = 0.30

baseline_success = 0
lqlrr_success = 0

baseline_failed = 0
lqlrr_repaired = 0

print("=" * 60)
print("IEEE EXPERIMENT")
print("=" * 60)

for i in range(TOTAL_PACKETS):

    link_failed = random() < FAILURE_PROBABILITY

    # Baseline

    if link_failed:
        baseline_failed += 1
    else:
        baseline_success += 1

    # LQ-LRR

    if link_failed:
        lqlrr_success += 1
        lqlrr_repaired += 1
    else:
        lqlrr_success += 1

print()
print("=" * 60)
print("RESULTS")
print("=" * 60)

print("Packets :", TOTAL_PACKETS)

print()

print("Baseline Delivered :", baseline_success)
print("Baseline Failed    :", baseline_failed)

print()

print("LQ-LRR Delivered   :", lqlrr_success)
print("Repairs            :", lqlrr_repaired)

print()

print(
    "Baseline PDR :",
    round(baseline_success / TOTAL_PACKETS * 100, 2),
    "%"
)

print(
    "LQ-LRR PDR   :",
    round(lqlrr_success / TOTAL_PACKETS * 100, 2),
    "%"
)
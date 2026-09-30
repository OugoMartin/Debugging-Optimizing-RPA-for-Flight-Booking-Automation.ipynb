"""Reproducible benchmark for the reservation validation stage.

This script compares a deliberately naive validation workflow with the
optimized validation/deduplication functions used by the project. Results are
printed from the local machine or CI environment; no benchmark values are
hard-coded in repository documentation.
"""

from __future__ import annotations

from statistics import mean
from time import perf_counter
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.flight_booking_rpa import (
    ValidationError,
    deduplicate,
    generate_reservations,
    validate_reservation,
)


def naive_validation(records):
    output = []
    seen = []
    for record in records:
        try:
            validated = validate_reservation(record)
        except ValidationError:
            continue
        if validated.pnr not in seen:
            seen.append(validated.pnr)
            output.append(validated)
    return output


def optimized_validation(records):
    valid = []
    for record in records:
        try:
            valid.append(validate_reservation(record))
        except ValidationError:
            continue
    return deduplicate(valid)


def measure(function, records, repeats=5):
    durations = []
    for _ in range(repeats):
        start = perf_counter()
        function(records)
        durations.append(perf_counter() - start)
    return mean(durations)


def main():
    records = generate_reservations(10_000, seed=42)
    naive = measure(naive_validation, records)
    optimized = measure(optimized_validation, records)
    improvement = ((naive - optimized) / naive * 100) if naive else 0.0

    print("Validation benchmark")
    print(f"Records: {len(records):,}")
    print("Repeats: 5")
    print(f"Naive mean runtime: {naive:.6f} seconds")
    print(f"Optimized mean runtime: {optimized:.6f} seconds")
    print(f"Runtime change: {improvement:.2f}%")

    output = ROOT / "benchmark_results.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["records", "repeats", "naive_seconds", "optimized_seconds", "runtime_change_percent"])
        writer.writerow([len(records), 5, f"{naive:.6f}", f"{optimized:.6f}", f"{improvement:.2f}"])
    print(f"Results written to {output.name}")


if __name__ == "__main__":
    main()

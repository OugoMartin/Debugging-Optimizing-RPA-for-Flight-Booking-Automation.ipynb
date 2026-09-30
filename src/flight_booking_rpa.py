"""Production-style flight booking RPA simulation.

This module demonstrates validation, retries, logging, deterministic test-data
creation, duplicate handling, and summary metrics for an automation workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional, Tuple
import logging
import random
import re
import string
import time


VALID_AIRPORTS = {
    "JFK", "LAX", "HND", "LHR", "SIN", "FRA",
    "PEK", "HKG", "CDG", "DXB", "SYD",
}
VALID_STATUSES = {"Confirmed", "Checked-in", "Pending", "Canceled"}
PROCESSABLE_STATUSES = {"Confirmed", "Pending"}

LOGGER = logging.getLogger("flight_booking_rpa")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)


class ValidationError(ValueError):
    """Raised when a reservation does not meet workflow requirements."""


class TransientConfirmationError(RuntimeError):
    """Raised when a simulated downstream service fails temporarily."""


@dataclass(frozen=True)
class Reservation:
    pnr: str
    passenger: str
    origin: str
    destination: str
    fare: float
    status: str


@dataclass
class PipelineMetrics:
    input_records: int = 0
    valid_records: int = 0
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    retries: int = 0

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


PASSENGERS = [
    "Martin Ougo", "Sam Wanga", "Osman Otieno", "Jemimah Ngare",
    "Benard Ngare", "Oliver Miller", "James John", "John Ogutu",
    "Jackie Junior", "Jeff Jabez", "Lydia Ngare", "Ethan Thomas",
    "Charlotte White", "Thomas Junior", "Harper Clark",
]


def generate_pnr(rng: random.Random) -> str:
    """Return a six-character uppercase alphanumeric PNR."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(rng.choice(alphabet) for _ in range(6))


def generate_reservations(
    count: int = 50,
    *,
    seed: Optional[int] = 42,
) -> List[Dict[str, object]]:
    """Generate reproducible synthetic reservation data."""
    if count < 0:
        raise ValueError("count must be non-negative")

    rng = random.Random(seed)
    airports = sorted(VALID_AIRPORTS)
    statuses = sorted(VALID_STATUSES)
    records: List[Dict[str, object]] = []

    for _ in range(count):
        origin, destination = rng.sample(airports, 2)
        records.append(
            {
                "PNR": generate_pnr(rng),
                "Passenger": rng.choice(PASSENGERS),
                "Origin": origin,
                "Destination": destination,
                "Fare": rng.randint(100, 300),
                "Status": rng.choice(statuses),
            }
        )

    return records


def _normalize_fare(value: object) -> float:
    """Convert a fare into a positive float."""
    if isinstance(value, str):
        value = value.strip().replace("$", "").replace(",", "")

    try:
        fare = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Fare must be numeric") from exc

    if fare <= 0:
        raise ValidationError("Fare must be greater than zero")
    return fare


def validate_reservation(record: Dict[str, object]) -> Reservation:
    """Validate and normalize a single reservation dictionary."""
    required = {"PNR", "Passenger", "Origin", "Destination", "Fare", "Status"}
    missing = sorted(required - record.keys())
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    pnr = str(record["PNR"]).strip().upper()
    passenger = str(record["Passenger"]).strip()
    origin = str(record["Origin"]).strip().upper()
    destination = str(record["Destination"]).strip().upper()
    status = str(record["Status"]).strip()

    if not re.fullmatch(r"[A-Z0-9]{6}", pnr):
        raise ValidationError("PNR must be exactly 6 uppercase alphanumeric characters")
    if not passenger:
        raise ValidationError("Passenger must not be blank")
    if origin not in VALID_AIRPORTS:
        raise ValidationError(f"Unsupported origin airport: {origin}")
    if destination not in VALID_AIRPORTS:
        raise ValidationError(f"Unsupported destination airport: {destination}")
    if origin == destination:
        raise ValidationError("Origin and destination must be different")
    if status not in VALID_STATUSES:
        raise ValidationError(f"Unsupported status: {status}")

    return Reservation(
        pnr=pnr,
        passenger=passenger,
        origin=origin,
        destination=destination,
        fare=_normalize_fare(record["Fare"]),
        status=status,
    )


def deduplicate(records: Iterable[Reservation]) -> List[Reservation]:
    """Keep the first valid reservation for each PNR."""
    seen = set()
    unique: List[Reservation] = []

    for record in records:
        if record.pnr in seen:
            LOGGER.warning("Duplicate PNR skipped: %s", record.pnr)
            continue
        seen.add(record.pnr)
        unique.append(record)

    return unique


def simulate_confirmation_service(
    reservation: Reservation,
    *,
    rng: random.Random,
    transient_failure_rate: float = 0.10,
) -> str:
    """Simulate an I/O-bound booking-confirmation service."""
    if not 0 <= transient_failure_rate <= 1:
        raise ValueError("transient_failure_rate must be between 0 and 1")

    if rng.random() < transient_failure_rate:
        raise TransientConfirmationError(
            f"Temporary confirmation service failure for {reservation.pnr}"
        )

    return "confirmed"


def confirm_with_retry(
    reservation: Reservation,
    *,
    rng: random.Random,
    max_attempts: int = 3,
    transient_failure_rate: float = 0.10,
    base_delay_seconds: float = 0.01,
) -> Tuple[bool, int]:
    """Confirm a reservation with bounded exponential backoff."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    retries = 0

    for attempt in range(1, max_attempts + 1):
        try:
            simulate_confirmation_service(
                reservation,
                rng=rng,
                transient_failure_rate=transient_failure_rate,
            )
            return True, retries
        except TransientConfirmationError as exc:
            if attempt == max_attempts:
                LOGGER.error("%s; attempts exhausted", exc)
                return False, retries

            retries += 1
            delay = base_delay_seconds * (2 ** (attempt - 1))
            LOGGER.warning("%s; retrying in %.3fs", exc, delay)
            if delay > 0:
                time.sleep(delay)

    return False, retries


def run_pipeline(
    records: Iterable[Dict[str, object]],
    *,
    seed: int = 42,
    transient_failure_rate: float = 0.10,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.0,
) -> Dict[str, int]:
    """Validate, deduplicate, process, and summarize reservation records."""
    materialized = list(records)
    metrics = PipelineMetrics(input_records=len(materialized))
    valid: List[Reservation] = []

    for raw in materialized:
        try:
            valid.append(validate_reservation(raw))
        except ValidationError as exc:
            LOGGER.error("Invalid reservation skipped: %s", exc)

    valid = deduplicate(valid)
    metrics.valid_records = len(valid)
    rng = random.Random(seed)

    for reservation in valid:
        if reservation.status not in PROCESSABLE_STATUSES:
            metrics.skipped += 1
            LOGGER.info(
                "PNR %s skipped because status is %s",
                reservation.pnr,
                reservation.status,
            )
            continue

        success, retries = confirm_with_retry(
            reservation,
            rng=rng,
            max_attempts=max_attempts,
            transient_failure_rate=transient_failure_rate,
            base_delay_seconds=base_delay_seconds,
        )
        metrics.retries += retries

        if success:
            metrics.processed += 1
            LOGGER.info("PNR %s processed successfully", reservation.pnr)
        else:
            metrics.failed += 1

    return metrics.to_dict()


def main() -> None:
    records = generate_reservations(50, seed=42)
    summary = run_pipeline(
        records,
        seed=42,
        transient_failure_rate=0.10,
        max_attempts=3,
        base_delay_seconds=0.01,
    )
    print("\nPipeline summary")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

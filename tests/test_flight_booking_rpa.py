import unittest

from src.flight_booking_rpa import (
    Reservation,
    ValidationError,
    deduplicate,
    generate_reservations,
    run_pipeline,
    validate_reservation,
)


class FlightBookingRPATests(unittest.TestCase):
    def test_generation_is_reproducible(self):
        first = generate_reservations(5, seed=7)
        second = generate_reservations(5, seed=7)
        self.assertEqual(first, second)

    def test_generated_route_has_different_airports(self):
        records = generate_reservations(100, seed=1)
        self.assertTrue(
            all(r["Origin"] != r["Destination"] for r in records)
        )

    def test_validates_and_normalizes_fare(self):
        record = {
            "PNR": "ABC123",
            "Passenger": "Test Passenger",
            "Origin": "JFK",
            "Destination": "LAX",
            "Fare": "$250.50",
            "Status": "Confirmed",
        }
        result = validate_reservation(record)
        self.assertEqual(result.fare, 250.50)

    def test_rejects_missing_field(self):
        record = {
            "PNR": "ABC123",
            "Passenger": "Test Passenger",
            "Origin": "JFK",
            "Destination": "LAX",
            "Status": "Confirmed",
        }
        with self.assertRaises(ValidationError):
            validate_reservation(record)

    def test_rejects_invalid_airport(self):
        record = {
            "PNR": "ABC123",
            "Passenger": "Test Passenger",
            "Origin": "XXX",
            "Destination": "LAX",
            "Fare": 250,
            "Status": "Confirmed",
        }
        with self.assertRaises(ValidationError):
            validate_reservation(record)

    def test_deduplicates_by_pnr(self):
        records = [
            Reservation("ABC123", "A", "JFK", "LAX", 100.0, "Confirmed"),
            Reservation("ABC123", "B", "LAX", "JFK", 200.0, "Confirmed"),
        ]
        result = deduplicate(records)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].passenger, "A")

    def test_pipeline_counts_invalid_and_skipped_records(self):
        records = [
            {
                "PNR": "ABC123",
                "Passenger": "A",
                "Origin": "JFK",
                "Destination": "LAX",
                "Fare": 200,
                "Status": "Confirmed",
            },
            {
                "PNR": "DEF456",
                "Passenger": "B",
                "Origin": "LAX",
                "Destination": "JFK",
                "Fare": 180,
                "Status": "Canceled",
            },
            {
                "PNR": "BAD",
                "Passenger": "C",
                "Origin": "JFK",
                "Destination": "LAX",
                "Fare": 120,
                "Status": "Confirmed",
            },
        ]
        summary = run_pipeline(
            records,
            seed=5,
            transient_failure_rate=0.0,
            base_delay_seconds=0.0,
        )
        self.assertEqual(summary["input_records"], 3)
        self.assertEqual(summary["valid_records"], 2)
        self.assertEqual(summary["processed"], 1)
        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(summary["failed"], 0)


if __name__ == "__main__":
    unittest.main()

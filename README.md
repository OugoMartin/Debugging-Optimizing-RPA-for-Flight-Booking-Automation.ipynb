# Debugging & Optimizing RPA for Flight Booking Automation

A Python portfolio project that demonstrates how to debug, harden, and optimize an RPA-style flight-booking confirmation workflow.

## Project Overview

This project simulates a flight-booking automation pipeline and focuses on the engineering work required to make automation reliable in the presence of bad data, duplicate records, transient failures, and inefficient processing.

The repository now separates the **demonstration notebook** from the **production-style automation logic** so the project is easier to review, run, and extend.

## Business Scenario

A travel operations team receives reservation records that must be validated and processed before downstream confirmation activity. In a real automation workflow, common problems include:

- Missing reservation fields
- Invalid fare values
- Invalid airport codes
- Duplicate PNRs
- Origin and destination conflicts
- Transient confirmation-service failures
- Poor observability when automation fails

This project addresses those failure modes with validation, structured logging, retries, metrics, and testable Python functions.

## What This Project Demonstrates

- Defensive Python programming
- Data validation and normalization
- Exception handling and retry logic
- Duplicate detection
- Structured logging
- RPA-style workflow orchestration
- Performance-aware batch processing
- Unit testing
- Reproducible portfolio documentation

## Repository Structure

```text
.
├── README.md
├── Debugging_&_Optimizing_RPA_for_Flight_Booking_Automation.ipynb
├── Debug and Optimize a Python Flight-Booking Confirmation Automation documentation report.txt
├── src/
│   └── flight_booking_rpa.py
├── tests/
│   └── test_flight_booking_rpa.py
├── requirements.txt
└── .gitignore
```

## Core Workflow

1. Generate or ingest reservation records.
2. Validate required fields.
3. Normalize fares to numeric values.
4. Validate airport codes and routes.
5. Remove duplicate reservations.
6. Process eligible reservations.
7. Retry transient failures.
8. Log outcomes.
9. Produce processing metrics.

## Key Engineering Improvements

### 1. Reproducible test data

The original notebook generated random records without a fixed seed. The improved implementation supports deterministic data generation so debugging and testing are repeatable.

### 2. Strong validation

Reservations are checked for:

- Required fields
- Six-character PNR format
- Supported airport codes
- Different origin and destination
- Positive numeric fare
- Supported booking status

### 3. Clear separation of concerns

Generation, validation, processing, retry behavior, and metrics are implemented as separate functions. This makes the project easier to test and maintain.

### 4. Retry-safe automation

Transient failures are retried with exponential backoff. Permanent validation failures are rejected immediately instead of being retried unnecessarily.

### 5. Logging and metrics

The workflow records processed, skipped, failed, retried, and invalid reservations. This provides the observability expected in production automation.

## Example Usage

```python
from src.flight_booking_rpa import generate_reservations, run_pipeline

reservations = generate_reservations(50, seed=42)
summary = run_pipeline(reservations)

print(summary)
```

Example summary structure:

```python
{
    "input_records": 50,
    "valid_records": 50,
    "processed": 39,
    "skipped": 11,
    "failed": 0,
    "retries": 3
}
```

Actual values depend on the generated dataset and simulated confirmation results.

## Run Locally

```bash
git clone https://github.com/OugoMartin/Debugging-Optimizing-RPA-for-Flight-Booking-Automation.ipynb.git
cd Debugging-Optimizing-RPA-for-Flight-Booking-Automation.ipynb

python -m venv .venv
```

Activate the environment:

**Windows**

```bash
.venv\Scripts\activate
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the automation:

```bash
python src/flight_booking_rpa.py
```

Run tests:

```bash
python -m unittest discover -s tests
```

## Portfolio Value

This project is positioned as an automation-engineering case study rather than only a notebook exercise. It demonstrates how a Python automation can be redesigned for reliability, observability, maintainability, and testing.

Relevant skills include:

**Python · RPA · Automation · Debugging · Exception Handling · Data Validation · Logging · Retry Logic · Unit Testing · Workflow Optimization**

## Important Note

The flight reservations and confirmation behavior in this repository are simulated. The project does not connect to a live airline reservation system and does not claim production benchmark results unless they are reproduced and documented from an actual run.

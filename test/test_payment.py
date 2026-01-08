import pytest #type: ignore
from pathlib import Path
from collections import Counter
import re

TRIP_FILE = Path("../output/trip.sql")
PAYMENT_FILE = Path("../output/payment.sql")

# =====================
# PARSE TRIP
# =====================
def parse_completed_trips(file_path):
    trips = {}
    pattern = re.compile(
        r"\(\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*'([^']+)'\s*,\s*[^,]*,\s*[^,]*,\s*([0-9.]+)\s*\)"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    matches = pattern.findall(content)
    for match in matches:
        trip_id = int(match[0])
        status = match[1]
        fare = float(match[2])
        if status == "completed":
            trips[trip_id] = fare
    return trips

# =====================
# PARSE PAYMENT
# =====================
def parse_payment(file_path):
    payments = []
    pattern = re.compile(
        r"\(\s*(\d+),\s*(\d+),\s*([0-9.]+),\s*'(\w+)',\s*'(\w+)'\s*\)"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    matches = pattern.findall(content)
    for match in matches:
        payments.append({
            "payment_id": int(match[0]),
            "trip_id": int(match[1]),
            "amount": float(match[2]),
            "method": match[3],
            "status": match[4]
        })
    return payments

# =====================
# TESTS
# =====================
def test_trip_completed_only():
    trips = parse_completed_trips(TRIP_FILE)
    payments = parse_payment(PAYMENT_FILE)
    for p in payments:
        assert p["trip_id"] in trips, f"Payment for non-completed trip {p['trip_id']}"

def test_amount_positive():
    payments = parse_payment(PAYMENT_FILE)
    for p in payments:
        assert p["amount"] >= 0, f"Payment amount negative: {p}"

def test_methods_and_status():
    payments = parse_payment(PAYMENT_FILE)
    valid_methods = {"cash", "wallet", "credit"}
    valid_status = {"completed", "failed"}
    for p in payments:
        assert p["method"] in valid_methods, f"Invalid payment method {p['method']}"
        assert p["status"] in valid_status, f"Invalid payment status {p['status']}"

def test_payment_ids_unique():
    payments = parse_payment(PAYMENT_FILE)
    ids = [p["payment_id"] for p in payments]
    assert len(ids) == len(set(ids)), "Duplicate payment_id found"

def test_amount_matches_fare():
    trips = parse_completed_trips(TRIP_FILE)
    payments = parse_payment(PAYMENT_FILE)
    for p in payments:
        assert abs(p["amount"] - trips[p["trip_id"]]) < 0.01, f"Payment amount {p['amount']} does not match fare {trips[p['trip_id']]}"


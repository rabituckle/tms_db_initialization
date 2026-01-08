import pytest #type: ignore 
from pathlib import Path
from datetime import datetime
from collections import Counter
import re

TRIP_FILE = Path("../output/trip.sql")
TRIP_REQUEST_FILE = Path("../output/trip_request.sql")
DRIVER_FILE = Path("../output/driver.sql")
VEHICLE_FILE = Path("../output/vehicle.sql")

# =====================
# PARSER
# =====================
def parse_sql_tuples(file_path):
    """Trả về list các string của tuple, bỏ dòng header, chỉ lấy các dòng bắt đầu '('"""
    tuples = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("(") and line.endswith((")", ");", "),")):
                tuples.append(line)
    return tuples

def parse_trip_rows(file_path):
    trips = []
    pattern = re.compile(
        r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']+)'\s*,\s*(NULL|'[^']+')\s*,\s*(NULL|'[^']+')\s*,\s*([\d\.]+)\s*\)"
    )
    for line in parse_sql_tuples(file_path):
        m = pattern.match(line)
        if not m:
            continue
        trip = {
            "trip_id": int(m.group(1)),
            "trip_request_id": int(m.group(2)),
            "driver_id": int(m.group(3)),
            "vehicle_id": int(m.group(4)),
            "status": m.group(5),
            "start_time": None if m.group(6) == "NULL" else datetime.strptime(m.group(6).strip("'"), "%Y-%m-%d %H:%M:%S"),
            "end_time": None if m.group(7) == "NULL" else datetime.strptime(m.group(7).strip("'"), "%Y-%m-%d %H:%M:%S"),
            "fare": float(m.group(8))
        }
        trips.append(trip)
    return trips

def parse_trip_request_ids(file_path):
    pattern = re.compile(r"\(\s*(\d+)")
    ids = set()
    for line in parse_sql_tuples(file_path):
        m = pattern.match(line)
        if m:
            ids.add(int(m.group(1)))
    return ids

def parse_driver_ids(file_path):
    pattern = re.compile(r"\(\s*(\d+)")
    ids = set()
    for line in parse_sql_tuples(file_path):
        m = pattern.match(line)
        if m:
            ids.add(int(m.group(1)))
    return ids

def parse_vehicle_ids(file_path):
    pattern = re.compile(r"\(\s*(\d+)")
    ids = set()
    for line in parse_sql_tuples(file_path):
        m = pattern.match(line)
        if m:
            ids.add(int(m.group(1)))
    return ids

# =====================
# TESTS
# =====================
def test_trip_ids_unique():
    trips = parse_trip_rows(TRIP_FILE)
    ids = [t["trip_id"] for t in trips]
    assert len(ids) == len(set(ids)), "trip_id not unique"

def test_trip_request_exists():
    trips = parse_trip_rows(TRIP_FILE)
    request_ids = parse_trip_request_ids(TRIP_REQUEST_FILE)
    for t in trips:
        assert t["trip_request_id"] in request_ids, f"trip_request_id {t['trip_request_id']} not exist"

def test_driver_exists():
    trips = parse_trip_rows(TRIP_FILE)
    driver_ids = parse_driver_ids(DRIVER_FILE)
    for t in trips:
        assert t["driver_id"] in driver_ids, f"driver_id {t['driver_id']} not exist"

def test_vehicle_exists_and_fare():
    trips = parse_trip_rows(TRIP_FILE)
    vehicle_ids = parse_vehicle_ids(VEHICLE_FILE)
    for t in trips:
        assert t["vehicle_id"] in vehicle_ids, f"vehicle_id {t['vehicle_id']} not exist"
        assert t["fare"] >= 0, f"fare {t['fare']} invalid"

def test_start_end_time():
    trips = parse_trip_rows(TRIP_FILE)
    for t in trips:
        if t["status"] in ["in_progress", "completed"]:
            assert t["start_time"] is not None, "start_time is None for in_progress/completed trip"
            assert t["end_time"] is not None, "end_time is None for in_progress/completed trip"
            assert t["start_time"] <= t["end_time"], "start_time after end_time"

def test_status_values():
    trips = parse_trip_rows(TRIP_FILE)
    valid_status = {"assigned","in_progress","completed","canceled"}
    for t in trips:
        assert t["status"] in valid_status, f"Invalid status {t['status']}"

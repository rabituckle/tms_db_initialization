import pytest #type:ignore
from pathlib import Path
from datetime import datetime
from collections import Counter
import re

TRIP_FILE = Path("../output/trip.sql")
TRIP_REQUEST_FILE = Path("../output/trip_request.sql")
DRIVER_FILE = Path("../output/driver.sql")
VEHICLE_FILE = Path("../output/vehicle.sql")

# =====================
# PARSE DRIVER & VEHICLE
# =====================
def parse_drivers(file_path):
    ids = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("("):
                start = line.find("(")+1
                end = line.find(",")
                ids.add(int(line[start:end]))
    return ids

def parse_vehicles(file_path):
    vehicle_ids = set()
    vehicle_type_map = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("("):
                # (vehicle_id, 'type', 'status', driver_id)
                parts = re.findall(r"(?:'([^']*)'|([^,]+))", line)
                vals = [g1 if g1 else g2 for g1,g2 in parts]
                vid = int(vals[0])
                vehicle_ids.add(vid)
                vehicle_type_map[vid] = vals[1]  # 'car' hoặc 'motorbike'
    return vehicle_ids, vehicle_type_map

# =====================
# PARSE TRIP
# =====================
def parse_trips(file_path):
    trips = []
    pattern = re.compile(r"\((.*?)\)")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        matches = pattern.findall(content)
        for m in matches:
            # tách cột, tôn trọng string với dấu nháy
            cols = re.findall(r"(?:'([^']*)'|([^,]+))", m)
            values = [g1 if g1 else g2 for g1,g2 in cols]
            trip = {
                "trip_id": int(values[0]),
                "trip_request_id": int(values[1]),
                "driver_id": int(values[2]),
                "vehicle_id": int(values[3]),
                "status": values[4],
                "start_time": None if values[5]=="NULL" else datetime.strptime(values[5], "%Y-%m-%d %H:%M:%S"),
                "end_time": None if values[6]=="NULL" else datetime.strptime(values[6], "%Y-%m-%d %H:%M:%S"),
                "fare": float(values[7])
            }
            trips.append(trip)
    return trips

# =====================
# TESTS
# =====================
def test_trip_ids_unique():
    trips = parse_trips(TRIP_FILE)
    ids = [t["trip_id"] for t in trips]
    assert len(ids) == len(set(ids)), "trip_id not unique"

def test_trip_request_exists():
    trips = parse_trips(TRIP_FILE)
    requests = parse_trips(TRIP_REQUEST_FILE)  # dùng chung parser vì chỉ lấy id
    request_ids = set(r["trip_id"] for r in requests)  # sửa lại nếu parser khác
    for t in trips:
        assert t["trip_request_id"] in request_ids, f"trip_request_id {t['trip_request_id']} not exists"

def test_driver_exists():
    trips = parse_trips(TRIP_FILE)
    driver_ids = parse_drivers(DRIVER_FILE)
    for t in trips:
        assert t["driver_id"] in driver_ids, f"driver_id {t['driver_id']} not exists"

def test_vehicle_exists_and_fare():
    trips = parse_trips(TRIP_FILE)
    vehicle_ids, vehicle_type_map = parse_vehicles(VEHICLE_FILE)
    for t in trips:
        vid = t["vehicle_id"]
        assert vid in vehicle_ids, f"vehicle_id {vid} not exists"
        # kiểm tra fare theo type xe
        if vehicle_type_map[vid] == "car":
            assert 5 <= t["fare"] <= 50, f"fare {t['fare']} unrealistic for car"
        elif vehicle_type_map[vid] == "motorbike":
            assert 2 <= t["fare"] <= 20, f"fare {t['fare']} unrealistic for motorbike"

def test_start_end_time():
    trips = parse_trips(TRIP_FILE)
    for t in trips:
        if t["start_time"] and t["end_time"]:
            assert t["start_time"] <= t["end_time"], f"start_time after end_time for trip {t['trip_id']}"

import pytest #type:ignore
from pathlib import Path
from datetime import datetime, timedelta

# =====================
# CONFIG
# =====================
APPUSER_FILE = Path("../output/appuser.sql")
DRIVER_FILE = Path("../output/driver.sql")

LAT_MIN, LAT_MAX = 50.0, 55.0     # England
LONG_MIN, LONG_MAX = -6.0, 2.0
TOLERANCE_SECONDS_AVAILABLE = 2*3600   # ±2 tiếng
TOLERANCE_DAYS_UNAVAILABLE = (1, 2)   # 1-2 ngày

# =====================
# HELPERS
# =====================
def parse_active_drivers(file_path):
    drivers = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if "'driver'" in line and "'active'" in line:
                start = line.find("(")+1
                end = line.find(",")
                drivers.add(int(line[start:end]))
    return drivers

def parse_driver(file_path):
    drivers = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    for row in content.split("VALUES")[1].split(",\n"):
        row = row.strip().strip(";").strip("()")
        if not row:
            continue
        user_id, work_status, longitude, latitude, last_update = row.split(", ")
        drivers.append({
            "user_id": int(user_id),
            "work_status": work_status.strip("'"),
            "longitude": float(longitude),
            "latitude": float(latitude),
            "last_update": datetime.strptime(last_update.strip("'"), "%Y-%m-%d %H:%M:%S")
        })
    return drivers

# =====================
# TESTS
# =====================
def test_user_id_in_appuser():
    active_driver_ids = parse_active_drivers(APPUSER_FILE)
    drivers = parse_driver(DRIVER_FILE)
    for d in drivers:
        assert d["user_id"] in active_driver_ids, f"user_id {d['user_id']} not active driver in appuser"

def test_work_status():
    drivers = parse_driver(DRIVER_FILE)
    for d in drivers:
        assert d["work_status"] in ["available", "unavailable"], f"Invalid work_status {d['work_status']}"

def test_lat_long_range():
    drivers = parse_driver(DRIVER_FILE)
    for d in drivers:
        assert LAT_MIN <= d["latitude"] <= LAT_MAX, f"Latitude {d['latitude']} out of range"
        assert LONG_MIN <= d["longitude"] <= LONG_MAX, f"Longitude {d['longitude']} out of range"

def test_last_logic():
    drivers = parse_driver(DRIVER_FILE)
    now = datetime.now()
    for d in drivers:
        delta = now - d["last_update"]
        if d["work_status"] == "available":
            # ±4 tiếng
            assert delta.total_seconds() <= 4*3600, \
                f"Available driver last_update too old: {d['last_update']}"
        else:
            # unavailable: 1 ngày -> 1 tuần
            min_sec = 1*86400
            max_sec = 7*86400
            assert min_sec <= delta.total_seconds() <= max_sec, \
                f"Unavailable driver last_update not in 1 week: {d['last_update']}"


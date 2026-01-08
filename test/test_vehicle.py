import re
from pathlib import Path

VEHICLE_FILE = Path("../output/vehicle.sql")
DRIVER_FILE = Path("../output/driver.sql")

# =====================
# HELPERS
# =====================
def parse_driver_ids(file_path):
    ids = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("("):
                user_id = int(line.split(",")[0].strip("() "))
                ids.add(user_id)
    return ids

def parse_vehicles(file_path):
    vehicles = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    for row in content.split("VALUES")[1].split(",\n"):
        row = row.strip().strip(";").strip("()")
        if not row:
            continue
        vehicle_id, license_plate, v_type, status, driver_id = row.split(", ")
        vehicles.append({
            "vehicle_id": int(vehicle_id),
            "license_plate": license_plate.strip("'"),
            "type": v_type.strip("'"),
            "status": status.strip("'"),
            "driver_id": int(driver_id)
        })
    return vehicles

def is_valid_uk_plate(plate):
    return bool(re.fullmatch(r"[A-Z]{2}\d{2} [A-Z]{3}", plate))

# =====================
# TESTS
# =====================
def test_driver_id_exists():
    driver_ids = parse_driver_ids(DRIVER_FILE)
    vehicles = parse_vehicles(VEHICLE_FILE)
    for v in vehicles:
        assert v["driver_id"] in driver_ids, f"Driver_id {v['driver_id']} not in driver.sql"

def test_vehicle_type():
    vehicles = parse_vehicles(VEHICLE_FILE)
    for v in vehicles:
        assert v["type"] in ["car", "motorbike"], f"Invalid vehicle type: {v['type']}"

def test_vehicle_status():
    vehicles = parse_vehicles(VEHICLE_FILE)
    for v in vehicles:
        assert v["status"] in ["active", "maintenance"], f"Invalid vehicle status: {v['status']}"

def test_license_plate_format():
    vehicles = parse_vehicles(VEHICLE_FILE)
    for v in vehicles:
        assert is_valid_uk_plate(v["license_plate"]), f"Invalid UK license plate: {v['license_plate']}"

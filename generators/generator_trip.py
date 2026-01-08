from faker import Faker  # type: ignore
import random
from datetime import datetime, timedelta
from pathlib import Path

# =====================
# CONFIG
# =====================
Faker.seed(2025)
fake = Faker("en_US")
random.seed(2025)

TRIP_REQUEST_FILE = Path("../output/trip_request.sql")
DRIVER_FILE = Path("../output/driver.sql")
VEHICLE_FILE = Path("../output/vehicle.sql")
OUTPUT_FILE = Path("../output/trip.sql")

N = 120000  # số trip muốn sinh

# Status
STATUS_LIST = ["assigned", "in_progress", "completed", "canceled"]

# Giá xe
FARE_BASE = {"car": 15, "motorbike": 8}  # đơn vị tạm tính

# =====================
# HELPER: parse từ SQL
# =====================
def parse_trip_requests(file_path):
    """Lấy trip_request_id và request_time"""
    trip_requests = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    values_part = content.split("VALUES")[1].strip().rstrip(";")
    lines = values_part.split(",\n")
    for line in lines:
        line = line.strip()[1:-1]  # bỏ ( )
        parts = [p.strip().strip("'") for p in line.split(",")]
        trip_requests.append({
            "trip_request_id": int(parts[0]),
            "user_id": int(parts[1]),
            "request_time": datetime.strptime(parts[-1], "%Y-%m-%d %H:%M:%S")
        })
    return trip_requests

def parse_drivers(file_path):
    """Lấy danh sách driver_id"""
    drivers = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    values_part = content.split("VALUES")[1].strip().rstrip(";")
    lines = values_part.split(",\n")
    for line in lines:
        line = line.strip()[1:-1]
        parts = [p.strip().strip("'") for p in line.split(",")]
        drivers.append(int(parts[0]))
    return drivers

def parse_vehicles(file_path):
    """Lấy vehicle_id và type"""
    vehicles = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    values_part = content.split("VALUES")[1].strip().rstrip(";")
    lines = values_part.split(",\n")
    for line in lines:
        line = line.strip()[1:-1]
        parts = [p.strip().strip("'") for p in line.split(",")]
        vehicles.append({
            "vehicle_id": int(parts[0]),
            "type": parts[2]
        })
    return vehicles

# =====================
# GENERATE TRIP
# =====================
trip_requests = parse_trip_requests(TRIP_REQUEST_FILE)
drivers = parse_drivers(DRIVER_FILE)
vehicles = parse_vehicles(VEHICLE_FILE)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("INSERT INTO trip (trip_id, trip_request_id, driver_id, vehicle_id, status, start_time, end_time, fare)\nVALUES\n")
    for i, tr in enumerate(trip_requests[:N]):
        trip_id = i + 1
        trip_request_id = tr["trip_request_id"]
        request_time = tr["request_time"]

        # Chọn driver + vehicle ngẫu nhiên
        driver_id = random.choice(drivers)
        vehicle = random.choice(vehicles)
        vehicle_id = vehicle["vehicle_id"]

        # Status
        status = random.choices(STATUS_LIST, weights=[0.1, 0.2, 0.6, 0.1], k=1)[0]

        # Start time >= request_time
        start_time = request_time + timedelta(minutes=random.randint(5, 120))
        # End time >= start_time nếu chưa canceled
        if status != "canceled":
            end_time = start_time + timedelta(minutes=random.randint(10, 90))
        else:
            end_time = None

        # Fare dựa trên loại xe
        base_fare = FARE_BASE.get(vehicle["type"], 10)
        fare = round(base_fare * random.uniform(0.8, 1.5), 2)

        # SQL line
        start_time_str = f"'{start_time.strftime('%Y-%m-%d %H:%M:%S')}'" if start_time else "NULL"
        end_time_str = f"'{end_time.strftime('%Y-%m-%d %H:%M:%S')}'" if end_time else "NULL"
        line = f"({trip_id}, {trip_request_id}, {driver_id}, {vehicle_id}, '{status}', {start_time_str}, {end_time_str}, {fare})"
        line += ",\n" if i < N - 1 else ";\n"
        f.write(line)

print(f"✅ Generated {OUTPUT_FILE} with {N} trip records")

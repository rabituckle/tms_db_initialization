import random
from pathlib import Path
from faker import Faker #type: ignore

# =====================
# CONFIG
# =====================
fake = Faker("en_GB")
Faker.seed(2025)
random.seed(2025)

DRIVER_FILE = Path("../output/driver.sql")
OUTPUT_FILE = Path("../output/vehicle.sql")

VEHICLE_TYPES = ["car", "motorbike"]
VEHICLE_TYPE_RATIO = [0.3, 0.7]  # motorbike 70%, car 30%
STATUS_OPTIONS = ["active", "maintenance"]
STATUS_RATIO = [0.8, 0.2]  # active 80%, maintenance 20%

# =====================
# HELPER
# =====================
def parse_driver_ids(file_path):
    """Lấy tất cả driver_id trong driver.sql"""
    ids = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("("):
                continue
            user_id = int(line.split(",")[0].strip("() "))
            ids.append(user_id)
    return ids

def random_license_plate():
    """Sinh UK license plate kiểu AB12 CDE"""
    letters1 = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    numbers = ''.join(random.choices('0123456789', k=2))
    letters2 = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
    return f"{letters1}{numbers} {letters2}"

# =====================
# GENERATE VEHICLE
# =====================
driver_ids = parse_driver_ids(DRIVER_FILE)
N = len(driver_ids)  # 1 vehicle mỗi driver
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("INSERT INTO vehicle (vehicle_id, license_plate, type, status, driver_id)\nVALUES\n")
    for i, driver_id in enumerate(driver_ids):
        vehicle_id = i + 1
        license_plate = random_license_plate()
        v_type = random.choices(VEHICLE_TYPES, VEHICLE_TYPE_RATIO)[0]
        status = random.choices(STATUS_OPTIONS, STATUS_RATIO)[0]
        line = f"({vehicle_id}, '{license_plate}', '{v_type}', '{status}', {driver_id})"
        line += ",\n" if i < N - 1 else ";\n"
        f.write(line)

print(f"✅ Generated {OUTPUT_FILE} with {N} vehicles")

import random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker #type:ignore

# =====================
# CONFIG
# =====================
fake = Faker("en_US")
Faker.seed(2025)
random.seed(2025)

APPUSER_FILE = Path("../output/appuser.sql")
OUTPUT_FILE = Path("../output/driver.sql")

# Viêt Nam lat/long
# Viêt Nam → England
LAT_MIN, LAT_MAX = 50.0, 55.0
LONG_MIN, LONG_MAX = -6.0, 2.0

# tỉ lệ unavailable
UNAVAILABLE_RATIO = 0.2

# =====================
# HELPER
# =====================
def parse_active_drivers(file_path):
    """Trả về danh sách user_id có role=driver và status=active"""
    drivers = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if "'driver'" in line and "'active'" in line:
                # lấy user_id đầu tiên trong ngoặc
                start = line.find("(") + 1
                end = line.find(",")
                drivers.append(int(line[start:end]))
    return drivers

def random_lat_long():
    lat = round(random.uniform(LAT_MIN, LAT_MAX), 6)
    long = round(random.uniform(LONG_MIN, LONG_MAX), 6)
    return lat, long

def random_last_update(work_status):
    now = datetime.now()
    if work_status == "unavailable":
        dt = now - timedelta(days=random.randint(1, 2), seconds=random.randint(0, 86400))
    else:
        dt = now - timedelta(seconds=random.randint(0, 2*3600))
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# =====================
# GENERATE DRIVER
# =====================
driver_ids = parse_active_drivers(APPUSER_FILE)
N = len(driver_ids)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("INSERT INTO driver (user_id, work_status, longitude, latitude, last_update)\nVALUES\n")
    for i, user_id in enumerate(driver_ids):
        work_status = "unavailable" if random.random() < UNAVAILABLE_RATIO else "available"
        latitude, longitude = random_lat_long()
        last_update = random_last_update(work_status)
        line = f"({user_id}, '{work_status}', {longitude}, {latitude}, '{last_update}')"
        line += ",\n" if i < N - 1 else ";\n"
        f.write(line)

print(f"✅ Generated {OUTPUT_FILE} with {N} active driver records using Faker")

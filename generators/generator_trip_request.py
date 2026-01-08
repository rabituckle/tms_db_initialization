import random
from pathlib import Path
from faker import Faker #type: ignore
from datetime import datetime, timedelta

# =====================
# CONFIG
# =====================
fake = Faker("en_GB")
Faker.seed(2025)
random.seed(2025)

APPUSER_FILE = Path("../output/appuser.sql")
OUTPUT_FILE = Path("../output/trip_request.sql")

TOTAL_TRIP_REQUESTS = 100_000
STATUS_OPTIONS = ["requested", "rejected", "accepted"]
STATUS_RATIO = [0.10, 0.15, 0.75]

# =====================
# PARSE CUSTOMER JOIN DATE
# =====================
join_date_of_customer = {}
with open(APPUSER_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("("):
            parts = line.strip("();").split(",")
            user_id = int(parts[0].strip())
            role = parts[5].strip().strip("'")
            join_date_str = parts[6].strip().strip("'")
            join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
            if role == "customer":
                join_date_of_customer[user_id] = join_date

customers = list(join_date_of_customer.keys())

# =====================
# GENERATE TRIP REQUESTS
# =====================
trip_requests = []

for _ in range(TOTAL_TRIP_REQUESTS):
    c_id = random.choice(customers)
    join_date = join_date_of_customer[c_id]

    # request_time >= join_date
    delta_days = max((datetime.now() - join_date).days, 0)
    request_time = join_date + timedelta(
        days=random.randint(0, delta_days),
        minutes=random.randint(1, 120)
    )

    pickup_addr = fake.address().replace("\n", ", ").replace("'", "''")
    drop_addr = fake.address().replace("\n", ", ").replace("'", "''")

    # lat/lon England ±0.3 deg for drop
    base_lat = random.uniform(50.0, 55.0)
    base_lon = random.uniform(-5.0, 1.5)
    delta_lat = random.uniform(-0.3, 0.3)
    delta_lon = random.uniform(-0.3, 0.3)

    pickup_lat = round(base_lat, 6)
    pickup_lon = round(base_lon, 6)
    drop_lat = round(base_lat + delta_lat, 6)
    drop_lon = round(base_lon + delta_lon, 6)

    status = random.choices(STATUS_OPTIONS, STATUS_RATIO)[0]

    trip_requests.append((
        request_time,  # index 0
        c_id,          # index 1: user_id
        pickup_addr,   # 2
        drop_addr,     # 3
        pickup_lat,    # 4
        pickup_lon,    # 5
        drop_lat,      # 6
        drop_lon,      # 7
        status         # 8
    ))

# =====================
# SORT BY REQUEST TIME
# =====================
trip_requests.sort(key=lambda x: x[0])

# =====================
# ASSIGN TRIP_REQUEST_ID
# =====================
trip_requests_with_id = []
for i, t in enumerate(trip_requests):
    trip_requests_with_id.append((
        i + 1,   # trip_request_id
        t[1],    # user_id
        t[2],    # pickup_location
        t[3],    # drop_location
        t[4],    # pickup_latitude
        t[5],    # pickup_longitude
        t[6],    # drop_latitude
        t[7],    # drop_longitude
        t[8],    # status
        t[0]     # request_time
    ))

# =====================
# WRITE SQL FILE
# =====================
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(
        "INSERT INTO trip_request "
        "(trip_request_id, user_id, pickup_location, drop_location, pickup_latitude, pickup_longitude, drop_latitude, drop_longitude, status, request_time)\nVALUES\n"
    )
    for i, t in enumerate(trip_requests_with_id):
        line = (
            f"({t[0]}, {t[1]}, '{t[2]}', '{t[3]}', "
            f"{t[4]}, {t[5]}, {t[6]}, {t[7]}, "
            f"'{t[8]}', '{t[9].strftime('%Y-%m-%d %H:%M:%S')}')"
        )
        line += ",\n" if i < len(trip_requests_with_id)-1 else ";\n"
        f.write(line)

print(f"✅ Generated {len(trip_requests_with_id)} trip_requests")

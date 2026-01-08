import random
import re
from pathlib import Path

# =====================
# CONFIG
# =====================
TRIP_FILE = Path("../output/trip.sql")
OUTPUT_FILE = Path("../output/payment.sql")

PAYMENT_METHODS = ["cash", "wallet", "credit"]
PAYMENT_METHOD_PROBS = [0.5, 0.4, 0.1]

PAYMENT_STATUS = ["completed", "failed"]
PAYMENT_STATUS_PROBS = [0.95, 0.05] 

# =====================
# HELPER
# =====================
def parse_completed_trips(file_path):
    """
    Parse trip.sql, trả về list dict: [{"trip_id":.., "fare":..}]
    chỉ lấy trip có status='completed'
    """
    trips = []
    # (\d+) -> trip_id, \d+,\d+,\d+ -> các số khác, '...' -> status
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
            trips.append({"trip_id": trip_id, "fare": fare})
    return trips

# =====================
# GENERATE PAYMENT
# =====================
trips = parse_completed_trips(TRIP_FILE)
N = len(trips)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("INSERT INTO payment (payment_id, trip_id, amount, payment_method, status)\nVALUES\n")
    for i, trip in enumerate(trips):
        payment_id = i + 1
        trip_id = trip["trip_id"]
        amount = trip["fare"]
        method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_PROBS, k=1)[0]
        status = random.choices(PAYMENT_STATUS, weights=PAYMENT_STATUS_PROBS, k=1)[0]
        line = f"({payment_id}, {trip_id}, {amount:.2f}, '{method}', '{status}')"
        line += ",\n" if i < N - 1 else ";\n"
        f.write(line)

print(f"✅ Generated {OUTPUT_FILE} with {N} payment records (only completed trips)")

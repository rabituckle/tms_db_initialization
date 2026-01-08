import random
import re
from pathlib import Path

# =====================
# CONFIG
# =====================
TRIP_FILE = Path("../output/trip.sql")
OUTPUT_FILE = Path("../output/feedback.sql")

RATING_PROBS_COMPLETED = [1, 1, 3, 2, 3]  # rating 1-5
RATING_PROBS_CANCELED = [8, 2, 0, 0, 0]   # rating 1-5

PROB_HAS_RATING = 0.8
PROB_HAS_COMMENT = 0.3

# =====================
# HELPER
# =====================
def parse_eligible_trips(file_path):
    """Lấy trip_id và status của các trip completed/canceled"""
    trips = []
    pattern = re.compile(
        r"\(\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*'([^']+)'"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    matches = pattern.findall(content)
    for trip_id, status in matches:
        if status in {"completed", "canceled"}:
            trips.append({"trip_id": int(trip_id), "status": status})
    return trips

# =====================
# GENERATE FEEDBACK
# =====================
trips = parse_eligible_trips(TRIP_FILE)
N = len(trips)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("INSERT INTO feedback (feedback_id, trip_id, rating, comment)\nVALUES\n")
    feedback_id = 1
    for i, trip in enumerate(trips):
        if random.random() > PROB_HAS_RATING:
            continue  # skip trips without rating

        # rating
        if trip["status"] == "completed":
            rating = random.choices([1, 2, 3, 4, 5], weights=RATING_PROBS_COMPLETED, k=1)[0]
        else:  # canceled
            rating = random.choices([1, 2, 3, 4, 5], weights=RATING_PROBS_CANCELED, k=1)[0]

        # comment
        comment = ""
        if random.random() < PROB_HAS_COMMENT:
            comment = f"'Feedback for trip {trip['trip_id']}'"

        line = f"({feedback_id}, {trip['trip_id']}, {rating}, {comment if comment else 'NULL'})"
        line += ",\n" if i < N - 1 else ";\n"
        f.write(line)
        feedback_id += 1

print(f"✅ Generated {OUTPUT_FILE} with {feedback_id -1} feedback records")

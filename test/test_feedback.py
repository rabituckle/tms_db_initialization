import pytest #type:ignore
from pathlib import Path
from datetime import datetime
import re

TRIP_FILE = Path("../output/trip.sql")
FEEDBACK_FILE = Path("../output/feedback.sql")

# =====================
# PARSE TRIP
# =====================
def parse_trips(file_path):
    """Trả về dict {trip_id: status}"""
    trips = {}
    pattern = re.compile(
        r"\(\s*(\d+),\s*\d+,\s*\d+,\s*\d+,\s*'([^']+)'"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    for trip_id, status in pattern.findall(content):
        trips[int(trip_id)] = status
    return trips

# =====================
# PARSE FEEDBACK
# =====================
def parse_feedback(file_path):
    """Trả về list dict: [{'feedback_id', 'trip_id', 'rating', 'comment'}]"""
    feedbacks = []
    pattern = re.compile(
        r"\(\s*(\d+),\s*(\d+),\s*(\d+),\s*(NULL|'[^']*')\s*\)"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    for f_id, trip_id, rating, comment in pattern.findall(content):
        feedbacks.append({
            "feedback_id": int(f_id),
            "trip_id": int(trip_id),
            "rating": int(rating),
            "comment": None if comment == "NULL" else comment.strip("'")
        })
    return feedbacks

# =====================
# TESTS
# =====================
def test_trip_id_valid():
    trips = parse_trips(TRIP_FILE)
    feedbacks = parse_feedback(FEEDBACK_FILE)
    for f in feedbacks:
        assert f["trip_id"] in trips, f"trip_id {f['trip_id']} not in trips"
        assert trips[f["trip_id"]] in {"completed", "canceled"}, f"trip_id {f['trip_id']} has invalid status"

def test_rating_valid():
    feedbacks = parse_feedback(FEEDBACK_FILE)
    for f in feedbacks:
        assert 1 <= f["rating"] <= 5, f"feedback_id {f['feedback_id']} has invalid rating {f['rating']}"

def test_comment_consistency():
    feedbacks = parse_feedback(FEEDBACK_FILE)
    for f in feedbacks:
        # comment có thể None hoặc string
        if f["comment"]:
            assert isinstance(f["comment"], str), f"feedback_id {f['feedback_id']} comment not string"
        else:
            assert f["comment"] is None

import pytest #type:ignore
import re
from collections import Counter
from pathlib import Path

# =====================
# CONFIG
# =====================
APPUSER_FILE = Path("../output/appuser.sql")
CUSTOMER_FILE = Path("../output/customer.sql")
PENALTY_VALUES = [0, 1, 2, 3]
PENALTY_PROBS = [0.7, 0.2, 0.07, 0.03]
TOLERANCE = 0.05  # ±5% tolerance

# =====================
# HELPERS
# =====================
def parse_appuser(file_path):
    """Trả về set các user_id có role=customer"""
    pattern = re.compile(
        r"\((\d+),\s*'[^']+',\s*'[^']+',\s*'[^']+',\s*\d+,\s*'customer',"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return set(int(m) for m in pattern.findall(content))

def parse_customer(file_path):
    """Trả về list dict {'user_id':..., 'penalty_count':...}"""
    pattern = re.compile(r"\((\d+),\s*(\d+)\)")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    customers = []
    for m in pattern.findall(content):
        customers.append({"user_id": int(m[0]), "penalty_count": int(m[1])})
    return customers

# =====================
# TESTS
# =====================
def test_user_id_in_appuser():
    appuser_ids = parse_appuser(APPUSER_FILE)
    customers = parse_customer(CUSTOMER_FILE)
    for c in customers:
        assert c["user_id"] in appuser_ids, f"user_id {c['user_id']} not in appuser"

def test_penalty_values():
    customers = parse_customer(CUSTOMER_FILE)
    for c in customers:
        assert c["penalty_count"] in PENALTY_VALUES, f"Invalid penalty_count: {c['penalty_count']}"

def test_penalty_ratio():
    customers = parse_customer(CUSTOMER_FILE)
    counts = Counter(c["penalty_count"] for c in customers)
    total = len(customers)
    for val, expected_ratio in zip(PENALTY_VALUES, PENALTY_PROBS):
        actual_ratio = counts[val] / total
        assert abs(actual_ratio - expected_ratio) <= TOLERANCE, f"Penalty {val} ratio out of tolerance: {actual_ratio:.2f} vs {expected_ratio}"

import pytest # type: ignore
import re
from collections import Counter

# =====================
# CONFIG
# =====================
APPUSER_SQL_FILE = r"D:\HUST\Source code\Database\output\appuser.sql"
ROLE_RATIO = {"customer": 0.8, "driver": 0.2}
STATUS_RATIO = {"active": 0.88, "inactive": 0.10, "suspended": 0.02}
TOLERANCE = 0.05  # ±5% tolerance

# =====================
# HELPER
# =====================
def parse_appuser(file_path):
    """Đọc file SQL, trả về list các dict"""
    users = []
    pattern = re.compile(r"\((\d+),\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*(\d+),\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    matches = pattern.findall(content)
    for m in matches:
        user = {
            "user_id": int(m[0]),
            "name": m[1],
            "phone": m[2],
            "email": m[3],
            "gender": int(m[4]),
            "role": m[5],
            "join_date": m[6],
            "status": m[7],
        }
        users.append(user)
    return users

# =====================
# TESTS
# =====================
def test_unique_phone_email():
    users = parse_appuser(APPUSER_SQL_FILE)
    phones = [u["phone"] for u in users]
    emails = [u["email"] for u in users]
    assert len(phones) == len(set(phones)), "Duplicate phone detected!"
    assert len(emails) == len(set(emails)), "Duplicate email detected!"

def test_phone_format():
    users = parse_appuser(APPUSER_SQL_FILE)
    for u in users:
        assert re.match(r"^0\d{9}$", u["phone"]), f"Phone format invalid: {u['phone']}"

def test_gender_value():
    users = parse_appuser(APPUSER_SQL_FILE)
    for u in users:
        assert u["gender"] in [0, 1], f"Invalid gender: {u['gender']}"

def test_role_value():
    users = parse_appuser(APPUSER_SQL_FILE)
    for u in users:
        assert u["role"] in ROLE_RATIO.keys(), f"Invalid role: {u['role']}"

def test_status_value():
    users = parse_appuser(APPUSER_SQL_FILE)
    for u in users:
        assert u["status"] in STATUS_RATIO.keys(), f"Invalid status: {u['status']}"

def test_role_ratio():
    users = parse_appuser(APPUSER_SQL_FILE)
    counts = Counter(u["role"] for u in users)
    total = len(users)
    for role, expected_ratio in ROLE_RATIO.items():
        actual_ratio = counts[role] / total
        assert abs(actual_ratio - expected_ratio) <= TOLERANCE, f"Role {role} ratio out of tolerance"

def test_status_ratio():
    users = parse_appuser(APPUSER_SQL_FILE)
    counts = Counter(u["status"] for u in users)
    total = len(users)
    for status, expected_ratio in STATUS_RATIO.items():
        actual_ratio = counts[status] / total
        assert abs(actual_ratio - expected_ratio) <= TOLERANCE, f"Status {status} ratio out of tolerance"

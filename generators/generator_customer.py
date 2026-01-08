import random
import re
from pathlib import Path

# =====================
# CONFIG
# =====================
APPUSER_FILE = Path("../output/appuser.sql")  # input appuser.sql
OUTPUT_FILE = Path("../output/customer.sql")  # output customer.sql

# penalty_count ratio: 0,1,2,>=3
PENALTY_VALUES = [0, 1, 2, 3]
PENALTY_PROBS = [0.7, 0.2, 0.07, 0.03]

# =====================
# HELPER
# =====================
def parse_appuser(file_path):
    """Lấy danh sách user_id có role=customer"""
    users = []
    pattern = re.compile(
        r"\((\d+),\s*'[^']+',\s*'[^']+',\s*'[^']+',\s*\d+,\s*'customer',"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    matches = pattern.findall(content)
    for m in matches:
        users.append(int(m))
    return users

# =====================
# GENERATE CUSTOMER
# =====================
customer_ids = parse_appuser(APPUSER_FILE)
N = len(customer_ids)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)  # đảm bảo folder tồn tại

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("INSERT INTO customer (user_id, penalty_count)\nVALUES\n")
    for i, user_id in enumerate(customer_ids):
        penalty_count = random.choices(PENALTY_VALUES, weights=PENALTY_PROBS, k=1)[0]
        line = f"({user_id}, {penalty_count})"
        line += ",\n" if i < N - 1 else ";\n"
        f.write(line)

print(f"✅ Generated {OUTPUT_FILE} with {N} customer records")

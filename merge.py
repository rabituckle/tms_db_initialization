from pathlib import Path

# =====================
# CONFIG
# =====================
OUTPUT_DIR = Path(r"D:\HUST\Source code\Database\output")
MERGED_FILE = Path("data_tms.sql")
SQL_FILES = [
    "appuser.sql",
    "customer.sql",
    "driver.sql",
    "vehicle.sql",
    "trip_request.sql",
    "trip.sql",
    "payment.sql",
    "feedback.sql"
]

# =====================
# GỌP FILES
# =====================
with open(MERGED_FILE, "w", encoding="utf-8") as f_out:
    f_out.write("-- Auto-generated merged SQL\n")
    f_out.write("BEGIN;\n\n")  # start transaction

    for file_name in SQL_FILES:
        file_path = OUTPUT_DIR / file_name
        if file_path.exists():
            f_out.write(f"-- ======= {file_name} =======\n")
            with open(file_path, "r", encoding="utf-8") as f_in:
                f_out.write(f_in.read())
                if not f_in.read().endswith("\n"):
                    f_out.write("\n")
            f_out.write("\n")
        else:
            print(f"⚠️ File {file_path} not found, skipping.")

    f_out.write("COMMIT;\n")  # end transaction

print(f"✅ Merged SQL written to {MERGED_FILE}")

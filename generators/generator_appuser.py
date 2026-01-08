from faker import Faker # type: ignore
import random

# =====================
# CONFIG
# =====================
Faker.seed(2025)
fake = Faker("en_US")

N = 50000        # số bản ghi appuser
START_ID = 1

# Tỉ lệ role
roles = ["customer", "driver"]
role_probs = [0.8, 0.2]

# Tỉ lệ status
statuses = ["active", "inactive", "suspended"]
status_probs = [0.88, 0.10, 0.02]

phones = set()
emails = set()

# =====================
# FILE OUTPUT
# =====================
with open(r"output\appuser.sql", "w", encoding="utf-8") as f:
    f.write(
        "INSERT INTO appuser "
        "(user_id, name, phone, email, gender, role, join_date, status)\nVALUES\n"
    )

    for i in range(N):
        user_id = START_ID + i
        name = fake.name()

        # phone dạng 0 + 9 số
        phone = "0" + "".join([str(random.randint(0, 9)) for _ in range(9)])
        while phone in phones:
            phone = "0" + "".join([str(random.randint(0, 9)) for _ in range(9)])
        phones.add(phone)

        email = fake.email()
        while email in emails:
            email = fake.email()
        emails.add(email)

        gender = random.choice([0, 1])
        role = random.choices(roles, weights=role_probs, k=1)[0]
        join_date = fake.date_between(start_date="-5y", end_date="today")
        status = random.choices(statuses, weights=status_probs, k=1)[0]

        line = (
            f"({user_id}, "
            f"'{name}', "
            f"'{phone}', "
            f"'{email}', "
            f"{gender}, "
            f"'{role}', "
            f"'{join_date}', "
            f"'{status}')"
        )
        line += ",\n" if i < N - 1 else ";\n"
        f.write(line)

print("✅ Generated appuser.sql with 50,000 records")

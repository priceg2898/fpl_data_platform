from faker import Faker
import pandas as pd
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path


fake = Faker()


def generate_base_users(n=5):
    return [
        {
            "user_id": i,
            "name": fake.name(),
            "email": fake.email(),
            "country": fake.country(),
            "created_at": fake.date_between("-2y", "-1y"),
        }
        for i in range(1, n + 1)
    ]


def generate_products(n=5):
    return [
        {
            "product_id": i,
            "name": fake.word().title(),
            "category": fake.random_element(["electronics", "books", "clothing"]),
            "price": round(random.uniform(5, 500), 2),
        }
        for i in range(1, n + 1)
    ]


def generate_scd2_users(base_users, months=12, change_prob=0.9):
    records = []

    for user in base_users:
        current = user.copy()

        start_date = current["created_at"]
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)

        version_start = start_date

        for m in range(months):
            change_happened = random.random() < change_prob

            if change_happened:
                # close previous record
                version_end = version_start + timedelta(days=30)

                records.append(
                    {
                        **current,
                        "valid_from": version_start,
                        "valid_to": version_end,
                        "is_current": False,
                    }
                )

                # mutate user
                if random.random() < 0.1:
                    current["email"] = fake.email()
                if random.random() < 0.1:
                    current["name"] = fake.name()
                if random.random() < 0.1:
                    current["country"] = fake.country()

                version_start = version_end

        # final record
        records.append(
            {
                **current,
                "valid_from": version_start,
                "valid_to": None,
                "is_current": True,
            }
        )

    return records


def generate_transactions(users, products, min_transaction_id=0, n=5):
    transactions = []
    for tran_id in range(min_transaction_id + 1, min_transaction_id + n + 1):
        user = random.choice(users)
        date = fake.date_time_between(start_date="-5d", end_date="now")
        for line_id in range(1, random.randint(1, 20)):
            product = random.choice(products)
            qty = random.randint(1, 100)
            transactions.append(
                {
                    "tran_id": tran_id,
                    "tran_line_id": line_id,
                    "user_id": user["user_id"],
                    "tran_date": date,
                    "prod_id": product["product_id"],
                    "qty": qty,
                    "val": round(qty * product["price"], 2),
                }
            )
    return transactions


base_products = generate_products(20)
base_users = generate_base_users(50)
# scd2_users = generate_scd2_users(base_users)

# pd.DataFrame(base_products).to_parquet("../../../data/products.parquet", index=False)

# print(base_users)
# print(generate_products())
trans = generate_transactions(base_users, base_products)

now = datetime.now(ZoneInfo("Europe/London"))
curr_date = now.strftime("%Y-%m-%d")
timestamp = now.strftime("%Y%m%d_%H%M%S")

base_path = Path(f"../../../data/bronze/dummy_data/products/date={curr_date}/")

base_path.mkdir(parents=True, exist_ok=True)


pd.DataFrame(trans).to_parquet(f"{base_path}transactions.parquet", index=False)

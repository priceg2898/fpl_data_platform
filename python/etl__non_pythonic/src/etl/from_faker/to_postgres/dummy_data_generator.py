import time
import random
from faker import Faker
import psycopg2
from datetime import datetime
from zoneinfo import ZoneInfo

fake = Faker()

# --- Weighted attributes ---
categories = ["Electronics", "Clothing", "Home", "Toys", "Books"]
category_weights = [40, 25, 20, 10, 5]
brands = {
    "Electronics": ["Sony", "Apple", "Samsung", "LG"],
    "Clothing": ["Nike", "Adidas", "Uniqlo", "H&M"],
    "Home": ["Ikea", "HomeDepot", "Wayfair"],
    "Toys": ["Lego", "Mattel", "Hasbro"],
    "Books": ["Penguin", "HarperCollins", "Random House"],
}
price_ranges = {
    "Electronics": (100, 2000),
    "Clothing": (10, 200),
    "Home": (20, 1000),
    "Toys": (5, 150),
    "Books": (5, 50),
}

countries = ["USA", "UK", "Canada", "Germany", "Australia"]
country_weights = [50, 15, 15, 10, 10]
account_types = ["Basic", "Premium", "VIP"]
account_weights = [60, 30, 10]

# --- PostgreSQL connection ---
conn = psycopg2.connect(
    host="postgres1", database="postgres", user="greg", password="greg1"
)
cur = conn.cursor()


# --- Product generator ---
def generate_product():
    category = random.choices(categories, weights=category_weights, k=1)[0]
    brand = random.choice(brands[category])
    name = f"{brand} {fake.word().capitalize()}"
    price = round(random.uniform(*price_ranges[category]), 2)
    sku = fake.unique.bothify(text="??-#####")
    return name, category, brand, price, sku


# --- User generator ---
def generate_user():
    name = fake.name()
    email = fake.unique.email()
    age = random.randint(18, 70)
    country = random.choices(countries, weights=country_weights, k=1)[0]
    account_type = random.choices(account_types, weights=account_weights, k=1)[0]
    return name, email, age, country, account_type


# --- Update product ---
def update_product(max_id):
    update_id = random.randint(1, max_id)
    options = ["price", "category", "brand", "sku"]
    weights = [50, 20, 20, 10]
    field = random.choices(options, weights=weights, k=1)[0]

    if field == "price":
        new_price = round(random.uniform(5, 2000), 2)
        cur.execute(
            "UPDATE products SET price=%s, updated_at=%s WHERE id=%s",
            (new_price, datetime.now(ZoneInfo("Europe/London")), update_id),
        )
        print(f"Updated product {update_id} price: {new_price}")
    elif field == "category":
        new_category = random.choices(categories, weights=category_weights, k=1)[0]
        new_brand = random.choice(brands[new_category])
        cur.execute(
            "UPDATE products SET category=%s, brand=%s, updated_at=%s WHERE id=%s",
            (
                new_category,
                new_brand,
                datetime.now(ZoneInfo("Europe/London")),
                update_id,
            ),
        )
        print(
            f"Updated product {update_id} category: {new_category}, brand: {new_brand}"
        )
    elif field == "brand":
        cur.execute("SELECT category FROM products WHERE id=%s", (update_id,))
        category = cur.fetchone()[0]
        new_brand = random.choice(brands[category])
        cur.execute(
            "UPDATE products SET brand=%s, updated_at=%s WHERE id=%s",
            (new_brand, datetime.now(ZoneInfo("Europe/London")), update_id),
        )
        print(f"Updated product {update_id} brand: {new_brand}")
    elif field == "sku":
        new_sku = fake.unique.bothify(text="??-#####")
        cur.execute(
            "UPDATE products SET sku=%s, updated_at=%s WHERE id=%s",
            (new_sku, datetime.now(ZoneInfo("Europe/London")), update_id),
        )
        print(f"Updated product {update_id} sku: {new_sku}")


# --- Update user ---
def update_user(max_id):
    update_id = random.randint(1, max_id)
    options = ["age", "country", "account_type"]
    weights = [50, 30, 20]
    field = random.choices(options, weights=weights, k=1)[0]

    if field == "age":
        new_age = random.randint(18, 70)
        cur.execute(
            "UPDATE users SET age=%s, updated_at=%s WHERE id=%s",
            (new_age, datetime.now(ZoneInfo("Europe/London")), update_id),
        )
        print(f"Updated user {update_id} age: {new_age}")
    elif field == "country":
        new_country = random.choices(countries, weights=country_weights, k=1)[0]
        cur.execute(
            "UPDATE users SET country=%s, updated_at=%s WHERE id=%s",
            (new_country, datetime.now(ZoneInfo("Europe/London")), update_id),
        )
        print(f"Updated user {update_id} country: {new_country}")
    elif field == "account_type":
        new_type = random.choices(account_types, weights=account_weights, k=1)[0]
        cur.execute(
            "UPDATE users SET account_type=%s, updated_at=%s WHERE id=%s",
            (new_type, datetime.now(ZoneInfo("Europe/London")), update_id),
        )
        print(f"Updated user {update_id} account_type: {new_type}")


# --- Main loop ---
try:
    while True:
        # --- Max IDs ---
        cur.execute("SELECT MAX(id) FROM products")
        max_product_id = cur.fetchone()[0] or 0

        cur.execute("SELECT MAX(id) FROM users")
        max_user_id = cur.fetchone()[0] or 0

        # --- Insert new products ---
        for _ in range(5):
            name, category, brand, price, sku = generate_product()
            cur.execute(
                "INSERT INTO products (name, category, brand, price, sku, updated_at) VALUES (%s,%s,%s,%s,%s,%s)",
                (
                    name,
                    category,
                    brand,
                    price,
                    sku,
                    datetime.now(ZoneInfo("Europe/London")),
                ),
            )

        # --- Insert new users ---
        for _ in range(5):
            name, email, age, country, account_type = generate_user()
            cur.execute(
                "INSERT INTO users (name,email,age,country,account_type, updated_at) VALUES (%s,%s,%s,%s,%s,%s)",
                (
                    name,
                    email,
                    age,
                    country,
                    account_type,
                    datetime.now(ZoneInfo("Europe/London")),
                ),
            )

        conn.commit()
        print("Inserted 5 products and 5 users.")

        # --- Update 1 old product & user ---
        if max_product_id > 0:
            update_product(max_product_id)
        if max_user_id > 0:
            update_user(max_user_id)
        conn.commit()

        # --- Wait 10 seconds ---
        time.sleep(10)

except KeyboardInterrupt:
    print("Stopping loop...")

finally:
    cur.close()
    conn.close()

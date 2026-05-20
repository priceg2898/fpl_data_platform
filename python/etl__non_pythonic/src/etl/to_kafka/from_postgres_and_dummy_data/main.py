import psycopg2
from kafka import KafkaProducer
import json
import random
import time
from datetime import datetime
import argparse

# --- Command line argument for Kafka send interval ---
parser = argparse.ArgumentParser(description="Kafka event simulator")
parser.add_argument(
    "--interval",
    type=float,
    default=0.0,
    help="Seconds between sending Kafka events (0 = as fast as possible)",
)
args = parser.parse_args()
kafka_interval = args.interval

# --- PostgreSQL connection ---
conn = psycopg2.connect(
    host="localhost", database="postgres", user="greg", password="greg1"
)
cur = conn.cursor()

# --- Kafka Producer ---
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# --- Constants ---
ACTIVE_WINDOW = 50
USER_EVENTS = ["page_view", "login", "add_to_cart", "wishlist"]
PRODUCT_EVENTS = ["stock_received", "inventory_adjustment", "price_change"]
DB_POLL_INTERVAL = 60  # seconds

# --- In-memory caches ---
active_users = []
active_products = []
last_db_poll = 0


# --- Fetch active users ---
def fetch_active_users():
    cur.execute(
        "SELECT id, name, email, age, country, account_type FROM users ORDER BY id DESC LIMIT %s",
        (ACTIVE_WINDOW,),
    )
    rows = cur.fetchall()
    users = []
    for r in rows:
        users.append(
            {
                "user_id": r[0],
                "name": r[1],
                "email": r[2],
                "age": r[3],
                "country": r[4],
                "account_type": r[5],
            }
        )
    return users


# --- Fetch active products ---
def fetch_active_products():
    cur.execute(
        "SELECT id, name, category, brand, price, sku FROM products ORDER BY id DESC LIMIT %s",
        (ACTIVE_WINDOW,),
    )
    rows = cur.fetchall()
    products = []
    for r in rows:
        products.append(
            {
                "product_id": r[0],
                "name": r[1],
                "category": r[2],
                "brand": r[3],
                "price": float(r[4]),
                "sku": r[5],
            }
        )
    return products


# --- Event generators ---
def generate_user_event(user):
    event_type = random.choices(USER_EVENTS, weights=[50, 20, 20, 10], k=1)[0]
    return {
        "user_id": user["user_id"],
        "event_type": event_type,
        "page": f"/products/{random.randint(1, 100)}"
        if event_type == "page_view"
        else None,
        "timestamp": datetime.utcnow().isoformat(),
    }


def generate_product_event(product):
    event_type = random.choices(PRODUCT_EVENTS, weights=[50, 30, 20], k=1)[0]
    return {
        "product_id": product["product_id"],
        "sku": product["sku"],
        "event_type": event_type,
        "quantity": random.randint(10, 100) if event_type == "stock_received" else None,
        "timestamp": datetime.utcnow().isoformat(),
    }


def generate_purchase_event(users, products):
    user = random.choice(users)
    product = random.choice(products)
    return {
        "user_id": user["user_id"],
        "product_id": product["product_id"],
        "quantity": random.randint(1, 3),
        "price": product["price"],
        "timestamp": datetime.utcnow().isoformat(),
    }


# --- Main loop ---
try:
    while True:
        now = time.time()
        # --- Poll DB every minute ---
        if (
            now - last_db_poll > DB_POLL_INTERVAL
            or not active_users
            or not active_products
        ):
            active_users = fetch_active_users()
            active_products = fetch_active_products()
            last_db_poll = now
            print(
                f"Polled DB: {len(active_users)} users, {len(active_products)} products"
            )

        # --- Produce events ---
        if active_users and active_products:
            # User events
            user = random.choice(active_users)
            producer.send("user-events", generate_user_event(user))

            # Product events
            product = random.choice(active_products)
            producer.send("product-events", generate_product_event(product))

            # Purchase events
            producer.send(
                "purchase-events",
                generate_purchase_event(active_users, active_products),
            )

            producer.flush()

        if kafka_interval > 0:
            time.sleep(kafka_interval)

except KeyboardInterrupt:
    print("Stopping Kafka producer...")

finally:
    cur.close()
    conn.close()
    producer.close()

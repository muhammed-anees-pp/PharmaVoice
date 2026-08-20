import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = "pharmacy.db"
DEFAULT_INVENTORY_PATH = "pharmacy_inventory.json"


"""
GET DATABASE PATH
"""
def get_database_path():
    return os.getenv(
        "PHARMACY_DB_PATH",
        str(BASE_DIR / DEFAULT_DB_PATH),
    )


"""
GET INVENTORY PATH
"""
def get_inventory_path():
    return os.getenv(
        "PHARMACY_DATA_PATH",
        str(BASE_DIR / DEFAULT_INVENTORY_PATH),
    )


"""
LOAD INVENTORY DATA
"""
def load_inventory_data():
    inventory_path = get_inventory_path()

    if not os.path.exists(inventory_path):
        raise FileNotFoundError(
            f"Pharmacy inventory file not found: {inventory_path}"
        )

    with open(inventory_path, "r", encoding="utf-8") as inventory_file:
        data = json.load(inventory_file)

    drugs = data.get("drugs")

    if not isinstance(drugs, list):
        raise ValueError("Pharmacy inventory JSON must contain a drugs list")

    return drugs


"""
GET CURRENT UTC TIMESTAMP
"""
def utc_now():
    return datetime.now(timezone.utc).isoformat()


"""
OPEN DATABASE CONNECTION
"""
@contextmanager
def connect(db_path=None):
    connection = sqlite3.connect(db_path or get_database_path())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


"""
INITIALIZE DATABASE
"""
def initialize_database(db_path=None):
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS drugs (
                slug TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'INR',
                package_quantity INTEGER NOT NULL,
                stock INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                drug_slug TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total REAL NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (drug_slug) REFERENCES drugs(slug)
            );

            CREATE TABLE IF NOT EXISTS order_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            );
            """
        )
        seed_drugs(connection)


"""
SEED DRUG INVENTORY
"""
def seed_drugs(connection):
    now = utc_now()

    for drug in load_inventory_data():
        slug = drug["slug"].lower()

        connection.execute(
            """
            INSERT INTO drugs (
                slug,
                name,
                description,
                price,
                currency,
                package_quantity,
                stock,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                price = excluded.price,
                currency = excluded.currency,
                package_quantity = excluded.package_quantity,
                updated_at = excluded.updated_at
            """,
            (
                slug,
                drug["name"],
                drug["description"],
                drug["price"],
                drug.get("currency", "INR"),
                drug["quantity"],
                drug["stock"],
                now,
                now,
            ),
        )


"""
GET DRUG BY SLUG
"""
def get_drug(slug):
    initialize_database()

    with connect() as connection:
        return connection.execute(
            "SELECT * FROM drugs WHERE slug = ?",
            (slug.lower(),),
        ).fetchone()


"""
GET OR CREATE CUSTOMER
"""
def get_or_create_customer(connection, customer_name):
    normalized_name = customer_name.strip()
    now = utc_now()

    connection.execute(
        """
        INSERT INTO customers (name, created_at, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET updated_at = excluded.updated_at
        """,
        (normalized_name, now, now),
    )

    return connection.execute(
        "SELECT * FROM customers WHERE name = ?",
        (normalized_name,),
    ).fetchone()


"""
CREATE PHARMACY ORDER
"""
def create_order(customer_name, drug_slug):
    initialize_database()

    with connect() as connection:
        drug = connection.execute(
            "SELECT * FROM drugs WHERE slug = ?",
            (drug_slug.lower(),),
        ).fetchone()

        if not drug:
            return None

        customer = get_or_create_customer(connection, customer_name)
        now = utc_now()
        status = "pending"

        cursor = connection.execute(
            """
            INSERT INTO orders (
                customer_id,
                drug_slug,
                quantity,
                total,
                currency,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer["id"],
                drug["slug"],
                drug["package_quantity"],
                drug["price"],
                drug["currency"],
                status,
                now,
                now,
            ),
        )
        order_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO order_status_history (
                order_id,
                status,
                note,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                order_id,
                status,
                "Order created",
                now,
            ),
        )

        return get_order_by_id(connection, order_id)


"""
GET ORDER
"""
def get_order(order_id):
    initialize_database()

    with connect() as connection:
        return get_order_by_id(connection, int(order_id))


"""
GET ORDER STATUS HISTORY
"""
def get_order_history(order_id):
    initialize_database()

    with connect() as connection:
        return connection.execute(
            """
            SELECT status, note, created_at
            FROM order_status_history
            WHERE order_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (int(order_id),),
        ).fetchall()


"""
GET ORDER BY ID
"""
def get_order_by_id(connection, order_id):
    return connection.execute(
        """
        SELECT
            orders.id AS order_id,
            customers.name AS customer,
            drugs.name AS drug,
            orders.quantity AS quantity,
            orders.total AS total,
            orders.currency AS currency,
            orders.status AS status,
            orders.created_at AS created_at,
            orders.updated_at AS updated_at
        FROM orders
        JOIN customers ON customers.id = orders.customer_id
        JOIN drugs ON drugs.slug = orders.drug_slug
        WHERE orders.id = ?
        """,
        (order_id,),
    ).fetchone()

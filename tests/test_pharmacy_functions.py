import os
import sqlite3
import tempfile
import unittest

from pharmacy_functions import get_drug_info
from pharmacy_functions import lookup_order
from pharmacy_functions import place_order


class PharmacyFunctionTests(unittest.TestCase):
    def setUp(self):
        self.database = tempfile.NamedTemporaryFile(delete=False)
        self.database.close()
        os.environ["PHARMACY_DB_PATH"] = self.database.name

    def tearDown(self):
        os.environ.pop("PHARMACY_DB_PATH", None)
        os.unlink(self.database.name)

    def test_get_drug_info_returns_seeded_inventory(self):
        result = get_drug_info("aspirin")

        self.assertEqual(result["name"], "Acetylsalicylic Acid")
        self.assertEqual(result["currency"], "INR")
        self.assertEqual(result["quantity"], 30)
        self.assertEqual(result["available_stock"], 100)

    def test_place_order_persists_customer_order_and_history(self):
        order = place_order("Ada Lovelace", "metformin")

        self.assertEqual(order["order_id"], 1)
        self.assertEqual(order["status"], "pending")

        lookup = lookup_order(order["order_id"])

        self.assertEqual(lookup["customer"], "Ada Lovelace")
        self.assertEqual(lookup["drug"], "Metformin Hydrochloride")
        self.assertEqual(lookup["quantity"], 60)
        self.assertEqual(lookup["status_history"][0]["status"], "pending")

        with sqlite3.connect(self.database.name) as connection:
            customer_count = connection.execute(
                "SELECT COUNT(*) FROM customers"
            ).fetchone()[0]
            history_count = connection.execute(
                "SELECT COUNT(*) FROM order_status_history"
            ).fetchone()[0]

        self.assertEqual(customer_count, 1)
        self.assertEqual(history_count, 1)

    def test_lookup_order_handles_missing_and_invalid_ids(self):
        self.assertEqual(
            lookup_order(999),
            {"error": "Order 999 not found"},
        )
        self.assertEqual(
            lookup_order("invalid"),
            {"error": "Invalid order ID: invalid"},
        )


if __name__ == "__main__":
    unittest.main()


from __future__ import annotations
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import pandas as pd
from faker import Faker

from .db import PostgresClient

fake = Faker()

ORDER_STATUSES = ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
PAYMENT_METHODS = ["CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "BANK_TRANSFER", "GIFT_CARD"]
SHIPPING_STATUSES = ["PREPARING", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "FAILED"]

class ShopStreamGenerator:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self._customer_ids: list[int] = []
        self._product_ids: list[int] = []
        self._order_ids: list[int] = []

    def _execute(self, sql: str, params: Any | None = None) -> None:
        with PostgresClient() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)

    def _fetchall(self, sql: str, params: Any | None = None) -> list[dict[str, Any]]:
        with PostgresClient() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def load_reference_ids(self) -> None:
        self._customer_ids = [row["customer_id"] for row in self._fetchall("SELECT customer_id FROM customers")]
        self._product_ids = [row["product_id"] for row in self._fetchall("SELECT product_id FROM products")]
        self._order_ids = [row["order_id"] for row in self._fetchall("SELECT order_id FROM orders")]

    def generate_customers(self, count: int = 100) -> None:
        insert_sql = """
            INSERT INTO customers (first_name, last_name, email, phone, city, state, country, postal_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """
        for _ in range(count):
            values = (
                fake.first_name(),
                fake.last_name(),
                fake.unique.email(),
                fake.phone_number(),
                fake.city(),
                fake.state(),
                fake.country(),
                fake.postcode(),
            )
            self._execute(insert_sql, values)

    def generate_products(self, count: int = 100) -> None:
        insert_sql = """
            INSERT INTO products (sku, name, description, category_id, supplier_id, price, cost_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (sku) DO NOTHING
        """
        for _ in range(count):
            category_id = random.randint(1, 9)
            supplier_id = random.randint(1, 3)
            price = Decimal(fake.pydecimal(left_digits=4, right_digits=2, positive=True))
            cost_price = Decimal(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
            values = (
                fake.unique.bothify(text="SKU-????-####"),
                fake.catch_phrase(),
                fake.text(max_nb_chars=180),
                category_id,
                supplier_id,
                price,
                cost_price,
            )
            self._execute(insert_sql, values)

    def generate_orders(self, count: int = 100) -> None:
        if not self._customer_ids or not self._product_ids:
            self.load_reference_ids()

        order_insert = """
            INSERT INTO orders (customer_id, total_amount, discount_amount, tax_amount, shipping_address)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING order_id
        """

        item_insert = """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
            VALUES (%s, %s, %s, %s, %s)
        """

        payment_insert = """
            INSERT INTO payments (order_id, payment_method, payment_status, transaction_reference, amount)
            VALUES (%s, %s, %s, %s, %s)
        """

        shipping_insert = """
            INSERT INTO shipping (order_id, carrier, tracking_number, shipping_status, estimated_delivery, shipped_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        for _ in range(count):
            customer_id = random.choice(self._customer_ids)
            line_items = []
            total_amount = Decimal("0.00")
            product_count = random.randint(1, 5)

            for _ in range(product_count):
                product_id = random.choice(self._product_ids)
                quantity = random.randint(1, 4)
                unit_price = Decimal(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
                total_price = quantity * unit_price
                total_amount += total_price
                line_items.append((product_id, quantity, unit_price, total_price))

            discount_amount = Decimal(random.choice([0, 5, 10, 15]))
            tax_amount = (total_amount - discount_amount) * Decimal("0.08")
            shipping_address = fake.address().replace("\n", ", ")

            with PostgresClient() as conn:
                with conn.cursor() as cur:
                    cur.execute(order_insert, (customer_id, total_amount, discount_amount, tax_amount, shipping_address))
                    order_id = cur.fetchone()["order_id"]

                    for product_id, quantity, unit_price, total_price in line_items:
                        cur.execute(item_insert, (order_id, product_id, quantity, unit_price, total_price))

                    cur.execute(
                        payment_insert,
                        (
                            order_id,
                            random.choice(PAYMENT_METHODS),
                            random.choice(["COMPLETED", "PENDING"]),
                            fake.unique.bothify(text="TXN-########"),
                            total_amount,
                        ),
                    )

                    shipped_at = datetime.now() - timedelta(days=random.randint(0, 3))
                    estimated_delivery = shipped_at + timedelta(days=random.randint(2, 7))
                    cur.execute(
                        shipping_insert,
                        (
                            order_id,
                            fake.company(),
                            fake.unique.bothify(text="TRK-########"),
                            random.choice(SHIPPING_STATUSES),
                            estimated_delivery,
                            shipped_at,
                        ),
                    )

                    if random.random() < 0.15:
                        cur.execute("UPDATE orders SET order_status = %s WHERE order_id = %s", ("CANCELLED", order_id))
                    else:
                        cur.execute("UPDATE orders SET order_status = %s WHERE order_id = %s", (random.choice(ORDER_STATUSES), order_id))

    def generate_reviews(self, count: int = 100) -> None:
        if not self._customer_ids or not self._product_ids:
            self.load_reference_ids()

        insert_review = """
            INSERT INTO reviews (product_id, customer_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
        """

        for _ in range(count):
            self._execute(
                insert_review,
                (
                    random.choice(self._product_ids),
                    random.choice(self._customer_ids),
                    random.randint(1, 5),
                    fake.sentence(nb_words=20),
                ),
            )

    def generate_inventory_updates(self) -> None:
        if not self._product_ids:
            self.load_reference_ids()

        insert_inventory = """
            INSERT INTO inventory (product_id, quantity, reserved_quantity, reorder_level)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_id) DO UPDATE
            SET quantity = EXCLUDED.quantity,
                reserved_quantity = EXCLUDED.reserved_quantity,
                reorder_level = EXCLUDED.reorder_level,
                updated_at = CURRENT_TIMESTAMP
        """

        for product_id in random.sample(self._product_ids, min(len(self._product_ids), 30)):
            self._execute(
                insert_inventory,
                (
                    product_id,
                    random.randint(0, 500),
                    random.randint(0, 100),
                    random.randint(5, 50),
                ),
            )

    def generate_late_arriving_orders(self, count: int = 10) -> None:
        if not self._customer_ids or not self._product_ids:
            self.load_reference_ids()

        late_insert = """
            INSERT INTO orders (customer_id, total_amount, discount_amount, tax_amount, shipping_address, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING order_id
        """

        for _ in range(count):
            customer_id = random.choice(self._customer_ids)
            total_amount = Decimal(fake.pydecimal(left_digits=4, right_digits=2, positive=True))
            discount_amount = Decimal(random.choice([0, 5, 10]))
            tax_amount = (total_amount - discount_amount) * Decimal("0.08")
            created_at = datetime.now() - timedelta(days=random.randint(10, 30))
            updated_at = created_at + timedelta(hours=random.randint(1, 72))
            shipping_address = fake.address().replace("\n", ", ")

            with PostgresClient() as conn:
                with conn.cursor() as cur:
                    cur.execute(late_insert, (customer_id, total_amount, discount_amount, tax_amount, shipping_address, created_at, updated_at))
                    order_id = cur.fetchone()["order_id"]
                    product_id = random.choice(self._product_ids)
                    quantity = random.randint(1, 3)
                    unit_price = Decimal(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
                    total_price = quantity * unit_price
                    cur.execute(
                        "INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price) VALUES (%s, %s, %s, %s, %s)",
                        (order_id, product_id, quantity, unit_price, total_price),
                    )

    def run_seed(self) -> None:
        self.generate_customers(200)
        self.generate_products(150)
        self.load_reference_ids()
        self.generate_orders(120)
        self.generate_reviews(80)
        self.generate_inventory_updates()
        self.generate_late_arriving_orders(25)

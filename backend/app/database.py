import os
import sqlite3

from contextlib import contextmanager


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(
        BASE_DIR,
        "..",
        "orders.db"
    )
)


DB_PATH = os.path.abspath(DB_PATH)


@contextmanager
def get_db():

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = sqlite3.Row

    try:
        yield connection

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def init_db():

    with get_db() as db:

        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL UNIQUE,
                name TEXT,
                address TEXT
            );


            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                tracking_number TEXT,
                shipping_fee INTEGER,

                FOREIGN KEY(customer_id)
                    REFERENCES customers(id)
            );


            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,

                FOREIGN KEY(order_id)
                    REFERENCES orders(id)
            );


            CREATE TABLE IF NOT EXISTS import_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                orders_file TEXT,
                shipping_file TEXT,

                total_order_rows INTEGER DEFAULT 0,
                matched_rows INTEGER DEFAULT 0,
                unmatched_rows INTEGER DEFAULT 0,
                invalid_phone_rows INTEGER DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            """
        )


        # Tạo admin mặc định lần đầu.
        from .services.auth_s import hash_password

        admin_username = os.getenv(
            "ADMIN_USERNAME",
            "admin"
        )

        admin_password = os.getenv(
            "ADMIN_PASSWORD",
            "ChangeMe123!"
        )


        existing = db.execute(
            """
            SELECT id
            FROM admin_users
            WHERE username = ?
            """,
            (admin_username,)
        ).fetchone()


        if not existing:

            db.execute(
                """
                INSERT INTO admin_users (
                    username,
                    password_hash
                )
                VALUES (?, ?)
                """,
                (
                    admin_username,
                    hash_password(admin_password)
                )
            )
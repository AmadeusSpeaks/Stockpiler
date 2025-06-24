import sqlite3
import os

DB_PATH = "db/stockpile.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount INTEGER NOT NULL,
                purchased TEXT NOT NULL,
                expires TEXT NOT NULL
            )
        ''')
        conn.commit()

def add_product(name, amount, purchased, expires):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO products (name, amount, purchased, expires) VALUES (?, ?, ?, ?)",
            (name, amount, purchased, expires)
        )
        conn.commit()

def get_products():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM products ORDER BY name ASC")
        return c.fetchall()

def update_product(product_id, name, amount, purchased, expires):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE products SET name = ?, amount = ?, purchased = ?, expires = ? WHERE id = ?",
            (name, amount, purchased, expires, product_id)
        )
        conn.commit()

def delete_product(product_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()

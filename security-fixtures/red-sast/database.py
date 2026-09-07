"""Intentionally vulnerable fixture used only for the red SAST demo."""

import sqlite3


def get_user_data(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Intentionally vulnerable: SQL query is built by concatenation.
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)

    return cursor.fetchall()


def search_products(keyword):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Intentionally vulnerable: SQL query is built with an f-string.
    query = f"SELECT * FROM products WHERE name LIKE '%{keyword}%'"
    cursor.execute(query)

    return cursor.fetchall()

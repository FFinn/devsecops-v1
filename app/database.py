"""Small safe example used by the green SAST scenario."""

import sqlite3


def get_user_data(user_id: int) -> list[tuple]:
    """Return one user by id using a parameterized SQL query."""
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchall()


def search_products(keyword: str) -> list[tuple]:
    """Search products using a parameterized LIKE query."""
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE name LIKE ?",
            (f"%{keyword}%",),
        )
        return cursor.fetchall()

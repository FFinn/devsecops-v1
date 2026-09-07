"""Небольшой безопасный пример для успешного SAST-прогона."""

import sqlite3


def get_user_data(user_id: int) -> list[tuple]:
    """Возвращает пользователя по идентификатору с параметризованным SQL-запросом."""
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchall()


def search_products(keyword: str) -> list[tuple]:
    """Ищет товары по названию с помощью параметризованного LIKE-запроса."""
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE name LIKE ?",
            (f"%{keyword}%",),
        )
        return cursor.fetchall()

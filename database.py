"""
Модуль для взаимодействия с БД
"""

import sqlite3


class Database:
    """
    Класс для взаимодействия с БД
    """

    def __init__(self, db_name="wb_founder.db") -> None:
        """
        Инициализация класса

        :param db_name: путь до БД
        """
        self.db_name = db_name
        self.init_db()

    def init_db(self) -> None:
        """
        Инициализация БД
        :return:
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    def add_user(self, user_id: int, username: str, full_name: str) -> None:
        """
        Добавление пользователя в БД

        :param user_id: id пользователя
        :param username: ник пользователя
        :param full_name: полное имя пользователя
        :return:
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
            """,
                (user_id, username, full_name),
            )
            conn.commit()

# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

class DatabaseManager:
    """
    Класс для управления всеми операциями с базой данных SQLite.
    """
    def __init__(self, db_name="work_time.db"):
        """
        Инициализирует менеджер и создает таблицу, если она не существует.
        """
        self.db_name = db_name
        self._init_db()

    def _get_connection(self):
        """Возвращает соединение с базой данных."""
        conn = sqlite3.connect(self.db_name)
        # Этот курсор будет возвращать строки в виде словарей, что удобнее
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Создает основную таблицу для хранения записей о рабочем времени."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                comment TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_entry(self, start_time_str, end_time_str, comment=""):
        """
        Добавляет новую запись о рабочем времени в базу данных.
        Время должно быть в формате ISO (YYYY-MM-DD HH:MM:SS).
        """
        start_dt = datetime.fromisoformat(start_time_str)
        end_dt = datetime.fromisoformat(end_time_str)
        duration = int((end_dt - start_dt).total_seconds() / 60)

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO work_entries (start_time, end_time, duration_minutes, comment) VALUES (?, ?, ?, ?)",
            (start_time_str, end_time_str, duration, comment)
        )
        conn.commit()
        conn.close()

    def add_or_update_entry(self, start_time_str, end_time_str, comment=""):
        """
        Добавляет новую или обновляет существующую запись для указанной даты.
        Проверка осуществляется по дате из start_time.
        """
        start_dt = datetime.fromisoformat(start_time_str)
        end_dt = datetime.fromisoformat(end_time_str)
        duration = int((end_dt - start_dt).total_seconds() / 60)
        entry_date = start_dt.date().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Проверяем, есть ли запись для этой даты
        cursor.execute("SELECT id FROM work_entries WHERE date(start_time) = ?", (entry_date,))
        existing_entry = cursor.fetchone()

        if existing_entry:
            # 2. Если есть - обновляем её
            entry_id = existing_entry['id']
            cursor.execute(
                """
                UPDATE work_entries 
                SET start_time = ?, end_time = ?, duration_minutes = ?, comment = ?
                WHERE id = ?
                """,
                (start_time_str, end_time_str, duration, comment, entry_id)
            )
        else:
            # 3. Если нет - добавляем новую
            cursor.execute(
                "INSERT INTO work_entries (start_time, end_time, duration_minutes, comment) VALUES (?, ?, ?, ?)",
                (start_time_str, end_time_str, duration, comment)
            )
        conn.commit()
        conn.close()

    def get_all_entries(self):
        """Возвращает все записи из базы данных, отсортированные по дате."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM work_entries ORDER BY start_time DESC")
        entries = cursor.fetchall()
        conn.close()
        return entries
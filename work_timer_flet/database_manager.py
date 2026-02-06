# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

class DatabaseManager:
    """
    Класс для управления всеми операциями с базой данных SQLite.
    """
    def __init__(self, db_name="work_time_flet.db"):
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
                comment TEXT
            )
        """)

        # --- Миграция: Проверяем и удаляем старый столбец duration_minutes ---
        cursor.execute("PRAGMA table_info(work_entries)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'duration_minutes' in columns:
            print("Обнаружена старая схема БД. Выполняется миграция...")
            # 1. Переименовываем старую таблицу
            cursor.execute("ALTER TABLE work_entries RENAME TO _work_entries_old")
            # 2. Создаем новую таблицу с правильной структурой
            cursor.execute("""
                CREATE TABLE work_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    comment TEXT
                )
            """)
            # 3. Копируем данные из старой таблицы в новую (без duration_minutes)
            cursor.execute("INSERT INTO work_entries (id, start_time, end_time, comment) SELECT id, start_time, end_time, comment FROM _work_entries_old")
            # 4. Удаляем старую таблицу
            cursor.execute("DROP TABLE _work_entries_old")
            print("Миграция успешно завершена.")

        # Создаем таблицу для настроек по месяцам
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_settings (
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                hourly_rate REAL DEFAULT 0.0,
                advance REAL DEFAULT 0.0,
                PRIMARY KEY (year, month)
            )
        """)
        # Создаем таблицу для глобальных настроек
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_or_update_entry(self, start_time_str, end_time_str, comment=""):
        """
        Добавляет новую или обновляет существующую запись для указанной даты.
        Проверка осуществляется по дате из start_time.
        """
        start_dt = datetime.fromisoformat(start_time_str)
        end_dt = datetime.fromisoformat(end_time_str)
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
                SET start_time = ?, end_time = ?, comment = ?
                WHERE id = ?
                """,
                (start_time_str, end_time_str, comment, entry_id)
            )
        else:
            # 3. Если нет - добавляем новую
            cursor.execute(
                "INSERT INTO work_entries (start_time, end_time, comment) VALUES (?, ?, ?)",
                (start_time_str, end_time_str, comment)
            )
        conn.commit()
        conn.close()

    def get_entry_by_date(self, entry_date):
        """
        Возвращает запись за указанную дату.
        :param entry_date: дата в виде объекта datetime.date
        :return: словарь с данными записи или None, если запись не найдена.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        # Используем функцию date() из SQLite для сравнения только дат
        cursor.execute("SELECT * FROM work_entries WHERE date(start_time) = ?", (entry_date.isoformat(),))
        entry = cursor.fetchone()
        conn.close()
        return entry

    def delete_entry_by_date(self, entry_date):
        """
        Удаляет запись за указанную дату.
        :param entry_date: дата в виде объекта datetime.date
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM work_entries WHERE date(start_time) = ?", (entry_date.isoformat(),))
        conn.commit()
        conn.close()

    def get_all_entries(self):
        """Возвращает все записи из базы данных, отсортированные по дате."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM work_entries ORDER BY start_time ASC")
        entries = cursor.fetchall()
        conn.close()
        return entries

    def get_entries_for_month(self, year, month):
        """Возвращает все записи за указанный месяц и год, отсортированные по дате."""
        conn = self._get_connection()
        cursor = conn.cursor()
        # Используем strftime для извлечения года и месяца из текстового поля даты
        cursor.execute(
            "SELECT * FROM work_entries WHERE strftime('%Y', start_time) = ? AND strftime('%m', start_time) = ? ORDER BY start_time ASC",
            (str(year), f"{month:02d}")
        )
        entries = cursor.fetchall()
        conn.close()
        return entries

    def get_settings_for_month(self, year, month):
        """
        Возвращает часовую ставку и аванс для указанного месяца. 
        Ставка наследуется с предыдущих месяцев, аванс - нет.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Получаем аванс ТОЛЬКО для этого месяца. Если его нет, аванс равен 0.
        cursor.execute("SELECT advance FROM monthly_settings WHERE year = ? AND month = ?", (year, month))
        advance_row = cursor.fetchone()
        advance = advance_row['advance'] if advance_row else 0.0

        # 2. Получаем последнюю установленную ставку до или в этом месяце.
        cursor.execute(
            """
            SELECT hourly_rate FROM monthly_settings 
            WHERE (year * 100 + month) <= ?
            ORDER BY year DESC, month DESC 
            LIMIT 1
            """,
            (year * 100 + month,)
        )
        rate_row = cursor.fetchone()
        hourly_rate = rate_row['hourly_rate'] if rate_row else 0.0
        
        conn.close()
        
        return {"hourly_rate": hourly_rate, "advance": advance}

    def save_settings_for_month(self, year, month, hourly_rate, advance):
        """Сохраняет или обновляет настройки для указанного месяца."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO monthly_settings (year, month, hourly_rate, advance) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(year, month) DO UPDATE SET
            hourly_rate=excluded.hourly_rate,
            advance=excluded.advance
            """,
            (year, month, hourly_rate, advance)
        )
        conn.commit()
        conn.close()

    def get_global_setting(self, key, default=None):
        """Возвращает значение глобальной настройки."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM global_settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result['value'] if result else default

    def set_global_setting(self, key, value):
        """Сохраняет или обновляет глобальную настройку."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO global_settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()
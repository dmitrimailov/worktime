import flet as ft
from datetime import datetime
import json
import os

# Импортируем наши классы-экраны
from database_manager import DatabaseManager
from updater import Updater
from views.main_view import MainView
from views.add_edit_view import AddEditView
from views.history_view import HistoryView
from views.settings_view import SettingsView

APP_VERSION = "1.0.1" # --- ГЛАВНАЯ ВЕРСИЯ ПРИЛОЖЕНИЯ ---

def main(page: ft.Page):
    # 1. Настраиваем окно
    page.title = "Work Timer" # Заголовок окна, не виден на Android
    page.appbar = ft.AppBar(title=ft.Text(f"Work Timer v{APP_VERSION}"), center_title=True)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER # Центрируем все содержимое по горизонтали

   # Используем системную папку данных приложения
    db_path = os.path.join(page.data_dir, "work_time_flet.db")
    page.db_manager = DatabaseManager(db_name=db_path)


    # Запускаем проверку обновлений
    updater = Updater(page, APP_VERSION)
    updater.check_for_updates()

    # 2. Функция для переключения экранов
    def switch_screen(screen_widget):
        page.controls.clear()
        page.add(screen_widget)
        # Если у экрана есть метод on_show, вызываем его
        if hasattr(screen_widget, "on_show"):
            screen_widget.on_show()
        # Обновляем заголовок в AppBar в зависимости от экрана
        if hasattr(screen_widget, "appbar_title"):
            page.appbar.title = ft.Text(screen_widget.appbar_title)
        page.update()

    # 3. Создаем экземпляры всех экранов
    # Мы передаем функцию switch_screen, чтобы экраны могли сами управлять навигацией
    screens = {
        "main": MainView(switch_screen),
        "add_edit": AddEditView(switch_screen),
        "history": HistoryView(switch_screen),
        "settings": SettingsView(switch_screen),
    }

    # Передаем каждому экрану ссылки на другие экраны, чтобы они могли переключаться
    screens["main"].set_screens(screens)
    screens["add_edit"].set_screens(screens)
    screens["history"].set_screens(screens)
    screens["settings"].set_screens(screens)

    # 4. Показываем главный экран при запуске
    switch_screen(screens["main"])


if __name__ == "__main__":
    ft.run(main)

import flet as ft
from datetime import datetime
import json

# Импортируем наши классы-экраны
from database_manager import DatabaseManager
from updater import Updater
from views.main_view import MainView
from views.add_edit_view import AddEditView
from views.history_view import HistoryView
from views.settings_view import SettingsView

def main(page: ft.Page):
    # 1. Настраиваем окно
    try:
        with open('version.json', 'r') as f:
            app_version = json.load(f).get("version", "1.0.0")
    except:
        app_version = "1.0.0"

    page.title = f"Work Timer v{app_version}"
    page.appbar = ft.AppBar(title=ft.Text("Work Timer"), center_title=True)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER # Центрируем все содержимое по горизонтали

    # Инициализируем менеджер БД и сохраняем его в объекте страницы
    page.db_manager = DatabaseManager(db_name="work_time_flet.db")

    # Запускаем проверку обновлений
    updater = Updater(page, app_version)
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

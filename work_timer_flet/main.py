import flet as ft
import os
import asyncio

# Импортируем наши классы-экраны
from database_manager import DatabaseManager
from updater import Updater
from views.main_view import MainView
from views.add_edit_view import AddEditView
from views.history_view import HistoryView
from views.settings_view import SettingsView

APP_VERSION = "1.0.1" # --- ГЛАВНАЯ ВЕРСИЯ ПРИЛОЖЕНИЯ ---

async def main(page: ft.Page):
    # 1. Настраиваем окно
    page.title = "Work Timer" # Заголовок окна, не виден на Android

    # Регистрируем наш кастомный контрол для установки APK
    # page.app.add_control_factory("apk_installer", apk_installer_control_factory)

    # --- Определяем путь к базе данных ---
    # Используем page.client_storage.get("flet.app_path") - это самый надежный
    # способ получить путь к папке данных приложения на любой платформе.
    # Flet устанавливает эту переменную при сборке.
    app_data_dir = os.getenv("FLET_APP_STORAGE_DATA")

    if not app_data_dir:
        # Если мы на ПК (переменная не установлена), используем текущую папку
        app_data_dir = "."

    # --- Очистка старого файла обновления ---
    # При каждом запуске проверяем, не остался ли скачанный APK от прошлого обновления.
    try:
        old_apk_path = os.path.join(app_data_dir, "update.apk")
        if os.path.exists(old_apk_path):
            os.remove(old_apk_path)
            print(f"Старый файл обновления удален: {old_apk_path}")
    except Exception as e:
        print(f"Не удалось удалить старый файл обновления: {e}")

    db_path = os.path.join(app_data_dir, "work_time_flet.db")

    # --- Настраиваем AppBar и отладочную информацию ---
    title_text = f"Work Timer v{APP_VERSION}"
    
    # Создаем диалоговое окно для показа пути к БД
    db_path_dialog = ft.AlertDialog(
        title=ft.Text("Путь к базе данных"),
        content=ft.TextField(value=db_path, read_only=True, border=ft.InputBorder.NONE),
        on_dismiss=lambda e: print("Диалог пути к БД закрыт"),
    )
    page.overlay.append(db_path_dialog)

    def show_db_path(e):
        db_path_dialog.open = True
        page.update()

    # Создаем заголовок с обработчиком долгого нажатия
    app_title = ft.Text(title_text, size=16)
    
    page.appbar = ft.AppBar(title=ft.GestureDetector(content=app_title, on_long_press=show_db_path), center_title=True)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER # Центрируем все содержимое по горизонтали
    
    print(f"Используемый путь к БД: {db_path}")
    page.db_manager = DatabaseManager(db_name=db_path)


    # Создаем экземпляр Updater и добавляем его на страницу как невидимый контрол
    updater = Updater(APP_VERSION)
    page.add(updater)

    # 2. Функция для переключения экранов
    async def switch_screen(screen_widget):
        page.controls.clear()
        page.add(screen_widget)
        # Если у экрана есть метод on_show, вызываем его
        if hasattr(screen_widget, "on_show"):
            screen_widget.on_show()
        # Обновляем заголовок в AppBar в зависимости от экрана
        if hasattr(screen_widget, "appbar_title"):
            page.appbar.title.content = ft.Text(screen_widget.appbar_title)
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
    await switch_screen(screens["main"])

    # --- Запускаем проверку обновлений с небольшой задержкой ---
    # Это предотвращает "гонку состояний" при запуске на Android
    async def run_update_check():
        await asyncio.sleep(1) # Даем UI 1 секунду на полную отрисовку
        await updater.check_for_updates()
    page.run_task(run_update_check)


if __name__ == "__main__":
    ft.run(main)

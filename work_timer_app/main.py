# -*- coding: utf-8 -*-
import json
import threading
import requests
from packaging.version import parse as parse_version
from kivy.clock import mainthread

# Сначала выполняем все импорты, чтобы Kivy знал о классах
from kivy.lang import Builder
from kivymd.app import MDApp

# --- Добавляем импорты для всех виджетов KivyMD, используемых в .kv файле ---
# Это необходимо, чтобы Kivy знал о классах до загрузки worktimer.kv
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.list import MDListItem
from kivymd.uix.divider import MDDivider
from kivymd.uix.textfield import MDTextField
from kivymd.uix.pickers import MDModalDatePicker
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogContentContainer, MDDialogButtonContainer
# Импорты для текстовых элементов списка, используемых в HistoryScreen
from kivymd.uix.list.list import MDListItemHeadlineText, MDListItemSupportingText
# -----------------------------------------------------------------------------

from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from database.database_manager import DatabaseManager

# Импортируем классы экранов из их новых файлов
from screens.main_screen import MainScreen
from screens.history_screen import HistoryScreen
from screens.add_edit_screen import AddEditScreen
from screens.settings_screen import SettingsScreen

# Задаем размер окна, как у мобильного приложения
Window.size = (400, 700)

# Теперь, когда все импортировано, определяем класс приложения
class WorkTimerApp(MDApp):
    """Главный класс приложения."""
    db_manager = None
    app_version = "неизвестно"
    update_dialog = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        self.load_app_version()
        self.title = f"Work Timer v{self.app_version}"
        # Мы не загружаем файл вручную. Kivy автоматически найдет и загрузит 'worktimer.kv',
        # так как его имя соответствует имени класса WorkTimerApp.
        # Метод build() должен вернуть корневой виджет, который Kivy создаст из этого файла.

    def on_start(self):
        """Инициализирует менеджер базы данных при старте приложения."""
        self.db_manager = DatabaseManager()
        # Запускаем проверку обновлений в отдельном потоке, чтобы не блокировать UI
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def load_app_version(self):
        """Загружает версию приложения из version.json."""
        try:
            with open('version.json', 'r') as f:
                version_data = json.load(f)
                self.app_version = version_data.get('version', self.app_version)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Ошибка загрузки файла версии: {e}")

    def check_for_updates(self):
        """Проверяет наличие новой версии на GitHub."""
        remote_version_url = "https://raw.githubusercontent.com/dmitrimailov/worktime/main/version.json" # Укажите правильный путь к файлу
        try:
            response = requests.get(remote_version_url, timeout=5)
            response.raise_for_status()  # Вызовет ошибку для плохих статусов (404, 500 и т.д.)

            remote_data = response.json()
            remote_version_str = remote_data.get("version")

            if not remote_version_str:
                print("Не удалось найти ключ 'version' в удаленном файле.")
                return

            local_version = parse_version(self.app_version)
            remote_version = parse_version(remote_version_str)

            print(f"Локальная версия: {local_version}, Удаленная версия: {remote_version}")

            if remote_version > local_version:
                print("Доступна новая версия!")
                self.show_update_dialog(remote_version_str)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при проверке обновлений: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка парсинга файла версии с GitHub: {e}")

    @mainthread
    def show_update_dialog(self, new_version):
        """Показывает диалог о доступном обновлении (выполняется в основном потоке)."""
        if self.update_dialog:
            return

        btn_ok = MDButton(style="text")
        btn_ok.add_widget(MDButtonText(text="OK"))
        btn_ok.bind(on_release=lambda x: self.update_dialog.dismiss())

        content = MDDialogContentContainer()
        content.add_widget(MDLabel(
            text=f"Обнаружена новая версия: {new_version}.\nПожалуйста, обновите приложение.",
            halign="left"
        ))

        self.update_dialog = MDDialog(
            MDDialogHeadlineText(text="Доступно обновление"),
            content,
            MDDialogButtonContainer(btn_ok, spacing="8dp"),
        )
        self.update_dialog.open()

if __name__ == '__main__':
    WorkTimerApp().run()

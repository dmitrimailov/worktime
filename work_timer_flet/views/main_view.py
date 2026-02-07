import flet as ft
from datetime import datetime
import sys

class MainView(ft.Column):
    def __init__(self, switch_screen_func):
        super().__init__()
        self.switch_screen = switch_screen_func
        self.appbar_title = "Work Timer" # Устанавливаем временный заголовок
        self.screens = {}

        # Настройки отображения
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.expand = True

        # Создаем кнопку выхода отдельно, чтобы управлять ее видимостью
        self.exit_button = ft.OutlinedButton(
            "Выход", icon="close", on_click=self.exit_app, width=250, height=50
        )

        # Создаем элементы управления (кнопки)
        self.controls = [
            ft.FilledButton(
                "Добавить запись",
                icon="add",
                on_click=self.go_to_add_edit,
                width=250,
                height=50,
            ),
            ft.FilledButton(
                "История",
                icon="history",
                on_click=self.go_to_history,
                width=250,
                height=50,
            ),
            ft.FilledButton(
                "Настройки",
                icon="settings",
                on_click=self.go_to_settings,
                width=250,
                height=50,
            ), # Запятая здесь важна
            self.exit_button,
        ]

    def did_mount(self):
        """Этот метод вызывается, когда элемент управления добавляется на страницу."""
        # Скрываем кнопку "Выход", если это не десктопная платформа
        if self.page.platform not in [ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX]:
            self.exit_button.visible = False
            self.update()

        # Устанавливаем правильный заголовок при монтировании
        from main import APP_VERSION
        self.appbar_title = f"Work Timer v{APP_VERSION}"

    def set_screens(self, screens):
        self.screens = screens

    def go_to_add_edit(self, e):
        self.switch_screen(self.screens["add_edit"])

    def go_to_history(self, e):
        self.switch_screen(self.screens["history"])

    def go_to_settings(self, e):
        self.switch_screen(self.screens["settings"])

    async def exit_app(self, e):
        # Используем разную логику для разных платформ
        if self.page.platform in [ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX]:
            # Элегантное закрытие окна на десктопе
            await e.page.window.close()
        else:
            # "Системный" выход для мобильных платформ
            sys.exit()

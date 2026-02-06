import flet as ft
from datetime import datetime

class MainView(ft.Column):
    def __init__(self, switch_screen_func):
        super().__init__()
        self.switch_screen = switch_screen_func
        self.appbar_title = "Work Timer" # Заголовок для этого экрана
        self.screens = {}

        # Настройки отображения
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.expand = True

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
            ),
            ft.OutlinedButton(
                "Выход", icon="close", on_click=self.exit_app, width=250, height=50
            ),
        ]

    def set_screens(self, screens):
        self.screens = screens

    def go_to_add_edit(self, e):
        self.switch_screen(self.screens["add_edit"])

    def go_to_history(self, e):
        self.switch_screen(self.screens["history"])

    def go_to_settings(self, e):
        self.switch_screen(self.screens["settings"])

    async def exit_app(self, e):
        await e.page.window.close()

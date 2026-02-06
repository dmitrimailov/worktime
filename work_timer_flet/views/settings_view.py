import flet as ft

class SettingsView(ft.Column):
    def __init__(self, switch_screen_func):
        super().__init__()
        self.switch_screen = switch_screen_func
        self.appbar_title = "Настройки"
        self.screens = {}

        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.expand = True

        self.controls = [
            ft.Text("Содержимое настроек"),
            ft.FilledButton(
                "Назад",
                icon="arrow_back",
                on_click=self.go_to_main
            ),
        ]

    def set_screens(self, screens):
        self.screens = screens

    def go_to_main(self, e):
        self.switch_screen(self.screens["main"])

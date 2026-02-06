import flet as ft
from datetime import datetime

class SettingsView(ft.Column):
    def __init__(self, switch_screen_func):
        super().__init__()
        self.switch_screen = switch_screen_func
        self.appbar_title = "Настройки"
        self.screens = {}

        # --- UI Настройки ---
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.expand = True

        # --- Глобальные настройки ---
        self.lunch_duration_field = ft.TextField(
            label="Обед (часы, например 1 или 0.5)",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # --- Настройки по месяцам ---
        current_year = datetime.now().year
        self.year_dropdown = ft.Dropdown(
            label="Год",
            width=140,
            options=[ft.dropdown.Option(str(y)) for y in range(current_year - 2, current_year + 3)],
            value=str(current_year),
        )
        self.year_dropdown.on_change = self.on_date_part_change

        self.month_dropdown = ft.Dropdown(
            label="Месяц",
            width=140,
            options=[ft.dropdown.Option(str(m), text=f"{m:02d}") for m in range(1, 13)],
            value=str(datetime.now().month),
        )
        self.month_dropdown.on_change = self.on_date_part_change
        self.hourly_rate_field = ft.TextField(
            label="Часовая ставка для выбранного месяца",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.advance_field = ft.TextField(
            label="Аванс для выбранного месяца",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # --- Элементы управления ---
        self.controls = [
            ft.Text("Общие настройки", size=18, weight=ft.FontWeight.BOLD),
            self.lunch_duration_field,
            ft.Divider(),
            ft.Text("Настройки по месяцам", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([self.year_dropdown, self.month_dropdown], alignment=ft.MainAxisAlignment.CENTER),
            self.hourly_rate_field,
            self.advance_field,
            ft.Row(
                [
                    ft.FilledButton("Сохранить", icon="save", on_click=self.save_settings),
                    ft.OutlinedButton("На главный", icon="arrow_back", on_click=self.go_to_main),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            )
        ]

    def on_show(self):
        """Вызывается при показе экрана, загружаем все настройки."""
        self.load_settings()

    def load_settings(self):
        """Загружает глобальные и месячные настройки."""
        db = self.page.db_manager
        # Загружаем глобальные
        lunch_hours = db.get_global_setting("lunch_duration_hours", 1.0)
        self.lunch_duration_field.value = str(lunch_hours)
        # Загружаем для текущего выбранного месяца
        self.load_monthly_settings()

    def on_date_part_change(self, e):
        """Вызывается при смене года или месяца."""
        self.load_monthly_settings()

    def load_monthly_settings(self):
        """Загружает настройки для выбранного в Dropdown месяца."""
        db = self.page.db_manager
        year = int(self.year_dropdown.value)
        month = int(self.month_dropdown.value)
        monthly_settings = db.get_settings_for_month(year, month)
        self.hourly_rate_field.value = str(monthly_settings.get("hourly_rate", 0.0))
        self.advance_field.value = str(monthly_settings.get("advance", 0.0))
        self.update()

    def save_settings(self, e):
        """Сохраняет настройки из полей ввода."""
        db = self.page.db_manager
        # Сохраняем глобальные
        db.set_global_setting("lunch_duration_hours", float(self.lunch_duration_field.value or 1.0))
        # Сохраняем месячные
        year = int(self.year_dropdown.value)
        month = int(self.month_dropdown.value)
        hourly_rate = float(self.hourly_rate_field.value or 0)
        advance = float(self.advance_field.value or 0)
        db.save_settings_for_month(year, month, hourly_rate, advance)

        # Сначала переходим на главный экран
        self.go_to_main(e)

        # А уже потом показываем уведомление на главном экране
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Настройки сохранены!"))
        self.page.snack_bar.open = True
        self.page.update()

    def set_screens(self, screens):
        self.screens = screens

    def go_to_main(self, e):
        self.switch_screen(self.screens["main"])

import flet as ft
from datetime import datetime

class AddEditView(ft.Column):
    def __init__(self, switch_screen_func):
        super().__init__()
        self.switch_screen = switch_screen_func
        self.screens = {}
        self.selected_date = None

        # --- Создаем пикеры даты и времени ---
        self.date_picker = ft.DatePicker(
            on_change=self.date_picked,
            first_date=datetime(2023, 1, 1),
            last_date=datetime(2030, 12, 31),
        )
        self.start_time_picker = ft.TimePicker(on_change=self.start_time_picked)
        self.end_time_picker = ft.TimePicker(on_change=self.end_time_picked)

        # --- Создаем поля формы ---
        self.start_time_field = ft.TextField(
            label="Приход",
            width=140,
            read_only=True,
            on_focus=lambda e: self.open_time_picker(self.start_time_picker),
        )
        self.end_time_field = ft.TextField(
            label="Уход",
            width=140,
            read_only=True,
            on_focus=lambda e: self.open_time_picker(self.end_time_picker),
        )
        self.comment_field = ft.TextField(
            label="Комментарий",
            multiline=True,
            min_lines=3,
            width=300,
        )

        # --- Создаем контейнер для формы, который будет скрыт по умолчанию ---
        self.form_container = ft.Column(
            [
                ft.Row(
                    [self.start_time_field, self.end_time_field],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                self.comment_field,
                ft.Row(
                    [
                        ft.FilledButton("Сохранить", icon="save", on_click=self.save_entry),
                        ft.OutlinedButton("Отмена", icon="cancel", on_click=self.go_to_main),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                ft.TextButton("Выбрать другую дату", icon="calendar_month", on_click=self.show_calendar),
            ],
            visible=False, # Форма изначально скрыта
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        # --- Основные элементы управления экрана ---
        self.controls = [self.form_container]

    def build(self):
        # Добавляем пикеры в оверлей страницы при сборке
        self.page.overlay.extend([self.date_picker, self.start_time_picker, self.end_time_picker])

    def on_show(self):
        """Вызывается при показе экрана. Открывает календарь."""
        self.form_container.visible = False
        # Добавляем пикеры в оверлей, если их там еще нет
        if self.date_picker not in self.page.overlay:
            self.page.overlay.extend([self.date_picker, self.start_time_picker, self.end_time_picker])
        self.update()
        self.date_picker.open = True
        self.page.update()

    def show_calendar(self, e):
        """Показывает календарь по нажатию кнопки."""
        self.date_picker.open = True
        self.page.update()

    def date_picked(self, e):
        """Обработчик выбора даты в календаре."""
        if not e.control.value:
            # Если пользователь закрыл календарь, не выбрав дату
            if not self.selected_date:
                # И до этого дата не была выбрана, возвращаемся на главный экран
                self.go_to_main(e)
            return

        self.selected_date = e.control.value.date()
        self.page.appbar.title = ft.Text(f"Запись за {self.selected_date.strftime('%d.%m.%Y')}")

        # Здесь в будущем будет логика загрузки данных из БД
        # А пока просто подставляем значения по умолчанию
        self.start_time_field.value = "09:00"
        self.end_time_field.value = "18:00"
        self.comment_field.value = ""

        self.form_container.visible = True
        self.update()

    def start_time_picked(self, e):
        """Обработчик выбора времени начала."""
        if e.control.value:
            self.start_time_field.value = e.control.value
            self.update()

    def end_time_picked(self, e):
        """Обработчик выбора времени окончания."""
        if e.control.value:
            self.end_time_field.value = e.control.value
            self.update()

    def open_time_picker(self, picker: ft.TimePicker):
        """Открывает указанный TimePicker."""
        picker.open = True
        self.page.update()

    def save_entry(self, e):
        """Обработчик сохранения записи."""
        db_manager = self.page.db_manager
        try:
            start_str = f"{self.selected_date.isoformat()} {self.start_time_field.value}:00"
            end_str = f"{self.selected_date.isoformat()} {self.end_time_field.value}:00"

            db_manager.add_or_update_entry(
                start_time_str=start_str,
                end_time_str=end_str,
                comment=self.comment_field.value
            )
            self.go_to_main(e)
        except Exception as ex:
            # В будущем здесь можно будет показать диалоговое окно с ошибкой
            print(f"Ошибка сохранения: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {ex}"), bgcolor="error")
            self.page.snack_bar.open = True
            self.page.update()

    def set_screens(self, screens):
        self.screens = screens

    def go_to_main(self, e):
        self.switch_screen(self.screens["main"])

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
            on_dismiss=self.date_picker_dismissed,
            first_date=datetime(2023, 1, 1),
            last_date=datetime(2030, 12, 31),
        )
        self.start_time_picker = ft.TimePicker(
            confirm_text="OK",
            on_change=self.start_time_changed,
            on_dismiss=self.start_time_dismissed,
        )
        self.end_time_picker = ft.TimePicker(
            confirm_text="OK",
            on_change=self.end_time_changed,
            on_dismiss=self.end_time_dismissed,
        )

        # --- Создаем поля формы ---
        # Вместо TextField используем Text внутри Container, чтобы надежно ловить клики
        self.start_time_text = ft.Text("09:00", size=16)
        self.start_time_container = ft.Container(
            content=self.start_time_text,
            width=140,
            height=50,
            border=ft.Border.all(1, "outline"),
            border_radius=ft.BorderRadius.all(4),
            padding=ft.Padding.all(10),
            on_click=lambda e: self.open_time_picker(self.start_time_picker),
        )

        self.end_time_text = ft.Text("18:00", size=16)
        self.end_time_container = ft.Container(
            content=self.end_time_text,
            width=140,
            height=50,
            border=ft.Border.all(1, "outline"),
            border_radius=ft.BorderRadius.all(4),
            padding=ft.Padding.all(10),
            on_click=lambda e: self.open_time_picker(self.end_time_picker),
        )

        self.comment_field = ft.TextField(
            label="Комментарий",
            multiline=True,
            min_lines=3,
            width=300,
        )

        self.delete_button = ft.OutlinedButton(
            "Удалить",
            icon="delete_forever",
            on_click=self.delete_entry,
            style=ft.ButtonStyle(color="red"),
        )

        # --- Создаем контейнер для формы, который будет скрыт по умолчанию ---
        self.form_container = ft.Column(
            [
                ft.Row(
                    [self.start_time_container, self.end_time_container],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                self.comment_field,
                ft.Row(
                    [
                        ft.FilledButton("Сохранить", icon="save", on_click=self.save_entry),
                        self.delete_button,
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
        # Сбрасываем состояние при каждом входе на экран
        self.selected_date = None
        self.form_container.visible = False
        # Добавляем пикеры в оверлей, если их там еще нет
        if self.date_picker not in self.page.overlay:
            self.page.overlay.extend([self.date_picker, self.start_time_picker, self.end_time_picker])
        self.page.update() # Обновляем всю страницу
        self.date_picker.open = True
        self.page.update()

    def show_calendar(self, e):
        """Показывает календарь по нажатию кнопки."""
        self.date_picker.open = True
        self.page.update()

    def date_picked(self, e):
        """Обработчик выбора даты в календаре."""
        # Явно конвертируем время из UTC в локальное время системы
        utc_date = self.date_picker.value
        local_date = utc_date.astimezone()
        self.selected_date = local_date.date()
        self.page.appbar.title = ft.Text(f"Запись за {self.selected_date.strftime('%d.%m.%Y')}")

        # Загружаем данные для выбранной даты
        db_manager = self.page.db_manager
        entry = db_manager.get_entry_by_date(self.selected_date)

        if entry:
            # Запись найдена, загружаем данные из нее
            start_dt = datetime.fromisoformat(entry['start_time'])
            end_dt = datetime.fromisoformat(entry['end_time'])
            self.start_time_text.value = start_dt.strftime("%H:%M")
            self.end_time_text.value = end_dt.strftime("%H:%M")
            self.comment_field.value = entry['comment'] if entry['comment'] else ""
            self.delete_button.visible = True # Показываем кнопку "Удалить"
        else:
            # Запись не найдена, используем значения по умолчанию
            self.start_time_text.value = "09:00"
            self.end_time_text.value = "18:00"
            self.comment_field.value = ""
            self.delete_button.visible = False # Скрываем кнопку "Удалить"

        self.form_container.visible = True
        self.page.update() # Обновляем всю страницу

    def date_picker_dismissed(self, e):
        """Вызывается при закрытии календаря."""
        # Если календарь закрыли, а дата так и не была выбрана,
        # значит, пользователь нажал "Cancel" при первом входе.
        if not self.selected_date:
            self.go_to_main(e)

    def start_time_changed(self, e):
        """Вызывается при нажатии OK, сохраняет значение."""
        self.start_time_text.value = self.start_time_picker.value.strftime("%H:%M")

    def end_time_changed(self, e):
        """Вызывается при нажатии OK, сохраняет значение."""
        self.end_time_text.value = self.end_time_picker.value.strftime("%H:%M")

    def start_time_dismissed(self, e):
        """Вызывается при закрытии пикера, обновляет страницу."""
        print("Start Time Picker dismissed")
        # Просто обновляем страницу, чтобы применилось состояние open=False
        self.page.update() # Обновляем всю страницу

    def end_time_dismissed(self, e):
        """Вызывается при закрытии пикера, обновляет страницу."""
        print("End Time Picker dismissed")
        self.page.update() # Обновляем всю страницу

    def open_time_picker(self, picker: ft.TimePicker):
        """Открывает указанный TimePicker."""
        picker.open = True
        self.page.update()

    def save_entry(self, e):
        """Обработчик сохранения записи."""
        db_manager = self.page.db_manager
        try:
            start_str = f"{self.selected_date.isoformat()} {self.start_time_text.value}:00"
            end_str = f"{self.selected_date.isoformat()} {self.end_time_text.value}:00"

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

    def delete_entry(self, e):
        """Обработчик удаления записи."""
        if self.selected_date:
            db_manager = self.page.db_manager
            db_manager.delete_entry_by_date(self.selected_date)
            
            # Возвращаемся на главный экран и показываем уведомление
            self.go_to_main(e)
            self.page.snack_bar = ft.SnackBar(ft.Text("Запись удалена!"))
            self.page.snack_bar.open = True
            self.page.update()

    def set_screens(self, screens):
        self.screens = screens

    def go_to_main(self, e):
        # Убираем пикеры из оверлея перед уходом с экрана
        # Это предотвратит "черный экран" при повторном открытии
        if self.date_picker in self.page.overlay:
            self.page.overlay.remove(self.date_picker)
            self.page.overlay.remove(self.start_time_picker)
            self.page.overlay.remove(self.end_time_picker)
        self.page.update()
        self.switch_screen(self.screens["main"])

# -*- coding: utf-8 -*-
from datetime import date, datetime

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.pickers import MDModalDatePicker

class AddEditScreen(Screen):
    # Свойства для связи с виджетами из .kv файла
    date_button = ObjectProperty(None)
    start_time_input = ObjectProperty(None)
    end_time_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_date = date.today()
        self.dialog = None  # Свойство для хранения диалогового окна

    def on_enter(self, *args):
        """Вызывается при входе на экран. Устанавливает сегодняшнюю дату."""
        self.selected_date = date.today()
        self.date_button.text = self.selected_date.strftime('%d %B %Y')
        # Очищаем поля
        self.start_time_input.text = ""
        self.end_time_input.text = ""

    def show_calendar(self):
        # В 2.0.1 используем MDModalDatePicker
        date_dialog = MDModalDatePicker()
        date_dialog.bind(on_ok=self.on_ok, on_cancel=self.on_date_cancel)
        date_dialog.open()

    def on_ok(self, instance):
        """Вызывается при нажатии 'OK' в календаре. Получает выбранную дату из виджета."""
        
            # Получаем выбранную дату из экземпляра datepicker
        self.selected_date = instance.get_date()[0]
             
        self.date_button.text = self.selected_date.strftime('%d %B %Y')
                
        instance.dismiss()
           
              
    def on_date_cancel(self, instance):
        """Вызывается при нажатии 'CANCEL' ТОЛЬКО в календаре."""
        instance.dismiss()

    def close_dialog(self, *args):
        """Закрывает общее диалоговое окно и очищает ссылку на него."""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

    def save_entry(self):
        """Собирает данные и сохраняет их в базу данных."""
        app = App.get_running_app()
        start_time_text = self.start_time_input.text.strip()
        end_time_text = self.end_time_input.text.strip()
        comment = ""  # Поле комментария больше не используется

        def format_time(time_str):
            """Автоматически исправляет и форматирует строку времени."""
            # Заменяем точки и запятые на двоеточие
            time_str = time_str.replace('.', ':').replace(',', ':')
            # Если нет двоеточия, но есть 3 или 4 цифры, вставляем его
            if ':' not in time_str and time_str.isdigit():
                if len(time_str) == 3: # 930 -> 09:30
                    time_str = f"0{time_str[0]}:{time_str[1:]}"
                elif len(time_str) == 4: # 0930 -> 09:30
                    time_str = f"{time_str[:2]}:{time_str[2:]}"
            return time_str

        start_time_text = format_time(start_time_text)
        end_time_text = format_time(end_time_text)

        # Валидация введенного времени
        try:
            # Проверяем, что время введено и в правильном формате (ЧЧ:ММ)
            start_dt = datetime.strptime(f"{self.selected_date.isoformat()} {start_time_text}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{self.selected_date.isoformat()} {end_time_text}", "%Y-%m-%d %H:%M")

            if end_dt <= start_dt:
                self.show_error_popup("Время окончания должно быть позже времени начала.")
                return

        except ValueError:
            self.show_error_popup("Неверный формат времени. Используйте ЧЧ:ММ (например, 09:00).")
            return

        start_time_str = start_dt.isoformat(sep=' ', timespec='seconds')
        end_time_str = end_dt.isoformat(sep=' ', timespec='seconds')

        try:
            app.db_manager.add_or_update_entry(start_time_str, end_time_str, comment)
            
            # Возвращаемся на главный экран после сохранения
            self.manager.current = 'main'
        except Exception as e:
            self.show_error_popup(f"Ошибка сохранения в БД: {e}")

    def show_error_popup(self, message):
        """Показывает всплывающее окно с сообщением об ошибке."""
        if self.dialog:  # Избегаем создания нескольких диалогов
            return
        # Заменяем старый Popup на современный MDDialog
        self.dialog = MDDialog(
            title="Ошибка",
            text=message,
            buttons=[
                # В KivyMD 2.x текст кнопки задается через MDButtonText
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=self.close_dialog)
            ],
        )
        self.dialog.open()
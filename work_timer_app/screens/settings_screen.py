# -*- coding: utf-8 -*-
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.popup import Popup
from kivy.uix.label import Label

class SettingsScreen(Screen):
    # Связываем с TextInput виджетами из .kv файла
    lunch_input = ObjectProperty(None)
    rate_input = ObjectProperty(None)
    advance_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Инициализируем хранилище настроек. Файл settings.json будет создан в папке приложения.
        self.store = JsonStore('settings.json')

    def on_enter(self, *args):
        """Вызывается при входе на экран. Загружает и отображает сохраненные настройки."""
        # Сначала проверяем, есть ли вообще данные по ключу 'payroll'
        if self.store.exists('payroll'):
            payroll_data = self.store.get('payroll')
        else:
            payroll_data = {}

        # Загружаем значения или используем значения по умолчанию, если их нет
        lunch_duration = payroll_data.get('lunch_duration_hours', '1.0')
        hourly_rate = payroll_data.get('hourly_rate', '0.0')
        advance = payroll_data.get('advance', '0.0')

        # Устанавливаем текст в поля ввода
        self.lunch_input.text = str(lunch_duration)
        self.rate_input.text = str(hourly_rate)
        self.advance_input.text = str(advance)

    def save_settings(self):
        """Сохраняет введенные значения в JsonStore."""
        try:
            # Пробуем преобразовать в float для валидации
            lunch = float(self.lunch_input.text)
            rate = float(self.rate_input.text)
            advance = float(self.advance_input.text)

            # Сохраняем данные
            self.store.put('payroll',
                           lunch_duration_hours=lunch,
                           hourly_rate=rate,
                           advance=advance)

            # Возвращаемся на главный экран
            self.manager.current = 'main'
        except ValueError:
            popup = Popup(title='Ошибка', content=Label(text='Пожалуйста, введите корректные числовые значения.'), size_hint=(0.8, 0.4))
            popup.open()
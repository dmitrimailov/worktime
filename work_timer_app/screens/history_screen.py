# -*- coding: utf-8 -*-
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore
# Импортируем необходимые компоненты для списка
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText
from .calculator import calculate_monthly_summary


class HistoryScreen(Screen):
    # Связываем с контейнером для результатов из .kv файла
    results_layout = ObjectProperty(None)
    daily_entries_list = ObjectProperty(None) # Будет связано с MDList из .kv

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.year = 0
        self.month = 0
        # self.settings_store = JsonStore('settings.json') # Убираем отсюда

    def set_period(self, year, month):
        """Устанавливает период для отображения."""
        self.year = year
        self.month = month

    def on_enter(self, *args):
        """Вызывается при входе на экран. Загружает и отображает сводку."""
        # Создаем экземпляр JsonStore здесь, чтобы всегда читать актуальные данные
        self.settings_store = JsonStore('settings.json')
        self.update_summary()

    def update_summary(self):
        """Обновляет сводку на экране."""
        # Очищаем список перед обновлением
        self.daily_entries_list.clear_widgets()

        app = App.get_running_app()

        # Загружаем настройки
        if self.settings_store.exists('payroll'):
            settings = self.settings_store.get('payroll')
        else:
            settings = {} # Используем настройки по умолчанию из калькулятора
        
        lunch_duration_hours = float(settings.get('lunch_duration_hours', 1.0))

        # Рассчитываем сводку
        summary = calculate_monthly_summary(app.db_manager, self.year, self.month, settings)
        
        # --- Добавляем логику для отображения детализации по дням ---
        all_entries = app.db_manager.get_all_entries()
        
        # Фильтруем записи по выбранному периоду
        monthly_entries = []
        for entry in all_entries:
            start_dt = datetime.fromisoformat(entry['start_time'])
            if start_dt.year == self.year and start_dt.month == self.month:
                monthly_entries.append(entry)
        
        # Сортируем по дате для красивого вывода
        monthly_entries.sort(key=lambda x: x['start_time'])

        for entry in monthly_entries:
            start_dt = datetime.fromisoformat(entry['start_time'])
            end_dt = datetime.fromisoformat(entry['end_time'])
            
            # Расчет отработанного времени за день (за вычетом обеда)
            duration_without_lunch_minutes = entry['duration_minutes'] - (lunch_duration_hours * 60)
            hours, remainder = divmod(duration_without_lunch_minutes, 60)
            
            # Создаем элемент списка для каждой записи
            list_item = MDListItem(
                MDListItemHeadlineText(text=f"Дата: {start_dt.strftime('%d.%m')} | {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"),
                MDListItemSupportingText(text=f"Итог за день: {int(hours)} ч. {int(remainder)} мин."),
                # Явно устанавливаем высоту, чтобы текст не обрезался
                theme_height="Custom",
                height="72dp"
            )
            self.daily_entries_list.add_widget(list_item)
        
        # Обновляем текст в виджетах MDLabel
        self.ids.period_label.text = f"Сводка за {self.month:02}.{self.year}"
        self.ids.work_days_value.text = str(summary['work_days_count'])
        self.ids.total_hours_value.text = f"{summary['total_hours_without_lunch']} ч. (всего {summary['total_hours_with_lunch']} ч.)"
        self.ids.gross_pay_value.text = f"{summary['gross_pay']} руб."
        self.ids.tax_value.text = f"{summary['tax_amount']} руб. (13%)"
        self.ids.net_pay_value.text = f"{summary['net_pay']} руб."
        self.ids.advance_value.text = f"{summary['advance']} руб."
        self.ids.final_payout_value.text = f"[b]{summary['final_payout']} руб.[/b]"
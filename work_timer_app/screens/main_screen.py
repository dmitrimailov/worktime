# -*- coding: utf-8 -*-
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivymd.uix.dialog import (
    MDDialog, 
    MDDialogHeadlineText, 
    MDDialogButtonContainer, 
    MDDialogContentContainer
)
from kivymd.uix.button import MDButton, MDButtonText


class MonthYearPicker(BoxLayout):
    """Виджет для выбора месяца и года в диалоговом окне."""
    year_input = ObjectProperty(None)
    month_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        now = datetime.now()
        self.year_input.text = str(now.year)
        self.month_input.text = str(now.month)


class MainScreen(Screen):
    dialog = None
    picker_widget = None  # Ссылка на наш кастомный виджет

    def show_month_picker_dialog(self):
        if not self.dialog:
            # 1. Создаем экземпляр виджета и сохраняем ссылку
            self.picker_widget = MonthYearPicker()

            btn_cancel = MDButton(style="text")
            btn_cancel.add_widget(MDButtonText(text="ОТМЕНА"))
            btn_cancel.bind(on_release=self.close_dialog)

            btn_ok = MDButton(style="text")
            btn_ok.add_widget(MDButtonText(text="OK"))
            btn_ok.bind(on_release=self.process_and_show_history)

            self.dialog = MDDialog(
                MDDialogHeadlineText(text="Выберите период"),
                MDDialogContentContainer(
                    self.picker_widget, # Используем сохраненную ссылку
                    orientation="vertical",
                ),
                MDDialogButtonContainer(
                    btn_cancel,
                    btn_ok,
                    spacing="8dp",
                ),
            )
        self.dialog.open()

    def close_dialog(self, *args):
        """Закрывает диалоговое окно."""
        if self.dialog:
            self.dialog.dismiss()

    def process_and_show_history(self, *args):
        try:
            # 2. Обращаемся напрямую к сохраненной ссылке
            year_text = self.picker_widget.year_input.text
            month_text = self.picker_widget.month_input.text
            
            year = int(year_text)
            month = int(month_text)

            if not (1 <= month <= 12):
                raise ValueError("Месяц должен быть от 1 до 12")
            

            # Получаем доступ к экрану истории и передаем ему данные
            history_screen = self.manager.get_screen('history')
            history_screen.set_period(year, month)
            self.manager.current = 'history'

            self.dialog.dismiss()
            # ... переход на экран истории ...
            
        except ValueError as e:
            print(f"Ошибка ввода: {e}")
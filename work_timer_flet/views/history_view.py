import flet as ft
from datetime import datetime
from calculator import calculate_monthly_summary

class HistoryView(ft.Column):
    def __init__(self, switch_screen_func):
        super().__init__()
        self.switch_screen = switch_screen_func
        self.screens = {}

        # --- UI Настройки ---
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.expand = True

        # --- Элементы управления ---
        current_year = datetime.now().year
        current_month = datetime.now().month
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
            value=str(current_month),
        )
        self.month_dropdown.on_change = self.on_date_part_change

        # Таблица для отображения записей
        self.entries_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Дата")),
                ft.DataColumn(ft.Text("День")),
                ft.DataColumn(ft.Text("Приход")),
                ft.DataColumn(ft.Text("Уход")),
                ft.DataColumn(ft.Text("Часы"), numeric=True),
            ],
            column_spacing=20, # Уменьшаем расстояние между колонками
            rows=[],
        )

        # Текстовые поля для итоговой сводки
        self.summary_text = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        # --- Контейнеры для разных состояний экрана ---

        # 1. Контейнер для выбора даты
        self.selection_container = ft.Column(
            [
                ft.Text("Выберите период для отчета", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self.year_dropdown, self.month_dropdown], alignment=ft.MainAxisAlignment.CENTER),
                ft.FilledButton("Показать отчет", icon="summarize", on_click=self.show_report),
                ft.OutlinedButton("На главный", icon="arrow_back", on_click=self.go_to_main),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            expand=True,
        )

        # 2. Контейнер для отображения отчета (изначально скрыт)
        self.report_container = ft.Column(
            [
                # Оборачиваем таблицу в Column, чтобы она корректно расширялась и скроллилась
                ft.Column([self.entries_table], scroll=ft.ScrollMode.ADAPTIVE, expand=True),
                ft.Divider(),
                self.summary_text,
                ft.OutlinedButton("Назад к выбору", icon="arrow_back", on_click=self.show_selection),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
            expand=True,
            padding=ft.Padding.only(bottom=15), # Добавляем отступ снизу
        )

        self.controls = [
            self.selection_container,
            self.report_container,
        ]

    def on_show(self):
        """Вызывается при показе экрана, отображаем экран выбора."""
        self.show_selection()

    def on_date_part_change(self, e):
        """Вызывается при смене года или месяца."""
        self.load_history()

    def load_history(self):
        """Загружает и отображает историю и сводку за выбранный месяц."""
        year = int(self.year_dropdown.value)
        month = int(self.month_dropdown.value)
        db = self.page.db_manager

        # Обновляем заголовок
        self.page.appbar.title = ft.Text(f"История за {month:02d}.{year}")

        # 1. Загружаем и отображаем детальные записи
        self.entries_table.rows.clear()
        entries = db.get_entries_for_month(year, month)
        lunch_hours = float(db.get_global_setting("lunch_duration_hours", 1.0))
        days_map = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

        for entry in entries:
            start_dt = datetime.fromisoformat(entry['start_time'])
            end_dt = datetime.fromisoformat(entry['end_time'])
            duration_minutes = (end_dt - start_dt).total_seconds() / 60

            # --- Используем ту же логику вычета обеда, что и в калькуляторе ---
            lunch_minutes_to_deduct = 0
            if duration_minutes >= 12 * 60:
                lunch_minutes_to_deduct = lunch_hours * 60
            elif duration_minutes >= 8 * 60:
                lunch_minutes_to_deduct = lunch_hours * 60
            elif duration_minutes >= 3 * 60:
                lunch_minutes_to_deduct = 30
            
            duration_without_lunch_minutes = duration_minutes - lunch_minutes_to_deduct
            duration_without_lunch_decimal = duration_without_lunch_minutes / 60.0

            # Преобразуем десятичные часы в формат ЧЧ:ММ для отображения в таблице
            day_hours = int(duration_without_lunch_decimal)
            day_minutes = round((duration_without_lunch_decimal * 60) % 60)
            
            self.entries_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(start_dt.strftime("%d.%m"))),
                    ft.DataCell(ft.Text(days_map[start_dt.weekday()])),
                    ft.DataCell(ft.Text(start_dt.strftime("%H:%M"))),
                    ft.DataCell(ft.Text(end_dt.strftime("%H:%M"))),
                    ft.DataCell(ft.Text(f"{day_hours:02d}:{day_minutes:02d}")),
                ])
            )

        # 2. Рассчитываем и отображаем итоговую сводку
        summary = calculate_monthly_summary(db, year, month)
        self.summary_text.controls.clear()
        
        # Преобразуем десятичные часы в формат ЧЧ:ММ для наглядности
        total_hours = int(summary['total_hours_without_lunch'])
        total_minutes = int((summary['total_hours_without_lunch'] * 60) % 60)
        
        self.summary_text.controls.extend([
            ft.Text(f"Рабочих дней: {summary['work_days_count']}"),
            ft.Text(f"Всего часов (без обеда): {total_hours} ч {total_minutes:02d} мин."),
            ft.Text(f"Начислено (грязными): {summary['gross_pay']} руб."),
            ft.Text(f"Аванс: {summary['advance']} руб."),
            ft.Text(f"Налог (13%): {summary['tax_amount']} руб."),
            ft.Text(f"К выплате: {summary['final_payout']} руб.", weight=ft.FontWeight.BOLD, size=16),
        ])

        self.update()

    def show_report(self, e=None):
        """Показывает контейнер с отчетом и скрывает выбор."""
        self.load_history()
        self.selection_container.visible = False
        self.report_container.visible = True
        self.update()

    def show_selection(self, e=None):
        """Показывает контейнер выбора и скрывает отчет."""
        self.selection_container.visible = True
        self.report_container.visible = False
        self.page.appbar.title = ft.Text("История") # Сбрасываем заголовок
        self.update()

    def set_screens(self, screens):
        self.screens = screens

    def go_to_main(self, e):
        self.switch_screen(self.screens["main"])

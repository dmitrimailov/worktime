# -*- coding: utf-8 -*-

from datetime import datetime


def calculate_monthly_summary(db_manager, year, month, settings):
    """
    Рассчитывает итоговую сводку за месяц на основе записей из базы данных и настроек.

    :param db_manager: Экземпляр DatabaseManager для доступа к данным.
    :param year: Год для расчета (int).
    :param month: Месяц для расчета (int).
    :param settings: Словарь с настройками.
                     Пример: {'lunch_duration_hours': 1, 'hourly_rate': 200, 'advance': 5000}
    :return: Словарь с результатами расчетов.
    """
    
    # Получаем настройки с безопасными значениями по умолчанию
    lunch_duration_hours = float(settings.get('lunch_duration_hours', 1.0))
    hourly_rate = float(settings.get('hourly_rate', 0.0))
    advance = float(settings.get('advance', 0.0))

    # Получаем все записи из БД
    all_entries = db_manager.get_all_entries()

    total_minutes_with_lunch = 0
    total_minutes_without_lunch = 0
    work_days_count = 0

    # Фильтруем записи по указанному году и месяцу
    
    for entry in all_entries:
        start_dt = datetime.fromisoformat(entry['start_time'])
        if start_dt.year == year and start_dt.month == month:
            
            work_days_count += 1

            # Общая продолжительность в минутах (уже есть в БД)
            duration_minutes = entry['duration_minutes']
            total_minutes_with_lunch += duration_minutes

            # Вычитаем обед
            duration_without_lunch = duration_minutes - (lunch_duration_hours * 60)
            if duration_without_lunch > 0:
                total_minutes_without_lunch += duration_without_lunch

    # Конвертируем минуты в часы
    total_hours_with_lunch = round(total_minutes_with_lunch / 60.0, 2)
    total_hours_without_lunch = round(total_minutes_without_lunch / 60.0, 2)

    # Расчет зарплаты
    gross_pay = total_hours_without_lunch * hourly_rate
    tax_amount = gross_pay * 0.13
    net_pay = gross_pay - tax_amount
    final_payout = net_pay - advance

    

    return {
        'work_days_count': work_days_count,
        'total_hours_with_lunch': total_hours_with_lunch,
        'total_hours_without_lunch': total_hours_without_lunch,
        'gross_pay': round(gross_pay, 2),
        'tax_amount': round(tax_amount, 2),
        'net_pay': round(net_pay, 2),
        'advance': round(advance, 2),
        'final_payout': round(final_payout, 2),
    }

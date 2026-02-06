# -*- coding: utf-8 -*-

from datetime import datetime


def calculate_monthly_summary(db_manager, year, month):
    """
    Рассчитывает итоговую сводку за месяц на основе записей из базы данных и настроек.

    :param db_manager: Экземпляр DatabaseManager для доступа к данным.
    :param year: Год для расчета (int).
    :param month: Месяц для расчета (int).
    :return: Словарь с результатами расчетов.
    """
    
    # Получаем настройки для указанного месяца из БД
    monthly_settings = db_manager.get_settings_for_month(year, month)
    lunch_duration_hours = float(db_manager.get_global_setting("lunch_duration_hours", 1.0))
    hourly_rate = float(monthly_settings.get('hourly_rate', 0.0))
    advance = float(monthly_settings.get('advance', 0.0))

    entries_for_month = db_manager.get_entries_for_month(year, month)

    total_minutes_with_lunch = 0
    total_minutes_without_lunch = 0
    work_days_count = 0

    # Фильтруем записи по указанному году и месяцу
    
    for entry in entries_for_month:
        work_days_count += 1

        # Вычисляем продолжительность "на лету"
        start_dt = datetime.fromisoformat(entry['start_time'])
        end_dt = datetime.fromisoformat(entry['end_time'])
        duration_minutes = (end_dt - start_dt).total_seconds() / 60

        total_minutes_with_lunch += duration_minutes

        # Вычитаем обед
        lunch_minutes_to_deduct = 0
        if duration_minutes >= 12 * 60:
            # Если отработано 12 часов и более, вычитаем полный обед
            lunch_minutes_to_deduct = lunch_duration_hours * 60
        elif duration_minutes >= 8 * 60:
            # Если отработано от 8 до 12 часов, также вычитаем полный обед
            lunch_minutes_to_deduct = lunch_duration_hours * 60
        elif duration_minutes >= 3 * 60:
            # Если отработано от 3 до 8 часов, вычитаем 30 минут
            lunch_minutes_to_deduct = 30
        
        duration_without_lunch = duration_minutes - lunch_minutes_to_deduct
        total_minutes_without_lunch += duration_without_lunch if duration_without_lunch > 0 else 0

    # Конвертируем минуты в часы
    total_hours_with_lunch = total_minutes_with_lunch / 60.0
    total_hours_without_lunch = total_minutes_without_lunch / 60.0

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

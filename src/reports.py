import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


def report(func: Optional[Callable] = None, filename: Optional[str] = None):
    """Декоратор для записи результатов отчетов в файл."""

    def decorator(report_func):
        @wraps(report_func)
        def wrapper(*args, **kwargs):
            result = report_func(*args, **kwargs)

            # Генерация имени файла
            if filename:
                file_path = filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = f"{report_func.__name__}_{timestamp}.json"

            # Запись в файл
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"Отчет сохранен в файл: {file_path}")
            except Exception as e:
                logger.error(f"Ошибка сохранения отчета: {e}")

            return result

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


@report
def spending_by_category(transactions: pd.DataFrame, category: str,
                         date: Optional[str] = None) -> Dict[str, float]:
    """Анализ трат по категории за последние 3 месяца."""
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        target_date = datetime.strptime(date, "%Y-%m-%d")
        three_months_ago = target_date - timedelta(days=90)

        # Фильтрация транзакций
        transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'])
        filtered_df = transactions[
            (transactions['Дата операции'] >= three_months_ago) &
            (transactions['Дата операции'] <= target_date) &
            (transactions['Категория'] == category)
            ]

        # Группировка по месяцам
        filtered_df['Месяц'] = filtered_df['Дата операции'].dt.to_period('M')
        monthly_spending = filtered_df.groupby('Месяц')['Сумма операции'].sum().abs()

        result = {str(month): round(amount, 2) for month, amount in monthly_spending.items()}
        logger.info(f"Проанализированы траты по категории '{category}'")

        return result
    except Exception as e:
        logger.error(f"Ошибка анализа трат по категории: {e}")
        return {}


@report
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> Dict[str, float]:
    """Средние траты по дням недели за последние 3 месяца."""
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        target_date = datetime.strptime(date, "%Y-%m-%d")
        three_months_ago = target_date - timedelta(days=90)

        # Фильтрация транзакций
        transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'])
        filtered_df = transactions[
            (transactions['Дата операции'] >= three_months_ago) &
            (transactions['Дата операции'] <= target_date)
            ]

        # Анализ по дням недели
        filtered_df['День недели'] = filtered_df['Дата операции'].dt.day_name()
        weekday_spending = filtered_df.groupby('День недели')['Сумма операции'].mean().abs()

        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        result = {day: round(weekday_spending.get(day, 0), 2) for day in days_order}

        logger.info("Проанализированы траты по дням недели")
        return result
    except Exception as e:
        logger.error(f"Ошибка анализа трат по дням недели: {e}")
        return {}
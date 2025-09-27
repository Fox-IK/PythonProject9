import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Dict
from functools import wraps
import os
from .utils import load_transactions

logger = logging.getLogger(__name__)


def report_decorator(filename: Optional[str] = None):
    """Декоратор для сохранения отчетов в файл"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Генерация имени файла если не указано
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                func_name = func.__name__
                report_filename = f"reports/{func_name}_{timestamp}.json"
            else:
                report_filename = filename

            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(report_filename), exist_ok=True)

            # Сохранение результата
            try:
                with open(report_filename, 'w', encoding='utf-8') as f:
                    if isinstance(result, pd.DataFrame):
                        json.dump(result.to_dict('records'), f, ensure_ascii=False, indent=2)
                    else:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"Отчет сохранен в {report_filename}")
            except Exception as e:
                logger.error(f"Ошибка сохранения отчета: {e}")

            return result

        return wrapper

    return decorator


class ReportGenerator:
    """Генератор отчетов"""

    @staticmethod
    @report_decorator()
    def spending_by_category(transactions: pd.DataFrame,
                             category: str,
                             date: Optional[str] = None) -> pd.DataFrame:
        """Траты по категории за последние 3 месяца"""
        try:
            if date is None:
                target_date = datetime.now()
            else:
                target_date = datetime.strptime(date, '%Y-%m-%d')

            # Расчет даты начала периода (3 месяца назад)
            start_date = target_date - timedelta(days=90)

            # Фильтрация данных
            mask = (transactions['Дата операции'] >= start_date) & \
                   (transactions['Дата операции'] <= target_date) & \
                   (transactions['Категория'] == category) & \
                   (transactions['Статус'] == 'OK') & \
                   (transactions['Сумма операции'] > 0)

            filtered_data = transactions.loc[mask].copy()

            if filtered_data.empty:
                return pd.DataFrame(columns=['Месяц', 'Сумма'])

            # Группировка по месяцам
            filtered_data['Месяц'] = filtered_data['Дата операции'].dt.to_period('M')
            monthly_spending = filtered_data.groupby('Месяц')['Сумма операции'].sum().reset_index()
            monthly_spending['Месяц'] = monthly_spending['Месяц'].astype(str)
            monthly_spending['Сумма'] = monthly_spending['Сумма операции'].round(2)

            return monthly_spending[['Месяц', 'Сумма']]

        except Exception as e:
            logger.error(f"Ошибка в spending_by_category: {e}")
            return pd.DataFrame()

    @staticmethod
    @report_decorator()
    def spending_by_weekday(transactions: pd.DataFrame,
                            date: Optional[str] = None) -> pd.DataFrame:
        """Средние траты по дням недели"""
        try:
            if date is None:
                target_date = datetime.now()
            else:
                target_date = datetime.strptime(date, '%Y-%m-%d')

            start_date = target_date - timedelta(days=90)

            mask = (transactions['Дата операции'] >= start_date) & \
                   (transactions['Дата операции'] <= target_date) & \
                   (transactions['Статус'] == 'OK') & \
                   (transactions['Сумма операции'] > 0)

            filtered_data = transactions.loc[mask].copy()

            if filtered_data.empty:
                return pd.DataFrame(columns=['День недели', 'Средняя сумма'])

            # Маппинг дней недели на русский
            day_mapping = {
                0: 'Понедельник',
                1: 'Вторник',
                2: 'Среда',
                3: 'Четверг',
                4: 'Пятница',
                5: 'Суббота',
                6: 'Воскресенье'
            }

            filtered_data['День недели'] = filtered_data['Дата операции'].dt.weekday.map(day_mapping)
            avg_spending = filtered_data.groupby('День недели')['Сумма операции'].mean().reset_index()
            avg_spending['Средняя сумма'] = avg_spending['Сумма операции'].round(2)

            # Сортировка по порядку дней недели
            day_order = list(day_mapping.values())
            avg_spending['День недели'] = pd.Categorical(avg_spending['День недели'], categories=day_order,
                                                         ordered=True)
            avg_spending = avg_spending.sort_values('День недели')

            return avg_spending[['День недели', 'Средняя сумма']]

        except Exception as e:
            logger.error(f"Ошибка в spending_by_weekday: {e}")
            return pd.DataFrame()

    @staticmethod
    @report_decorator()
    def spending_by_workday(transactions: pd.DataFrame,
                            date: Optional[str] = None) -> pd.DataFrame:
        """Средние траты в рабочие/выходные дни"""
        try:
            if date is None:
                target_date = datetime.now()
            else:
                target_date = datetime.strptime(date, '%Y-%m-%d')

            start_date = target_date - timedelta(days=90)

            mask = (transactions['Дата операции'] >= start_date) & \
                   (transactions['Дата операции'] <= target_date) & \
                   (transactions['Статус'] == 'OK') & \
                   (transactions['Сумма операции'] > 0)

            filtered_data = transactions.loc[mask].copy()

            if filtered_data.empty:
                return pd.DataFrame(columns=['Тип дня', 'Средняя сумма'])

            filtered_data['День недели'] = filtered_data['Дата операции'].dt.weekday
            filtered_data['Тип дня'] = filtered_data['День недели'].apply(
                lambda x: 'Выходной' if x >= 5 else 'Рабочий'
            )

            avg_spending = filtered_data.groupby('Тип дня')['Сумма операции'].mean().reset_index()
            avg_spending['Средняя сумма'] = avg_spending['Сумма операции'].round(2)

            return avg_spending[['Тип дня', 'Средняя сумма']]

        except Exception as e:
            logger.error(f"Ошибка в spending_by_workday: {e}")
            return pd.DataFrame()

    @staticmethod
    @report_decorator()
    def monthly_summary(transactions: pd.DataFrame,
                        months: int = 6) -> Dict[str, Any]:
        """Сводный отчет за несколько месяцев"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)

            mask = (transactions['Дата операции'] >= start_date) & \
                   (transactions['Дата операции'] <= end_date)

            filtered_data = transactions.loc[mask].copy()

            if filtered_data.empty:
                return {"error": "Нет данных за указанный период"}

            # Расходы по месяцам
            filtered_data['Месяц'] = filtered_data['Дата операции'].dt.to_period('M')
            expenses = filtered_data[filtered_data['Сумма операции'] > 0]
            income = filtered_data[filtered_data['Сумма операции'] < 0]

            monthly_expenses = expenses.groupby('Месяц')['Сумма операции'].sum()
            monthly_income = income.groupby('Месяц')['Сумма операции'].sum().abs()

            # Топ категории расходов
            top_categories = expenses.groupby('Категория')['Сумма операции'].sum().nlargest(5)

            report = {
                "period": f"{start_date.strftime('%Y-%m')} - {end_date.strftime('%Y-%m')}",
                "total_expenses": round(expenses['Сумма операции'].sum(), 2),
                "total_income": round(income['Сумма операции'].sum().abs(), 2),
                "monthly_expenses": {
                    month.strftime('%Y-%m'): round(amount, 2)
                    for month, amount in monthly_expenses.items()
                },
                "monthly_income": {
                    month.strftime('%Y-%m'): round(amount, 2)
                    for month, amount in monthly_income.items()
                },
                "top_categories": {
                    category: round(amount, 2)
                    for category, amount in top_categories.items()
                }
            }

            return report

        except Exception as e:
            logger.error(f"Ошибка в monthly_summary: {e}")
            return {"error": str(e)}


# Функции-обертки для совместимости
def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
    return ReportGenerator.spending_by_category(transactions, category, date)


def spending_by_weekday(transactions: pd.DataFrame,
                        date: Optional[str] = None) -> pd.DataFrame:
    return ReportGenerator.spending_by_weekday(transactions, date)


def spending_by_workday(transactions: pd.DataFrame,
                        date: Optional[str] = None) -> pd.DataFrame:
    return ReportGenerator.spending_by_workday(transactions, date)

import logging
import re
from datetime import datetime
from functools import reduce, wraps
from typing import Any, Callable, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class CashbackAnalyzer:
    """Анализатор выгодности категорий кешбэка"""

    def __init__(self, cashback_rules: Dict[str, float]):
        self.cashback_rules = cashback_rules

    def analyze_profitable_categories(self, data: pd.DataFrame, year: int,
                                      month: int) -> Dict[str, float]:
        """Анализ выгодности категорий повышенного кешбэка"""
        try:
            # Фильтрация данных по году и месяцу
            mask = (data['Дата операции'].dt.year == year) & \
                   (data['Дата операции'].dt.month == month) & \
                   (data['Статус'] == 'OK') & \
                   (data['Сумма операции'] > 0)  # Только расходы

            filtered_data = data.loc[mask]

            if filtered_data.empty:
                logger.warning(f"Нет данных за {month}/{year}")
                return {}

            # Группировка по категориям и расчет потенциального кешбэка
            cashback_analysis = {}

            for category in filtered_data['Категория'].unique():
                if pd.isna(category) or category == '':
                    continue

                category_data = filtered_data[filtered_data['Категория'] == category]

                # Расчет кешбэка по сложной логике
                from .utils import calculate_cashback
                potential_cashback = sum(
                    calculate_cashback(row['Сумма операции'], category, self.cashback_rules)
                    for _, row in category_data.iterrows()
                )

                cashback_analysis[category] = round(potential_cashback, 2)

            # Сортировка по убыванию кешбэка
            return dict(sorted(cashback_analysis.items(),
                               key=lambda x: x[1], reverse=True))

        except Exception as e:
            logger.error(f"Ошибка анализа категорий кешбэка: {e}")
            return {}


class InvestmentCalculator:
    """Калькулятор инвесткопилки"""

    @staticmethod
    def investment_bank(month: str, transactions: List[Dict[str, Any]],
                        limit: int) -> float:
        """Расчет суммы для инвесткопилки"""
        try:
            if limit not in [10, 50, 100]:
                raise ValueError("Лимит округления должен быть 10, 50 или 100")

            target_month = datetime.strptime(month, '%Y-%m')
            total_savings = 0.0

            for transaction in transactions:
                # Валидация транзакции
                if not InvestmentCalculator._validate_transaction(transaction):
                    continue

                trans_date = datetime.strptime(transaction['Дата операции'], '%Y-%m-%d')

                if (trans_date.year == target_month.year
                        and trans_date.month == target_month.month):

                    amount = float(transaction['Сумма операции'])
                    if amount > 0:  # Только расходы
                        # Округление вверх до ближайшего кратного limit
                        rounded_amount = ((amount + limit - 1) // limit) * limit
                        savings = rounded_amount - amount
                        total_savings += savings

            return round(total_savings, 2)

        except Exception as e:
            logger.error(f"Ошибка расчета инвесткопилки: {e}")
            return 0.0

    @staticmethod
    def _validate_transaction(transaction: Dict[str, Any]) -> bool:
        """Валидация транзакции"""
        required_fields = ['Дата операции', 'Сумма операции']

        for field in required_fields:
            if field not in transaction:
                logger.warning(f"Отсутствует поле {field} в транзакции")
                return False

        try:
            datetime.strptime(transaction['Дата операции'], '%Y-%m-%d')
            float(transaction['Сумма операции'])
            return True
        except (ValueError, TypeError):
            logger.warning("Некорректные данные в транзакции")
            return False


class TransactionSearcher:
    """Поисковик транзакций"""

    @staticmethod
    def simple_search(transactions: List[Dict[str, Any]],
                      search_string: str) -> List[Dict[str, Any]]:
        """Простой поиск по описанию и категории"""
        if not search_string or len(search_string.strip()) < 2:
            raise ValueError("Строка поиска должна содержать минимум 2 символа")

        def search_filter(transaction: Dict[str, Any]) -> bool:
            description = str(transaction.get('Описание', '')).lower()
            category = str(transaction.get('Категория', '')).lower()
            search_lower = search_string.lower()

            return (search_lower in description
                    or search_lower in category)

        return list(filter(search_filter, transactions))

    @staticmethod
    def search_by_phone(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Поиск транзакций с телефонными номерами"""
        # Паттерны для российских мобильных номеров
        phone_patterns = [
            r'\+7\s?\d{3}\s?\d{3}[\s-]?\d{2}[\s-]?\d{2}',  # +7 XXX XXX-XX-XX
            r'8\s?\d{3}\s?\d{3}[\s-]?\d{2}[\s-]?\d{2}',  # 8 XXX XXX-XX-XX
            r'\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}'  # XXX XXX-XX-XX
        ]

        def phone_filter(transaction: Dict[str, Any]) -> bool:
            description = str(transaction.get('Описание', ''))

            for pattern in phone_patterns:
                if re.search(pattern, description):
                    return True
            return False

        return list(filter(phone_filter, transactions))

    @staticmethod
    def search_by_person_transfers(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Поиск переводов физическим лицам"""
        # Паттерн для имени и фамилии с инициалом: "Имя Ф."
        name_pattern = r'[А-Я][а-я]+\s[А-Я]\.'

        def transfer_filter(transaction: Dict[str, Any]) -> bool:
            category = transaction.get('Категория', '')
            description = str(transaction.get('Описание', ''))

            return (category == 'Переводы'
                    and bool(re.search(name_pattern, description)))

        return list(filter(transfer_filter, transactions))


# Функциональные утилиты
def compose(*functions: Callable) -> Callable:
    """Композиция функций"""
    return reduce(lambda f, g: lambda x: f(g(x)), functions)


def pipe(value: Any, *functions: Callable) -> Any:
    """Конвейерная обработка значения через функции"""
    return compose(*functions)(value)


# Декораторы для логирования
def log_service_call(service_name: str):
    """Декоратор для логирования вызовов сервисов"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"Вызов сервиса {service_name}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Сервис {service_name} выполнен успешно")
                return result
            except Exception as e:
                logger.error(f"Ошибка в сервисе {service_name}: {e}")
                raise

        return wrapper

    return decorator


# Экспорт основных функций с декораторами
@log_service_call("profitable_cashback_categories")
def profitable_cashback_categories(data: pd.DataFrame, year: int,
                                   month: int, cashback_rules: Dict[str, float]) -> Dict[str, float]:
    analyzer = CashbackAnalyzer(cashback_rules)
    return analyzer.analyze_profitable_categories(data, year, month)


@log_service_call("investment_bank")
def investment_bank(month: str, transactions: List[Dict[str, Any]],
                    limit: int) -> float:
    return InvestmentCalculator.investment_bank(month, transactions, limit)


@log_service_call("simple_search")
def simple_search(transactions: List[Dict[str, Any]],
                  search_string: str) -> List[Dict[str, Any]]:
    return TransactionSearcher.simple_search(transactions, search_string)


@log_service_call("search_by_phone")
def search_by_phone(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return TransactionSearcher.search_by_phone(transactions)


@log_service_call("search_by_person_transfers")
def search_by_person_transfers(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return TransactionSearcher.search_by_person_transfers(transactions)

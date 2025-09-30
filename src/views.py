import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from .api_client import SyncAPIClient
from .utils import (
    calculate_cashback,
    filter_transactions_by_date,
    get_date_range,
    get_greeting,
    load_transactions,
    load_user_settings,
)

logger = logging.getLogger(__name__)


class DataProcessor:
    """Процессор данных для веб-страниц"""

    @staticmethod
    def process_main_page_data(df: pd.DataFrame, date_time: str,
                               settings: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка данных для главной страницы"""
        try:
            start_date, end_date = get_date_range(date_time, 'M')
            filtered_df = filter_transactions_by_date(df, start_date, end_date)

            cashback_rules = settings.get('cashback_rules', {'default': 0.01})

            return {
                'greeting': get_greeting(date_time),
                'cards': DataProcessor._get_cards_data(filtered_df, cashback_rules),
                'top_transactions': DataProcessor._get_top_transactions(filtered_df, 5),
                'currency_rates': SyncAPIClient.get_currency_rates(settings['user_currencies']),
                'stock_prices': SyncAPIClient.get_stock_prices(settings['user_stocks'])
            }
        except Exception as e:
            logger.error(f"Ошибка обработки данных главной страницы: {e}")
            raise

    @staticmethod
    def process_events_page_data(df: pd.DataFrame, date: str, period: str,
                                 settings: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка данных для страницы событий"""
        try:
            start_date, end_date = get_date_range(date, period)
            filtered_df = filter_transactions_by_date(df, start_date, end_date)

            return {
                'expenses': DataProcessor._get_expenses_data(filtered_df),
                'income': DataProcessor._get_income_data(filtered_df),
                'currency_rates': SyncAPIClient.get_currency_rates(settings['user_currencies']),
                'stock_prices': SyncAPIClient.get_stock_prices(settings['user_stocks'])
            }
        except Exception as e:
            logger.error(f"Ошибка обработки данных страницы событий: {e}")
            raise

    @staticmethod
    def _get_cards_data(df: pd.DataFrame, cashback_rules: Dict[str, float]) -> List[Dict[str, Any]]:
        """Данные по картам"""
        cards_data = []

        # Получаем уникальные номера карт
        card_numbers = [card for card in df['Номер карты'].unique()
                        if not pd.isna(card) and str(card).strip() != '']

        for card in card_numbers:
            card_df = df[df['Номер карты'] == card]
            # Только успешные операции расходов
            expenses_df = card_df[(card_df['Статус'] == 'OK')
                                  & (card_df['Сумма операции'] > 0)]

            if expenses_df.empty:
                continue

            total_spent = expenses_df['Сумма операции'].sum()

            # Расчет общего кешбэка по сложной логике
            total_cashback = 0
            for _, transaction in expenses_df.iterrows():
                category = transaction.get('Категория', '')
                amount = transaction['Сумма операции']
                total_cashback += calculate_cashback(amount, category, cashback_rules)

            cards_data.append({
                'last_digits': str(card)[-4:],
                'total_spent': round(total_spent, 2),
                'cashback': round(total_cashback, 2)
            })

        # Сортировка по убыванию общей суммы расходов
        return sorted(cards_data, key=lambda x: x['total_spent'], reverse=True)

    @staticmethod
    def _get_top_transactions(df: pd.DataFrame, limit: int) -> List[Dict[str, Any]]:
        """Топ транзакций по сумме платежа"""
        # Берем абсолютное значение для сравнения (учитываем и доходы и расходы)
        df['Абсолютная сумма'] = df['Сумма платежа'].abs()
        top_df = df.nlargest(limit, 'Абсолютная сумма')

        transactions = []
        for _, row in top_df.iterrows():
            transactions.append({
                'date': row['Дата операции'].strftime('%d.%m.%Y'),
                'amount': round(row['Сумма платежа'], 2),
                'category': row.get('Категория', 'Не указана'),
                'description': row.get('Описание', '')[:100]  # Ограничение длины
            })

        return transactions

    @staticmethod
    def _get_expenses_data(df: pd.DataFrame) -> Dict[str, Any]:
        """Данные по расходам"""
        expenses_df = df[(df['Статус'] == 'OK') & (df['Сумма операции'] > 0)]

        if expenses_df.empty:
            return {
                'total_amount': 0,
                'main': [],
                'transfers_and_cash': []
            }

        total_amount = expenses_df['Сумма операции'].sum()

        # Основные категории (топ-6 + остальное)
        category_expenses = expenses_df.groupby('Категория')['Сумма операции'].sum()
        top_categories = category_expenses.nlargest(6)
        other_categories = category_expenses.iloc[6:].sum() if len(category_expenses) > 6 else 0

        main_categories = [
            {'category': cat, 'amount': round(amount, 0)}
            for cat, amount in top_categories.items() if not pd.isna(cat)
        ]

        if other_categories > 0:
            main_categories.append({'category': 'Остальное', 'amount': round(other_categories, 0)})

        # Переводы и наличные
        transfers_cash = expenses_df[expenses_df['Категория'].isin(['Наличные', 'Переводы'])]
        transfers_data = transfers_cash.groupby('Категория')['Сумма операции'].sum()

        transfers_list = [
            {'category': cat, 'amount': round(amount, 0)}
            for cat, amount in transfers_data.items()
        ]

        return {
            'total_amount': round(total_amount, 0),
            'main': main_categories,
            'transfers_and_cash': transfers_list
        }

    @staticmethod
    def _get_income_data(df: pd.DataFrame) -> Dict[str, Any]:
        """Данные по поступлениям"""
        income_df = df[(df['Статус'] == 'OK') & (df['Сумма операции'] < 0)]

        if income_df.empty:
            return {
                'total_amount': 0,
                'main': []
            }

        # Преобразуем отрицательные суммы в положительные
        income_df = income_df.copy()
        income_df['Сумма операции'] = income_df['Сумма операции'].abs()

        total_amount = income_df['Сумма операции'].sum()

        category_income = income_df.groupby('Категория')['Сумма операции'].sum()

        main_income = [
            {'category': cat, 'amount': round(amount, 0)}
            for cat, amount in category_income.items() if not pd.isna(cat)
        ]

        return {
            'total_amount': round(total_amount, 0),
            'main': sorted(main_income, key=lambda x: x['amount'], reverse=True)
        }


def main_page(date_time: str, data_file: Optional[str] = None) -> Dict[str, Any]:
    """Главная страница - генерация JSON данных"""
    try:
        df = load_transactions(data_file) if data_file else load_transactions()
        settings = load_user_settings()

        processor = DataProcessor()
        return processor.process_main_page_data(df, date_time, settings)

    except Exception as e:
        logger.error(f"Ошибка генерации главной страницы: {e}")
        return {'error': str(e), 'greeting': 'Добрый день'}


def events_page(date: str, period: str = 'M',
                data_file: Optional[str] = None) -> Dict[str, Any]:
    """Страница событий - генерация JSON данных"""
    try:
        df = load_transactions(data_file) if data_file else load_transactions()
        settings = load_user_settings()

        processor = DataProcessor()
        return processor.process_events_page_data(df, date, period, settings)

    except Exception as e:
        logger.error(f"Ошибка генерации страницы событий: {e}")
        return {'error': str(e)}

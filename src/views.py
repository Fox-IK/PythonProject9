import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from .utils import get_greeting, get_currency_rates, get_stock_prices, filter_transactions_by_date

logger = logging.getLogger(__name__)


def home_page(date_str: str, transactions_df: pd.DataFrame, user_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Главная страница с анализом транзакций."""
    try:
        # Фильтрация транзакций
        filtered_df = filter_transactions_by_date(transactions_df, date_str)

        # Приветствие
        greeting = get_greeting(date_str)

        # Анализ по картам
        cards_analysis = _analyze_cards(filtered_df)

        # Топ транзакций
        top_transactions = _get_top_transactions(filtered_df)

        # Курсы валют и акции
        currency_rates = get_currency_rates(user_settings.get("user_currencies", []))
        stock_prices = get_stock_prices(user_settings.get("user_stocks", []))

        return {
            "greeting": greeting,
            "cards": cards_analysis,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices
        }
    except Exception as e:
        logger.error(f"Ошибка генерации главной страницы: {e}")
        return {"error": str(e)}


def _analyze_cards(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Анализ транзакций по картам."""
    cards_analysis = []

    # Группировка по последним цифрам карты
    if 'Номер карты' in df.columns:
        for card in df['Номер карты'].dropna().unique():
            card_transactions = df[df['Номер карты'] == card]
            total_spent = card_transactions['Сумма операции'].sum()
            cashback = total_spent * 0.01  # 1% кешбэк

            cards_analysis.append({
                "last_digits": str(card)[-4:],
                "total_spent": round(total_spent, 2),
                "cashback": round(cashback, 2)
            })

    return cards_analysis


def _get_top_transactions(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    """Получение топ-N транзакций по сумме."""
    try:
        # Берем абсолютные значения для сортировки
        df_sorted = df.nlargest(top_n, 'Сумма операции', keep='first')

        top_transactions = []
        for _, row in df_sorted.iterrows():
            top_transactions.append({
                "date": row['Дата операции'].strftime("%d.%m.%Y"),
                "amount": round(row['Сумма операции'], 2),
                "category": row.get('Категория', 'Неизвестно'),
                "description": row.get('Описание', '')
            })

        return top_transactions
    except Exception as e:
        logger.error(f"Ошибка получения топ транзакций: {e}")
        return []

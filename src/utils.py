import json
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_transactions(file_path: str) -> pd.DataFrame:
    """Загрузка транзакций из Excel файла."""
    try:
        df = pd.read_excel(file_path)
        logger.info(f"Успешно загружено {len(df)} транзакций")
        return df
    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        raise


def filter_transactions_by_date(df: pd.DataFrame, date_str: str) -> pd.DataFrame:
    """Фильтрация транзакций по дате."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start_of_month = target_date.replace(day=1, hour=0, minute=0, second=0)

        df['Дата операции'] = pd.to_datetime(df['Дата операции'])
        filtered_df = df[(df['Дата операции'] >= start_of_month) &
                         (df['Дата операции'] <= target_date)]

        logger.info(f"Отфильтровано {len(filtered_df)} транзакций за период")
        return filtered_df
    except Exception as e:
        logger.error(f"Ошибка фильтрации по дате: {e}")
        raise


def get_greeting(time_str: str) -> str:
    """Получение приветствия в зависимости от времени суток."""
    try:
        time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").time()

        if time_obj.hour < 6:
            return "Доброй ночи"
        elif time_obj.hour < 12:
            return "Доброе утро"
        elif time_obj.hour < 18:
            return "Добрый день"
        else:
            return "Добрый вечер"
    except Exception as e:
        logger.error(f"Ошибка определения приветствия: {e}")
        return "Добрый день"


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """Получение курсов валют через API."""
    try:
        # Заглушка для демонстрации - в реальном проекте используйте реальное API
        rates = []
        for currency in currencies:
            if currency == "USD":
                rates.append({"currency": currency, "rate": 73.21})
            elif currency == "EUR":
                rates.append({"currency": currency, "rate": 87.08})
            else:
                rates.append({"currency": currency, "rate": 1.0})

        logger.info("Курсы валют успешно получены")
        return rates
    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")
        return []


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """Получение цен акций через API."""
    try:
        # Заглушка для демонстрации
        prices = []
        stock_prices = {
            "AAPL": 150.12,
            "AMZN": 3173.18,
            "GOOGL": 2742.39,
            "MSFT": 296.71,
            "TSLA": 1007.08
        }

        for stock in stocks:
            price = stock_prices.get(stock, 0.0)
            prices.append({"stock": stock, "price": price})

        logger.info("Цены акций успешно получены")
        return prices
    except Exception as e:
        logger.error(f"Ошибка получения цен акций: {e}")
        return []

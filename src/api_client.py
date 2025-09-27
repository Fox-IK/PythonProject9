import aiohttp
import asyncio
import json
import cachetools
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Кэш для API запросов
cache = cachetools.TTLCache(maxsize=100, ttl=settings.cache_ttl)


class APIClient:
    """Клиент для работы с внешними API"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_currency_rates(self, currencies: List[str]) -> List[Dict[str, float]]:
        """Получение актуальных курсов валют"""
        cache_key = f"currency_rates_{'_'.join(sorted(currencies))}"

        if cache_key in cache:
            logger.info("Using cached currency rates")
            return cache[cache_key]

        try:
            # Пробуем разные API по очереди
            rates = await self._get_currency_rates_exchangerate(currencies)
            if not rates:
                rates = await self._get_currency_rates_currencyapi(currencies)

            if rates:
                cache[cache_key] = rates
                return rates
            else:
                # Fallback к статическим данным
                return self._get_fallback_currency_rates(currencies)

        except Exception as e:
            logger.error(f"Error fetching currency rates: {e}")
            return self._get_fallback_currency_rates(currencies)

    async def _get_currency_rates_exchangerate(self, currencies: List[str]) -> List[Dict[str, float]]:
        """Получение курсов валют через ExchangeRate API"""
        try:
            base_currency = "RUB"
            target_currencies = [c for c in currencies if c != "RUB"]

            if not target_currencies:
                return [{"currency": "RUB", "rate": 1.0}]

            async with self.session.get(
                    f"{settings.exchangerate_url}?base={base_currency}&symbols={','.join(target_currencies)}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = [{"currency": "RUB", "rate": 1.0}]

                    for currency in target_currencies:
                        if currency in data.get("rates", {}):
                            rate = 1 / data["rates"][currency]  # Конвертируем из RUB в валюту
                            rates.append({"currency": currency, "rate": round(rate, 4)})

                    return rates
        except Exception as e:
            logger.warning(f"ExchangeRate API failed: {e}")
            return []

    async def _get_currency_rates_currencyapi(self, currencies: List[str]) -> List[Dict[str, float]]:
        """Получение курсов валют через CurrencyAPI"""
        try:
            if not settings.currency_api_key:
                return []

            base_currency = "RUB"
            target_currencies = [c for c in currencies if c != "RUB"]

            async with self.session.get(
                    f"{settings.currency_api_url}?apikey={settings.currency_api_key}&base_currency={base_currency}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = [{"currency": "RUB", "rate": 1.0}]

                    for currency in target_currencies:
                        if currency in data.get("data", {}):
                            rate = 1 / data["data"][currency]["value"]
                            rates.append({"currency": currency, "rate": round(rate, 4)})

                    return rates
        except Exception as e:
            logger.warning(f"CurrencyAPI failed: {e}")
            return []

    async def get_stock_prices(self, stocks: List[str]) -> List[Dict[str, float]]:
        """Получение актуальных цен акций"""
        cache_key = f"stock_prices_{'_'.join(sorted(stocks))}"

        if cache_key in cache:
            logger.info("Using cached stock prices")
            return cache[cache_key]

        try:
            prices = await self._get_stock_prices_alphavantage(stocks)
            if prices:
                cache[cache_key] = prices
                return prices
            else:
                return self._get_fallback_stock_prices(stocks)

        except Exception as e:
            logger.error(f"Error fetching stock prices: {e}")
            return self._get_fallback_stock_prices(stocks)

    async def _get_stock_prices_alphavantage(self, stocks: List[str]) -> List[Dict[str, float]]:
        """Получение цен акций через Alpha Vantage"""
        try:
            prices = []

            for stock in stocks:
                # Для демо-режима используем лимитированные запросы
                if settings.alpha_vantage_api_key == "demo":
                    # Используем fallback данные для демо
                    continue

                async with self.session.get(
                        f"{settings.alpha_vantage_url}?function=GLOBAL_QUOTE&symbol={stock}&apikey={settings.alpha_vantage_api_key}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get("Global Quote", {})
                        if quote:
                            price = float(quote.get("05. price", 0))
                            prices.append({"stock": stock, "price": round(price, 2)})

            return prices if prices else []

        except Exception as e:
            logger.warning(f"Alpha Vantage API failed: {e}")
            return []

    def _get_fallback_currency_rates(self, currencies: List[str]) -> List[Dict[str, float]]:
        """Резервные данные о курсах валют"""
        fallback_rates = {
            "USD": 93.45,
            "EUR": 101.23,
            "GBP": 117.89,
            "CNY": 12.87,
            "JPY": 0.63,
            "RUB": 1.0
        }

        rates = []
        for currency in currencies:
            rate = fallback_rates.get(currency, 1.0)
            rates.append({"currency": currency, "rate": rate})

        logger.info("Using fallback currency rates")
        return rates

    def _get_fallback_stock_prices(self, stocks: List[str]) -> List[Dict[str, float]]:
        """Резервные данные о ценах акций"""
        fallback_prices = {
            "AAPL": 178.72,
            "AMZN": 145.63,
            "GOOGL": 138.21,
            "MSFT": 374.51,
            "TSLA": 235.49,
            "META": 351.95,
            "NVDA": 477.76,
            "NFLX": 485.13
        }

        prices = []
        for stock in stocks:
            price = fallback_prices.get(stock, 0.0)
            if price > 0:
                prices.append({"stock": stock, "price": price})

        logger.info("Using fallback stock prices")
        return prices


# Синхронная обертка для удобства использования
class SyncAPIClient:
    """Синхронная обертка для APIClient"""

    @staticmethod
    def get_currency_rates(currencies: List[str]) -> List[Dict[str, float]]:
        async def _fetch():
            async with APIClient() as client:
                return await client.get_currency_rates(currencies)

        return asyncio.run(_fetch())

    @staticmethod
    def get_stock_prices(stocks: List[str]) -> List[Dict[str, float]]:
        async def _fetch():
            async with APIClient() as client:
                return await client.get_stock_prices(stocks)

        return asyncio.run(_fetch())

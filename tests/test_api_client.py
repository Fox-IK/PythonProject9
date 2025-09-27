
import pytest
from unittest.mock import AsyncMock, patch
import asyncio


class TestAPIClient:
    @pytest.mark.asyncio
    async def test_get_currency_rates(self):
        async with AsyncMock() as mock_session:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                from src.api_client import APIClient
                client = APIClient()
                client.session = mock_session

                # Мок успешного ответа
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "rates": {"USD": 0.0107, "EUR": 0.0099},
                    "base": "RUB"
                }
                mock_session.get.return_value.__aenter__.return_value = mock_response

                rates = await client.get_currency_rates(["USD", "EUR"])
                # Ожидаем только запрошенные валюты, RUB не должен включаться если не запрошен
                assert len(rates) == 2
                assert any(rate['currency'] == 'USD' for rate in rates)
                assert any(rate['currency'] == 'EUR' for rate in rates)

    @pytest.mark.asyncio
    async def test_get_currency_rates_fallback(self):
        async with AsyncMock() as mock_session:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                from src.api_client import APIClient
                client = APIClient()
                client.session = mock_session

                # Мок неудачного ответа
                mock_response = AsyncMock()
                mock_response.status = 500
                mock_session.get.return_value.__aenter__.return_value = mock_response

                rates = await client.get_currency_rates(["USD", "EUR"])
                # Fallback должен вернуть только запрошенные валюты
                assert len(rates) == 2
                assert all(rate['rate'] > 0 for rate in rates)

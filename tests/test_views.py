# tests/test_views.py
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import DataProcessor, events_page, main_page


class TestViews:
    @pytest.fixture
    def sample_transactions(self):
        """Фикстура с корректными тестовыми данными"""
        return pd.DataFrame({
            'Дата операции': pd.to_datetime(['2023-12-01', '2023-12-05', '2023-12-10', '2023-12-15']),
            'Номер карты': ['1234567812345814', '1234567812345814', '1234567812347512', '1234567812347512'],
            'Статус': ['OK', 'OK', 'OK', 'OK'],
            'Сумма операции': [1000.0, 500.0, 300.0, 200.0],  # Все расходы (положительные)
            'Категория': ['Супермаркеты', 'Фастфуд', 'Транспорт', 'Развлечения'],
            'Описание': ['Магазин', 'Кафе', 'Такси', 'Кино'],
            'Сумма платежа': [1000.0, 500.0, 300.0, 200.0]
        })

    @pytest.fixture
    def sample_settings(self):
        return {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN"],
            "cashback_rules": {"default": 0.01}
        }

    @patch('src.views.SyncAPIClient.get_currency_rates')
    @patch('src.views.SyncAPIClient.get_stock_prices')
    def test_main_page(self, mock_stocks, mock_currency, sample_transactions, sample_settings):
        mock_currency.return_value = [{"currency": "USD", "rate": 93.45}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 178.72}]

        with patch('src.views.load_transactions', return_value=sample_transactions):
            with patch('src.views.load_user_settings', return_value=sample_settings):
                result = main_page('2023-12-20 15:30:00')

        assert 'greeting' in result
        assert 'cards' in result
        assert 'top_transactions' in result
        assert 'currency_rates' in result
        assert 'stock_prices' in result
        assert result['greeting'] == 'Добрый день'

    def test_data_processor(self, sample_transactions, sample_settings):
        processor = DataProcessor()

        result = processor.process_main_page_data(
            sample_transactions, '2023-12-20 15:30:00', sample_settings
        )

        # Теперь должно быть 2 карты с расходами (обе карты имеют расходы)
        assert len(result['cards']) == 2
        assert len(result['top_transactions']) == 4

        # Проверяем расчет кешбэка
        # Карта 5814: 1000 + 500 = 1500 * 1% = 15.0
        # Карта 7512: 300 + 200 = 500 * 1% = 5.0

        # Находим карты по last_digits
        card_5814 = next(card for card in result['cards'] if card['last_digits'] == '5814')
        card_7512 = next(card for card in result['cards'] if card['last_digits'] == '7512')

        assert card_5814['total_spent'] == 1500.0
        assert card_5814['cashback'] == 15.0
        assert card_7512['total_spent'] == 500.0
        assert card_7512['cashback'] == 5.0

    @patch('src.views.SyncAPIClient.get_currency_rates')
    @patch('src.views.SyncAPIClient.get_stock_prices')
    def test_events_page(self, mock_stocks, mock_currency, sample_transactions, sample_settings):
        mock_currency.return_value = [{"currency": "USD", "rate": 93.45}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 178.72}]

        with patch('src.views.load_transactions', return_value=sample_transactions):
            with patch('src.views.load_user_settings', return_value=sample_settings):
                result = events_page('2023-12-20', 'M')

        assert 'expenses' in result
        assert 'income' in result
        # Все операции расходы, поэтому income = 0
        assert result['expenses']['total_amount'] == 2000  # 1000+500+300+200
        assert result['income']['total_amount'] == 0  # Нет отрицательных сумм

import pytest
import pandas as pd
from datetime import datetime, timedelta
import os

@pytest.fixture
def sample_transactions():
    """Фикстура с примером транзакций"""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    return pd.DataFrame({
        'Дата операции': dates[:100],
        'Номер карты': ['1234567812345814'] * 50 + ['1234567812347512'] * 50,
        'Статус': ['OK'] * 100,
        'Сумма операции': [1000.0, 500.0] * 50,
        'Категория': ['Супермаркеты', 'Фастфуд'] * 50,
        'Описание': [f'Транзакция {i}' for i in range(100)],
        'Сумма платежа': [1000.0, 500.0] * 50
    })

@pytest.fixture
def sample_settings():
    """Фикстура с настройками"""
    return {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN"],
        "cashback_rules": {
            "Супермаркеты": 0.05,
            "Фастфуд": 0.03,
            "default": 0.01
        }
    }

@pytest.fixture(autouse=True)
def setup_teardown():
    """Фикстура для настройки перед каждым тестом"""
    # Настройка перед тестом
    yield
    # Очистка после теста
import pytest
import pandas as pd
from datetime import datetime
from src.views import home_page
from src.utils import get_greeting


@pytest.fixture
def sample_transactions():
    """Фикстура с тестовыми транзакциями."""
    return pd.DataFrame({
        'Дата операции': ['2023-12-01', '2023-12-15', '2023-11-20'],
        'Номер карты': ['1234567812345678', '1234567812345678', '8765432187654321'],
        'Сумма операции': [1000.0, 500.0, 2000.0],
        'Категория': ['Супермаркеты', 'Кафе', 'Транспорт'],
        'Описание': ['Покупка в магазине', 'Обед в кафе', 'Такси']
    })


@pytest.fixture
def user_settings():
    """Фикстура с настройками пользователя."""
    return {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "GOOGL"]
    }


def test_home_page(sample_transactions, user_settings):
    """Тест главной страницы."""
    result = home_page("2023-12-20 15:30:00", sample_transactions, user_settings)

    assert "greeting" in result
    assert "cards" in result
    assert "top_transactions" in result
    assert len(result["cards"]) > 0


@pytest.mark.parametrize("time_str,expected_greeting", [
    ("2023-12-20 08:30:00", "Доброе утро"),
    ("2023-12-20 14:30:00", "Добрый день"),
    ("2023-12-20 20:30:00", "Добрый вечер"),
    ("2023-12-20 02:30:00", "Доброй ночи"),
])
def test_get_greeting(time_str, expected_greeting):
    """Тест получения приветствия."""
    assert get_greeting(time_str) == expected_greeting

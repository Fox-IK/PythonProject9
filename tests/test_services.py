import pytest
from src.services import investment_bank, simple_search


@pytest.fixture
def sample_transactions_list():
    """Фикстура с тестовыми транзакциями в формате списка."""
    return [
        {
            'Дата операции': '2023-12-01',
            'Сумма операции': 1712.0,
            'Категория': 'Магазин',
            'Описание': 'Покупка товаров'
        },
        {
            'Дата операции': '2023-12-15',
            'Сумма операции': 500.0,
            'Категория': 'Кафе',
            'Описание': 'Обед'
        }
    ]


def test_investment_bank(sample_transactions_list):
    """Тест расчета инвесткопилки."""
    savings = investment_bank("2023-12", sample_transactions_list, 50)
    assert savings >= 0


def test_simple_search(sample_transactions_list):
    """Тест простого поиска."""
    # Исправляем порядок аргументов: сначала транзакции, потом строка поиска
    results = simple_search(sample_transactions_list, "кафе")
    assert len(results) == 1
    assert results[0]['Категория'] == 'Кафе'

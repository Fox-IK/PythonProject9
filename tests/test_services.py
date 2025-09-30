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


import pytest
from unittest.mock import patch
from src.services import (
    profitable_cashback_categories,
    investment_bank,
    simple_search,
    search_by_phone,
    search_by_person_transfers,
    CashbackAnalyzer,
    InvestmentCalculator,
    TransactionSearcher,
    compose,
    pipe,
    log_service_call
)
import pandas as pd
from datetime import datetime


class TestCashbackAnalyzer:
    """Тесты для анализатора кешбэка"""

    def test_analyze_profitable_categories(self):
        """Тест анализа выгодных категорий"""
        analyzer = CashbackAnalyzer({'Супермаркеты': 0.05, 'default': 0.01})

        # Создаем тестовые данные
        data = pd.DataFrame({
            'Дата операции': pd.to_datetime(['2023-12-01', '2023-12-05']),
            'Статус': ['OK', 'OK'],
            'Сумма операции': [1000.0, 2000.0],
            'Категория': ['Супермаркеты', 'Фастфуд']
        })

        result = analyzer.analyze_profitable_categories(data, 2023, 12)

        assert 'Супермаркеты' in result
        assert 'Фастфуд' in result
        assert result['Супермаркеты'] == 50.0  # 5% от 1000
        assert result['Фастфуд'] == 20.0  # 1% от 2000

    def test_analyze_profitable_categories_no_data(self):
        """Тест анализа без данных"""
        analyzer = CashbackAnalyzer({'default': 0.01})

        # Пустые данные
        data = pd.DataFrame(columns=['Дата операции', 'Статус', 'Сумма операции', 'Категория'])

        result = analyzer.analyze_profitable_categories(data, 2023, 12)

        assert result == {}

    def test_analyze_profitable_categories_with_empty_category(self):
        """Тест анализа с пустыми категориями"""
        analyzer = CashbackAnalyzer({'default': 0.01})

        data = pd.DataFrame({
            'Дата операции': pd.to_datetime(['2023-12-01']),
            'Статус': ['OK'],
            'Сумма операции': [1000.0],
            'Категория': ['']
        })

        result = analyzer.analyze_profitable_categories(data, 2023, 12)

        # Пустые категории должны игнорироваться
        assert '' not in result


class TestInvestmentCalculator:
    """Тесты для калькулятора инвесткопилки"""

    def test_investment_bank_valid_transactions(self):
        """Тест расчета с валидными транзакциями"""
        transactions = [
            {
                'Дата операции': '2023-12-01',
                'Сумма операции': '1047.0'  # Округление до 1050 = +3
            },
            {
                'Дата операции': '2023-12-15',
                'Сумма операции': '1982.0'  # Округление до 2000 = +18
            }
        ]

        result = InvestmentCalculator.investment_bank('2023-12', transactions, 50)

        assert result == 21.0  # 3 + 18

    def test_investment_bank_invalid_transaction(self):
        """Тест с невалидной транзакцией"""
        transactions = [
            {'Дата операции': 'invalid-date', 'Сумма операции': 'not-a-number'},
            {'Дата операции': '2023-12-01', 'Сумма операции': '1000.0'}
        ]

        result = InvestmentCalculator.investment_bank('2023-12', transactions, 50)

        # Только вторая транзакция должна учитываться
        assert result == 0.0  # 1000 округляется до 1000 = 0

    def test_validate_transaction_valid(self):
        """Тест валидации корректной транзакции"""
        transaction = {'Дата операции': '2023-12-01', 'Сумма операции': '1000.0'}

        assert InvestmentCalculator._validate_transaction(transaction) is True

    def test_validate_transaction_missing_fields(self):
        """Тест валидации транзакции с отсутствующими полями"""
        transaction = {'Дата операции': '2023-12-01'}  # Нет Сумма операции

        assert InvestmentCalculator._validate_transaction(transaction) is False

    def test_validate_transaction_invalid_data(self):
        """Тест валидации транзакции с невалидными данными"""
        transaction = {'Дата операции': 'invalid-date', 'Сумма операции': 'not-a-number'}

        assert InvestmentCalculator._validate_transaction(transaction) is False


class TestTransactionSearcher:
    """Тесты для поисковика транзакций"""

    @pytest.fixture
    def sample_transactions(self):
        return [
            {'Описание': 'Покупка в магазине', 'Категория': 'Супермаркеты'},
            {'Описание': 'Обед в кафе', 'Категория': 'Фастфуд'},
            {'Описание': 'Перевод Ивану И.', 'Категория': 'Переводы'},
            {'Описание': 'Пополнение +7 921 123-45-67', 'Категория': 'Мобильная связь'}
        ]

    def test_simple_search_by_description(self, sample_transactions):
        """Тест поиска по описанию"""
        results = TransactionSearcher.simple_search(sample_transactions, 'магазин')

        assert len(results) == 1
        assert results[0]['Описание'] == 'Покупка в магазине'

    def test_simple_search_by_category(self, sample_transactions):
        """Тест поиска по категории"""
        results = TransactionSearcher.simple_search(sample_transactions, 'Фастфуд')

        assert len(results) == 1
        assert results[0]['Категория'] == 'Фастфуд'

    def test_simple_search_short_string(self):
        """Тест поиска с короткой строкой"""
        with pytest.raises(ValueError, match="Строка поиска должна содержать минимум 2 символа"):
            TransactionSearcher.simple_search([], 'а')

    def test_search_by_phone(self, sample_transactions):
        """Тест поиска по телефонным номерам"""
        results = TransactionSearcher.search_by_phone(sample_transactions)

        assert len(results) == 1
        assert '+7 921 123-45-67' in results[0]['Описание']

    def test_search_by_person_transfers(self, sample_transactions):
        """Тест поиска переводов физлицам"""
        results = TransactionSearcher.search_by_person_transfers(sample_transactions)

        assert len(results) == 1
        assert results[0]['Категория'] == 'Переводы'
        assert 'Ивану И.' in results[0]['Описание']


class TestFunctionalUtilities:
    """Тесты функциональных утилит"""

    def test_compose(self):
        """Тест композиции функций"""

        def double(x):
            return x * 2

        def square(x):
            return x * x

        composed = compose(double, square)
        result = composed(3)  # square(3) = 9, double(9) = 18

        assert result == 18

class TestServiceDecorators:
    """Тесты декораторов сервисов"""

    def test_log_service_call_success(self):
        """Тест декоратора при успешном выполнении"""

        @log_service_call("test_service")
        def test_function():
            return "success"

        with patch('src.services.logger') as mock_logger:
            result = test_function()

            assert result == "success"
            mock_logger.info.assert_any_call("Вызов сервиса test_service")
            mock_logger.info.assert_any_call("Сервис test_service выполнен успешно")

    def test_log_service_call_exception(self):
        """Тест декоратора при исключении"""

        @log_service_call("test_service")
        def test_function():
            raise ValueError("Test error")

        with patch('src.services.logger') as mock_logger:
            with pytest.raises(ValueError, match="Test error"):
                test_function()

            mock_logger.info.assert_called_once_with("Вызов сервиса test_service")
            mock_logger.error.assert_called_once_with("Ошибка в сервисе test_service: Test error")


# Тесты для основных функций с декораторами
def test_profitable_cashback_categories_integration():
    """Интеграционный тест для profitable_cashback_categories"""
    data = pd.DataFrame({
        'Дата операции': pd.to_datetime(['2023-12-01']),
        'Статус': ['OK'],
        'Сумма операции': [1000.0],
        'Категория': ['Супермаркеты']
    })

    with patch('src.services.logger') as mock_logger:
        result = profitable_cashback_categories(data, 2023, 12, {'Супермаркеты': 0.05})

        assert 'Супермаркеты' in result
        mock_logger.info.assert_called()


def test_investment_bank_integration():
    """Интеграционный тест для investment_bank"""
    transactions = [{'Дата операции': '2023-12-01', 'Сумма операции': '1047.0'}]

    with patch('src.services.logger') as mock_logger:
        result = investment_bank('2023-12', transactions, 50)

        assert result == 3.0
        mock_logger.info.assert_called()
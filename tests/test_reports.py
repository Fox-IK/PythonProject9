import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import json
import os
from unittest.mock import patch, MagicMock

from src.reports import (
    ReportGenerator, spending_by_category, spending_by_weekday,
    spending_by_workday, report_decorator
)


class TestReportGeneratorExtended:
    """Расширенные тесты для ReportGenerator"""

    @pytest.fixture
    def sample_transactions_complex(self):
        """Фикстура с комплексными данными для отчетов"""
        dates = pd.date_range(start='2023-09-01', end='2023-12-31', freq='D')
        return pd.DataFrame({
            'Дата операции': dates,
            'Статус': ['OK'] * len(dates),
            'Категория': ['Супермаркеты'] * 30 + ['Фастфуд'] * 30 + ['Транспорт'] * 30 + ['Развлечения'] * 31,
            'Сумма операции': np.random.uniform(100, 5000, len(dates))
        })

    def test_spending_by_category_empty_data(self):
        """Тест отчета по категориям с пустыми данными"""
        df = pd.DataFrame(columns=['Дата операции', 'Категория', 'Сумма операции', 'Статус'])

        result = ReportGenerator.spending_by_category(df, 'Супермаркеты', '2023-12-20')

        assert result.empty
        assert list(result.columns) == ['Месяц', 'Сумма']

    def test_spending_by_category_no_matching_category(self):
        """Тест отчета по категориям без совпадающих категорий"""
        df = pd.DataFrame({
            'Дата операции': pd.to_datetime(['2023-12-01', '2023-12-02']),
            'Статус': ['OK', 'OK'],
            'Категория': ['Фастфуд', 'Транспорт'],  # Нет Супермаркетов
            'Сумма операции': [1000, 2000]
        })

        result = ReportGenerator.spending_by_category(df, 'Супермаркеты', '2023-12-20')

        assert result.empty

    def test_spending_by_category_only_failed_transactions(self):
        """Тест отчета по категориям только с неудачными транзакциями"""
        df = pd.DataFrame({
            'Дата операции': pd.to_datetime(['2023-12-01', '2023-12-02']),
            'Статус': ['FAILED', 'FAILED'],
            'Категория': ['Супермаркеты', 'Супермаркеты'],
            'Сумма операции': [1000, 2000]
        })

        result = ReportGenerator.spending_by_category(df, 'Супермаркеты', '2023-12-20')

        assert result.empty

    def test_spending_by_category_only_income(self):
        """Тест отчета по категориям только с доходами"""
        df = pd.DataFrame({
            'Дата операции': pd.to_datetime(['2023-12-01', '2023-12-02']),
            'Статус': ['OK', 'OK'],
            'Категория': ['Супермаркеты', 'Супермаркеты'],
            'Сумма операции': [-1000, -2000]  # Доходы
        })

        result = ReportGenerator.spending_by_category(df, 'Супермаркеты', '2023-12-20')

        assert result.empty

    def test_spending_by_category_different_months(self):
        """Тест отчета по категориям за несколько месяцев"""
        df = pd.DataFrame({
            'Дата операции': pd.to_datetime(['2023-10-15', '2023-11-15', '2023-12-15']),
            'Статус': ['OK', 'OK', 'OK'],
            'Категория': ['Супермаркеты', 'Супермаркеты', 'Супермаркеты'],
            'Сумма операции': [1000, 2000, 3000]
        })

        result = ReportGenerator.spending_by_category(df, 'Супермаркеты', '2023-12-20')

        # Должны быть данные за 3 месяца (октябрь, ноябрь, декабрь)
        assert len(result) == 3
        assert set(result['Месяц']) == {'2023-10', '2023-11', '2023-12'}
        assert result['Сумма'].sum() == 6000

    def test_spending_by_weekday_empty_data(self):
        """Тест отчета по дням недели с пустыми данными"""
        df = pd.DataFrame(columns=['Дата операции', 'Сумма операции', 'Статус'])

        result = ReportGenerator.spending_by_weekday(df, '2023-12-20')

        assert result.empty
        assert list(result.columns) == ['День недели', 'Средняя сумма']

    def test_spending_by_weekday_correct_ordering(self):
        """Тест правильного порядка дней недели в отчете"""
        df = pd.DataFrame({
            'Дата операции': pd.to_datetime([
                '2023-12-18', '2023-12-19', '2023-12-20',  # Пн, Вт, Ср
                '2023-12-21', '2023-12-22', '2023-12-23', '2023-12-24'  # Чт, Пт, Сб, Вс
            ]),
            'Статус': ['OK'] * 7,
            'Сумма операции': [100, 200, 300, 400, 500, 600, 700]
        })

        result = ReportGenerator.spending_by_weekday(df, '2023-12-24')

        # Проверяем порядок дней недели
        expected_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        assert list(result['День недели']) == expected_order

        # Проверяем средние значения (в данном случае они равны суммам, так по одной транзакции на день)
        assert list(result['Средняя сумма']) == [100, 200, 300, 400, 500, 600, 700]

    def test_spending_by_workday_empty_data(self):
        """Тест отчета по рабочим/выходным с пустыми данными"""
        df = pd.DataFrame(columns=['Дата операции', 'Сумма операции', 'Статус'])

        result = ReportGenerator.spending_by_workday(df, '2023-12-20')

        assert result.empty
        assert list(result.columns) == ['Тип дня', 'Средняя сумма']

    def test_spending_by_workday_correct_classification(self):
        """Тест правильной классификации рабочих и выходных дней"""
        df = pd.DataFrame({
            'Дата операции': pd.to_datetime([
                '2023-12-18', '2023-12-19', '2023-12-20',  # Пн, Вт, Ср - рабочие
                '2023-12-23', '2023-12-24'  # Сб, Вс - выходные
            ]),
            'Статус': ['OK'] * 5,
            'Сумма операции': [100, 200, 300, 400, 500]
        })

        result = ReportGenerator.spending_by_workday(df, '2023-12-24')

        assert len(result) == 2

        workday_data = result[result['Тип дня'] == 'Рабочий']
        weekend_data = result[result['Тип дня'] == 'Выходной']

        # Средняя за рабочие дни: (100 + 200 + 300) / 3 = 200
        assert workday_data['Средняя сумма'].iloc[0] == 200.0
        # Средняя за выходные: (400 + 500) / 2 = 450
        assert weekend_data['Средняя сумма'].iloc[0] == 450.0

    def test_monthly_summary_empty_data(self):
        """Тест сводного отчета с пустыми данными"""
        df = pd.DataFrame(columns=['Дата операции', 'Сумма операции', 'Статус', 'Категория'])

        result = ReportGenerator.monthly_summary(df, 6)

        assert 'error' in result
        assert result['error'] == "Нет данных за указанный период"


class TestReportDecorator:
    """Тесты декоратора отчетов"""

    def test_report_decorator_with_filename(self, tmp_path):
        """Тест декоратора с указанием имени файла"""
        test_filename = tmp_path / "test_report.json"

        @report_decorator(filename=str(test_filename))
        def test_function():
            return {"test": "data"}

        result = test_function()

        assert result == {"test": "data"}
        assert test_filename.exists()

        with open(test_filename, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == {"test": "data"}

    def test_report_decorator_with_dataframe(self, tmp_path):
        """Тест декоратора с DataFrame"""

        @report_decorator()
        def test_function():
            return pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})

        with patch('src.reports.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 12, 20, 15, 30, 0)

            result = test_function()

            # Проверяем, что функция возвращает правильный результат
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2

    def test_report_decorator_exception(self, tmp_path):
        """Тест декоратора при исключении в функции"""

        @report_decorator(filename=str(tmp_path / "error_report.json"))
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Файл не должен быть создан при исключении
        assert not (tmp_path / "error_report.json").exists()


class TestReportsFunctions:
    """Тесты функций-оберток отчетов"""

    def test_spending_by_category_wrapper(self):
        """Тест обертки spending_by_category"""
        with patch('src.reports.ReportGenerator.spending_by_category') as mock_method:
            mock_method.return_value = pd.DataFrame({'test': [1, 2, 3]})

            df = pd.DataFrame()
            result = spending_by_category(df, 'Супермаркеты', '2023-12-20')

            assert isinstance(result, pd.DataFrame)
            mock_method.assert_called_once_with(df, 'Супермаркеты', '2023-12-20')

    def test_spending_by_weekday_wrapper(self):
        """Тест обертки spending_by_weekday"""
        with patch('src.reports.ReportGenerator.spending_by_weekday') as mock_method:
            mock_method.return_value = pd.DataFrame({'test': [1, 2, 3]})

            df = pd.DataFrame()
            result = spending_by_weekday(df, '2023-12-20')

            assert isinstance(result, pd.DataFrame)
            mock_method.assert_called_once_with(df, '2023-12-20')

    def test_spending_by_workday_wrapper(self):
        """Тест обертки spending_by_workday"""
        with patch('src.reports.ReportGenerator.spending_by_workday') as mock_method:
            mock_method.return_value = pd.DataFrame({'test': [1, 2, 3]})

            df = pd.DataFrame()
            result = spending_by_workday(df, '2023-12-20')

            assert isinstance(result, pd.DataFrame)
            mock_method.assert_called_once_with(df, '2023-12-20')
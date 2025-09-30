from unittest.mock import MagicMock, patch

import pytest

from src.main import TransactionAnalyzer, main


class TestTransactionAnalyzer:
    """Тесты для основного класса приложения"""

    @pytest.fixture
    def analyzer(self):
        return TransactionAnalyzer()

    def test_initialization(self, analyzer):
        """Тест инициализации анализатора"""
        assert analyzer.data_file is not None
        assert analyzer.transactions_df is None
        assert analyzer.settings is None

    @patch('src.views.main_page')
    def test_generate_main_page(self, mock_main_page, analyzer):
        """Тест генерации главной страницы"""
        # Мокируем данные
        analyzer.transactions_df = MagicMock()
        analyzer.settings = MagicMock()
        expected_result = {'greeting': 'Добрый день'}
        mock_main_page.return_value = expected_result

        # Генерируем страницу
        result = analyzer.generate_main_page('2023-12-20 15:30:00')

        # Проверяем
        assert result == expected_result
        mock_main_page.assert_called_once_with('2023-12-20 15:30:00', 'data/operations.xlsx')

    @patch('src.views.events_page')
    def test_generate_events_page(self, mock_events_page, analyzer):
        """Тест генерации страницы событий"""
        # Мокируем данные
        analyzer.transactions_df = MagicMock()
        analyzer.settings = MagicMock()
        expected_result = {'expenses': {'total_amount': 1000}}
        mock_events_page.return_value = expected_result

        # Генерируем страницу
        result = analyzer.generate_events_page('2023-12-20', 'M')

        # Проверяем
        assert result == expected_result
        mock_events_page.assert_called_once_with('2023-12-20', 'M', 'data/operations.xlsx')

    @patch('src.services.profitable_cashback_categories')
    def test_analyze_cashback_categories(self, mock_cashback, analyzer):
        """Тест анализа кешбэка"""
        # Мокируем данные
        analyzer.transactions_df = MagicMock()
        analyzer.settings = {'cashback_rules': {'default': 0.01}}
        expected_result = {'Супермаркеты': 150.0}
        mock_cashback.return_value = expected_result

        # Анализируем
        result = analyzer.analyze_cashback_categories(2023, 12)

        # Проверяем
        assert result == expected_result
        mock_cashback.assert_called_once()

    @patch('src.services.investment_bank')
    def test_calculate_investment(self, mock_investment, analyzer):
        """Тест расчета инвесткопилки"""
        # Мокируем данные
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [{'Дата операции': '2023-12-01', 'Сумма операции': 1000}]
        analyzer.transactions_df = mock_df
        mock_investment.return_value = 50.0

        # Рассчитываем
        result = analyzer.calculate_investment('2023-12', 50)

        # Проверяем
        assert result == 50.0
        mock_investment.assert_called_once()

    @patch('src.services.simple_search')
    def test_search_transactions(self, mock_search, analyzer):
        """Тест поиска транзакций"""
        # Мокируем данные
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [{'Описание': 'Магазин'}]
        analyzer.transactions_df = mock_df
        mock_search.return_value = [{'Описание': 'Магазин'}]

        # Ищем
        result = analyzer.search_transactions('магазин')

        # Проверяем
        assert len(result) == 1
        mock_search.assert_called_once()

    @patch('src.reports.ReportGenerator')
    def test_generate_reports(self, mock_report_generator, analyzer):
        """Тест генерации отчетов"""
        # Мокируем данные
        analyzer.transactions_df = MagicMock()
        mock_report_generator.spending_by_category.return_value = MagicMock()
        mock_report_generator.spending_by_weekday.return_value = MagicMock()
        mock_report_generator.spending_by_workday.return_value = MagicMock()
        mock_report_generator.monthly_summary.return_value = {'total': 1000}

        # Генерируем отчеты
        reports = analyzer.generate_reports()

        # Проверяем
        assert 'spending_by_category' in reports
        assert 'monthly_summary' in reports
        assert mock_report_generator.spending_by_category.call_count == 1


class TestMainFunction:
    """Тесты для основной функции"""

    @patch('src.main.TransactionAnalyzer')
    @patch('builtins.print')
    def test_main_web_command(self, mock_print, mock_analyzer):
        """Тест main с командой web"""
        # Мокируем анализатор
        mock_instance = MagicMock()
        mock_instance.load_data.return_value = None
        mock_instance.generate_main_page.return_value = {'greeting': 'Добрый день'}
        mock_instance.generate_events_page.return_value = {'expenses': {'total_amount': 1000}}
        mock_analyzer.return_value = mock_instance

        # Запускаем с командой web
        with patch('sys.argv', ['main.py', '--command', 'web']):
            main()

        # Проверяем вызовы
        mock_instance.load_data.assert_called_once()
        mock_instance.generate_main_page.assert_called_once()
        mock_instance.generate_events_page.assert_called_once()

    @patch('src.main.TransactionAnalyzer')
    @patch('builtins.print')
    def test_main_report_command(self, mock_print, mock_analyzer):
        """Тест main с командой report"""
        # Мокируем анализатор
        mock_instance = MagicMock()
        mock_instance.load_data.return_value = None
        mock_instance.generate_reports.return_value = {
            'monthly_summary': {'total': 1000}
        }
        mock_analyzer.return_value = mock_instance

        # Запускаем с командой report
        with patch('sys.argv', ['main.py', '--command', 'report']):
            main()

        # Проверяем вызовы
        mock_instance.load_data.assert_called_once()
        mock_instance.generate_reports.assert_called_once()

    @patch('src.main.TransactionAnalyzer')
    @patch('builtins.print')
    def test_main_analyze_command(self, mock_print, mock_analyzer):
        """Тест main с командой analyze"""
        # Мокируем анализатор
        mock_instance = MagicMock()
        mock_instance.load_data.return_value = None
        mock_instance.analyze_cashback_categories.return_value = {'Категория': 100}
        mock_instance.calculate_investment.return_value = 50.0
        mock_analyzer.return_value = mock_instance

        # Запускаем с командой analyze
        with patch('sys.argv', ['main.py', '--command', 'analyze']):
            main()

        # Проверяем вызовы
        mock_instance.load_data.assert_called_once()
        mock_instance.analyze_cashback_categories.assert_called_once()
        mock_instance.calculate_investment.assert_called_once()

    @patch('src.main.TransactionAnalyzer')
    @patch('builtins.print')
    def test_main_test_command(self, mock_print, mock_analyzer):
        """Тест main с командой test"""
        # Мокируем анализатор
        mock_instance = MagicMock()
        mock_instance.load_data.return_value = None
        mock_instance.transactions_df = MagicMock()
        mock_instance.settings = {'user_currencies': ['USD']}
        mock_instance.search_transactions.return_value = [{'Описание': 'Магазин'}]
        mock_analyzer.return_value = mock_instance

        # Запускаем с командой test
        with patch('sys.argv', ['main.py', '--command', 'test']):
            main()

        # Проверяем вызовы
        mock_instance.load_data.assert_called_once()
        mock_instance.search_transactions.assert_called_once()

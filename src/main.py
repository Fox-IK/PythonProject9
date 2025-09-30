#!/usr/bin/env python3
"""
Основной модуль приложения для анализа транзакций
"""
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

# Создаем необходимые директории
Path('logs').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)
Path('data').mkdir(exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/transaction_analyzer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TransactionAnalyzer:
    """Основной класс приложения"""

    def __init__(self, data_file: str = None):
        from src.config import settings
        self.data_file = data_file or settings.data_file_path
        self.transactions_df = None
        self.settings = None

    def load_data(self):
        """Загрузка данных"""
        from src.utils import load_transactions, load_user_settings
        logger.info("Загрузка данных...")
        self.transactions_df = load_transactions(self.data_file)
        self.settings = load_user_settings()
        logger.info("Данные успешно загружены")

    def generate_main_page(self, date_time: str) -> dict:
        """Генерация данных для главной страницы"""
        from src.views import main_page
        return main_page(date_time, self.data_file)

    def generate_events_page(self, date: str, period: str = 'M') -> dict:
        """Генерация данных для страницы событий"""
        from src.views import events_page
        return events_page(date, period, self.data_file)

    def analyze_cashback_categories(self, year: int, month: int) -> dict:
        """Анализ выгодных категорий кешбэка"""
        from src.services import profitable_cashback_categories
        cashback_rules = self.settings.get('cashback_rules', {'default': 0.01})
        return profitable_cashback_categories(
            self.transactions_df, year, month, cashback_rules
        )

    def calculate_investment(self, month: str, limit: int) -> float:
        """Расчет инвесткопилки"""
        from src.services import investment_bank
        transactions_list = self.transactions_df.to_dict('records')
        return investment_bank(month, transactions_list, limit)

    def search_transactions(self, search_string: str) -> list:
        """Поиск транзакций"""
        from src.services import simple_search
        transactions_list = self.transactions_df.to_dict('records')
        return simple_search(transactions_list, search_string)

    def generate_reports(self):
        """Генерация всех отчетов"""
        from src.reports import ReportGenerator  # Добавлен импорт

        reports = {'spending_by_category': ReportGenerator.spending_by_category(
            self.transactions_df, 'Супермаркеты'
        ), 'spending_by_weekday': ReportGenerator.spending_by_weekday(
            self.transactions_df
        ), 'spending_by_workday': ReportGenerator.spending_by_workday(
            self.transactions_df
        ), 'monthly_summary': ReportGenerator.monthly_summary(
            self.transactions_df
        )}

        # Отчет по категориям

        # Отчет по дням недели

        # Отчет по рабочим/выходным дням

        # Сводный отчет

        return reports


def main():
    """Основная функция приложения"""
    parser = argparse.ArgumentParser(description='Анализатор банковских транзакций')
    parser.add_argument('--data-file', help='Путь к файлу с транзакциями')
    parser.add_argument('--command', choices=['web', 'report', 'analyze', 'test'],
                        default='web', help='Режим работы')

    args = parser.parse_args()

    try:
        # Инициализация анализатора
        analyzer = TransactionAnalyzer(args.data_file)
        analyzer.load_data()

        if args.command == 'web':
            # Пример генерации данных для веб-страниц
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            main_data = analyzer.generate_main_page(current_time)
            events_data = analyzer.generate_events_page(current_time.split()[0])

            print("=== ДАННЫЕ ДЛЯ ГЛАВНОЙ СТРАНИЦЫ ===")
            print(json.dumps(main_data, ensure_ascii=False, indent=2))

            print("\n=== ДАННЫЕ ДЛЯ СТРАНИЦЫ СОБЫТИЙ ===")
            print(json.dumps(events_data, ensure_ascii=False, indent=2))

        elif args.command == 'report':
            # Генерация отчетов
            reports = analyzer.generate_reports()
            print("=== ОТЧЕТЫ СГЕНЕРИРОВАНЫ ===")

            for report_name, report_data in reports.items():
                print(f"\n--- {report_name} ---")
                if isinstance(report_data, dict):
                    print(json.dumps(report_data, ensure_ascii=False, indent=2))
                elif hasattr(report_data, 'head'):  # DataFrame
                    print(report_data.head())
                else:
                    print(f"Тип данных: {type(report_data)}")
                    print(report_data)

            print("\n Отчеты сохранены в папке 'reports/'")

        elif args.command == 'analyze':
            # Анализ данных
            current_year = datetime.now().year
            current_month = datetime.now().month

            cashback_analysis = analyzer.analyze_cashback_categories(current_year, current_month)
            investment = analyzer.calculate_investment(
                f"{current_year}-{current_month:02d}", 50
            )

            print("=== АНАЛИЗ ДАННЫХ ===")
            print(f"Выгодные категории кешбэка: {cashback_analysis}")
            print(f"Инвесткопилка за месяц: {investment} руб.")

        elif args.command == 'test':
            # Простой тест функциональности
            print("=== ТЕСТ ФУНКЦИОНАЛЬНОСТИ ===")
            print(f"Загружено транзакций: {len(analyzer.transactions_df)}")
            print(f"Настройки: {list(analyzer.settings.keys())}")

            # Тест поиска
            search_results = analyzer.search_transactions("магазин")
            print(f"Результатов поиска 'магазин': {len(search_results)}")

    except Exception as e:
        logger.error(f"Ошибка приложения: {e}")
        raise


if __name__ == "__main__":
    main()

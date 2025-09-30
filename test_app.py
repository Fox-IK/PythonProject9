#!/usr/bin/env python3
"""
Простой скрипт для тестирования приложения
"""

import sys
from pathlib import Path

# Добавляем src в путь Python
sys.path.insert(0, str(Path(__file__).parent))

# Создаем необходимые директории
Path('logs').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)
Path('data').mkdir(exist_ok=True)


def test_basic_functionality():
    """Тест базовой функциональности"""
    try:
        print("🧪 Тестирование Transaction Analyzer...")

        # Импортируем модули
        from src.reports import ReportGenerator
        from src.utils import load_transactions, load_user_settings
        from src.views import events_page, main_page

        # 1. Загрузка данных
        print("1. Загрузка данных...")
        df = load_transactions()
        settings = load_user_settings()
        print(f"   ✅ Транзакций: {len(df)}")
        print(f"   ✅ Настроек: {len(settings)}")

        # 2. Тест веб-страниц
        print("2. Тест веб-страниц...")
        main_data = main_page("2023-12-20 15:30:00")
        events_data = events_page("2023-12-20", "M")
        print(f"   ✅ Главная страница: {main_data['greeting']}")
        print(f"   ✅ Страница событий: расходы {events_data['expenses']['total_amount']}")

        # 3. Тест отчетов
        print("3. Тест отчетов...")
        report = ReportGenerator.spending_by_category(df, "Супермаркеты")
        print(f"   ✅ Отчет по категории: {len(report)} записей")

        # 4. Тест сервисов
        print("4. Тест сервисов...")
        from src.services import simple_search
        transactions_list = df.head(10).to_dict('records')
        results = simple_search(transactions_list, "магазин")
        print(f"   ✅ Поиск: {len(results)} результатов")

        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_basic_functionality()

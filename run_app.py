#!/usr/bin/env python3
"""
Упрощенный запуск приложения
"""

import os
import sys
from pathlib import Path

# Добавляем src в путь Python
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Создаем необходимые директории
Path('logs').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)
Path('data').mkdir(exist_ok=True)


def main():
    """Основная функция"""
    try:
        from src.views import main_page, events_page
        from src.utils import load_transactions, load_user_settings

        print("🚀 Запуск Transaction Analyzer...")

        # Загрузка данных
        df = load_transactions()
        settings = load_user_settings()

        # Генерация данных для веб-страниц
        current_time = "2023-12-20 15:30:00"

        print("\n=== ГЛАВНАЯ СТРАНИЦА ===")
        main_data = main_page(current_time)
        print(f"Приветствие: {main_data['greeting']}")
        print(f"Карты: {len(main_data['cards'])}")
        print(f"Топ транзакций: {len(main_data['top_transactions'])}")

        print("\n=== СТРАНИЦА СОБЫТИЙ ===")
        events_data = events_page("2023-12-20", "M")
        print(f"Расходы: {events_data['expenses']['total_amount']}")
        print(f"Поступления: {events_data['income']['total_amount']}")

        print("\n✅ Приложение успешно запущено!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
import json
import pandas as pd
from .utils import load_transactions
from .views import home_page
from .services import investment_bank, simple_search, find_phone_transactions
from .reports import spending_by_category, spending_by_weekday


def main():
    """Основная функция приложения."""
    try:
        # Загрузка данных
        transactions_df = load_transactions('data/operations.xlsx')

        # Загрузка настроек пользователя
        with open('user_settings.json', 'r') as f:
            user_settings = json.load(f)

        # Демонстрация функциональности
        print("=== Анализатор транзакций ===")

        # Главная страница
        home_data = home_page("2023-12-20 15:30:00", transactions_df, user_settings)
        print("Главная страница сгенерирована")

        # Конвертация DataFrame в список словарей для сервисов
        transactions_list = transactions_df.to_dict('records')

        # Сервисы
        savings = investment_bank("2023-12", transactions_list, 50)
        print(f"Инвесткопилка: {savings} руб.")

        search_results = simple_search("кафе", transactions_list)
        print(f"Найдено транзакций по запросу 'кафе': {len(search_results)}")

        phone_transactions = find_phone_transactions(transactions_list)
        print(f"Найдено транзакций с телефонами: {len(phone_transactions)}")

        # Отчеты
        category_spending = spending_by_category(transactions_df, "Супермаркеты")
        print("Отчет по тратам по категории создан")

        weekday_spending = spending_by_weekday(transactions_df)
        print("Отчет по тратам по дням недели создан")

        print("\nВсе функции выполнены успешно!")

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()

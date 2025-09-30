"""
Скрипт для генерации тестовых данных
"""

import random
from datetime import datetime, timedelta

import pandas as pd


def generate_sample_data(num_records: int = 1000) -> pd.DataFrame:
    """Генерация тестовых данных транзакций"""

    # Категории транзакций
    categories = [
        'Супермаркеты', 'Фастфуд', 'Транспорт', 'Развлечения',
        'Одежда', 'Электроника', 'Здоровье', 'Образование',
        'Переводы', 'Наличные', 'Зарплата', 'Инвестиции'
    ]

    # Статусы операций
    statuses = ['OK', 'FAILED', 'PENDING']

    # Номера карт
    cards = ['1234567812345814', '1234567812347512', '1234567812340923']

    # Генерация дат
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    date_range = (end_date - start_date).days

    data = []
    for i in range(num_records):
        # Случайная дата в 2023 году
        random_days = random.randint(0, date_range)
        operation_date = start_date + timedelta(days=random_days)
        payment_date = operation_date + timedelta(days=random.randint(0, 30))

        # Случайная сумма (большинство - расходы, некоторые - доходы)
        is_income = random.random() < 0.2  # 20% доходы
        amount = round(random.uniform(100, 50000), 2)
        if is_income:
            amount = -amount

        transaction = {
            'Дата операции': operation_date.strftime('%d.%m.%Y'),
            'Дата платежа': payment_date.strftime('%d.%m.%Y'),
            'Номер карты': random.choice(cards),
            'Статус': random.choices(statuses, weights=[0.85, 0.1, 0.05])[0],
            'Сумма операции': amount,
            'Валюта операции': 'RUB',
            'Сумма платежа': amount,
            'Валюта платежа': 'RUB',
            'Кешбэк': round(abs(amount) * 0.01, 2) if amount > 0 and random.random() < 0.7 else 0,
            'Категория': random.choice(categories),
            'MCC': random.randint(1000, 9999),
            'Описание': f'Транзакция #{i + 1}',
            'Бонусы (включая кешбэк)': round(abs(amount) * 0.005, 2) if amount > 0 else 0,
            'Округление на «Инвесткопилку»': random.randint(0, 50),
            'Сумма операции с округлением': round(amount / 50) * 50 if amount > 0 else amount
        }

        data.append(transaction)

    return pd.DataFrame(data)


if __name__ == "__main__":
    # Генерация тестовых данных
    df = generate_sample_data(1000)
    df.to_excel('data/operations.xlsx', index=False)
    print("Тестовые данные сохранены в data/operations.xlsx")

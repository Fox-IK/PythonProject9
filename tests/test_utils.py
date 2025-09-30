# tests/test_utils.py
import json
import os
import tempfile
from datetime import datetime

import pandas as pd

from src.utils import DataValidator, calculate_cashback, get_date_range, get_greeting, load_user_settings


class TestUtils:
    def test_get_greeting(self):
        assert get_greeting('2023-12-20 08:30:00') == 'Доброе утро'
        assert get_greeting('2023-12-20 14:30:00') == 'Добрый день'
        assert get_greeting('2023-12-20 20:30:00') == 'Добрый вечер'
        assert get_greeting('2023-12-20 02:30:00') == 'Доброй ночи'

    def test_get_date_range(self):
        start, end = get_date_range('2023-12-20 15:30:00', 'M')
        assert start == datetime(2023, 12, 1, 0, 0, 0)  # Исправлено: добавили время
        assert end == datetime(2023, 12, 20, 15, 30, 0)

        start, end = get_date_range('2023-12-20', 'W')
        assert start.weekday() == 0  # Понедельник
        assert end.weekday() == 6  # Воскресенье

    def test_calculate_cashback(self):
        cashback_rules = {
            'Супермаркеты': 0.05,
            'default': 0.01
        }

        # Базовая логика
        assert calculate_cashback(1000, 'Супермаркеты', cashback_rules) == 50.0
        assert calculate_cashback(1000, 'Другое', cashback_rules) == 10.0

        # Бонус за большие покупки - ИСПРАВЛЕНО ожидание
        # 6000 * (5% + 1%) = 6000 * 0.06 = 360.0
        assert calculate_cashback(6000, 'Супермаркеты', cashback_rules) == 360.0
        # 11000 * (5% + 2%) = 11000 * 0.07 = 770.0
        assert calculate_cashback(11000, 'Супермаркеты', cashback_rules) == 770.0

        # Ограничение максимального кешбэка
        high_cashback_rules = {'default': 0.20}
        assert calculate_cashback(1000, 'Тест', high_cashback_rules) == 150.0  # Максимум 15%

    def test_data_validator(self):
        validator = DataValidator()

        # Тестовые данные с корректными данными
        test_data = pd.DataFrame({
            'Дата операции': ['15.01.2023', '20.02.2023', '10.03.2023'],  # Только корректные даты
            'Сумма операции': ['1000.50', '2000', '1500.75'],
            'Статус': ['OK', 'OK', 'OK']
        })

        clean_data, errors = validator.validate_transaction_data(test_data)

        assert len(clean_data) == 3  # Все строки должны быть корректными
        assert isinstance(errors, list)

    def test_load_user_settings(self):
        # Создаем временный файл настроек
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "user_currencies": ["USD", "EUR"],
                "user_stocks": ["AAPL", "AMZN"]
            }, f)
            temp_path = f.name

        try:
            # Мокаем путь к настройкам
            import src.utils
            original_path = src.utils.settings.user_settings_path
            src.utils.settings.user_settings_path = temp_path

            settings = load_user_settings()
            assert 'user_currencies' in settings
            assert 'user_stocks' in settings

        finally:
            src.utils.settings.user_settings_path = original_path
            os.unlink(temp_path)

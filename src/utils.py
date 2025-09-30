import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


class DataValidator :
    """Валидатор данных транзакций"""

    @staticmethod
    def validate_transaction_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]] :
        """Проверка и очистка данных транзакций"""
        errors = []

        # Проверка обязательных колонок
        required_columns = ['Дата операции', 'Сумма операции', 'Статус']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns :
            raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")

        # Копируем данные для очистки
        clean_df = df.copy()

        # Обработка дат
        clean_df, date_errors = DataValidator._process_dates(clean_df)
        errors.extend(date_errors)

        # Обработка числовых полей
        clean_df, numeric_errors = DataValidator._process_numeric_fields(clean_df)
        errors.extend(numeric_errors)

        # Обработка текстовых полей
        clean_df, text_errors = DataValidator._process_text_fields(clean_df)
        errors.extend(text_errors)

        # Удаление дубликатов
        initial_count = len(clean_df)
        clean_df = clean_df.drop_duplicates()
        if len(clean_df) < initial_count :
            errors.append(f"Удалено {initial_count - len(clean_df)} дубликатов")

        # Удаление строк с критическими ошибками
        initial_count = len(clean_df)
        clean_df = clean_df.dropna(subset=['Дата операции', 'Сумма операции', 'Статус'])
        if len(clean_df) < initial_count :
            errors.append(f"Удалено {initial_count - len(clean_df)} строк с некорректными данными")

        return clean_df, errors

    @staticmethod
    def _process_dates(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]] :
        """Обработка и валидация дат"""
        errors = []
        clean_df = df.copy()

        date_columns = ['Дата операции', 'Дата платежа']

        for col in date_columns :
            if col not in clean_df.columns :
                continue

            original_non_null = clean_df[col].notna().sum()

            # Пробуем разные форматы дат
            for date_format in settings.date_formats :
                try :
                    clean_df[col] = pd.to_datetime(
                        clean_df[col],
                        format=date_format,
                        errors='coerce'
                    )
                    # Если удалось преобразовать большинство дат, используем этот формат
                    if clean_df[col].notna().sum() > original_non_null * 0.8 :
                        break
                except Exception:
                    continue

            # Убираем устаревший параметр infer_datetime_format
            # Просто используем errors='coerce' для оставшихся проблемных значений
            if clean_df[col].isna().any() :
                clean_df[col] = pd.to_datetime(clean_df[col], errors='coerce')

            # Проверяем разумность дат (не в будущем и не слишком в прошлом)
            if col in clean_df.columns and clean_df[col].notna().any() :
                max_date = datetime.now() + timedelta(days=1)  # Завтра
                min_date = datetime(2000, 1, 1)  # 2000 год

                invalid_dates = clean_df[
                    (clean_df[col] > max_date) | (clean_df[col] < min_date)]

                if len(invalid_dates) > 0 :
                    errors.append(f"Найдено {len(invalid_dates)} некорректных дат в колонке {col}")
                    clean_df.loc[invalid_dates.index, col] = pd.NaT

        return clean_df, errors

    @staticmethod
    def _process_numeric_fields(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]] :
        """Обработка числовых полей"""
        errors = []
        clean_df = df.copy()

        numeric_columns = ['Сумма операции', 'Сумма платежа', 'Кешбэк', 'Бонусы (включая кешбэк)',
                           'Округление на «Инвесткопилку»', 'Сумма операции с округлением']

        for col in numeric_columns :
            if col not in clean_df.columns :
                continue

            # Заменяем запятые на точки и преобразуем в числа
            clean_df[col] = pd.to_numeric(
                clean_df[col].astype(str).str.replace(',', '.'),
                errors='coerce'
            )

            # Проверяем на выбросы (суммы больше 10 млн)
            if clean_df[col].notna().any() :
                outliers = clean_df[clean_df[col].abs() > 10000000]
                if len(outliers) > 0 :
                    errors.append(f"Найдено {len(outliers)} выбросов в колонке {col}")

        return clean_df, errors

    @staticmethod
    def _process_text_fields(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]] :
        """Обработка текстовых полей"""
        errors = []
        clean_df = df.copy()

        text_columns = ['Статус', 'Категория', 'Описание', 'Номер карты']

        for col in text_columns :
            if col not in clean_df.columns :
                continue

            clean_df[col] = clean_df[col].astype(str).str.strip()

            # Замена NaN строк
            clean_df[col] = clean_df[col].replace('nan', '').replace('None', '')

            # Проверка на слишком длинные тексты
            if col == 'Описание' :
                too_long = clean_df[clean_df[col].str.len() > 500]
                if len(too_long) > 0 :
                    errors.append(f"Найдено {len(too_long)} очень длинных описаний")
                    clean_df.loc[too_long.index, col] = clean_df.loc[too_long.index, col].str[:500]

        return clean_df, errors


def load_transactions(file_path: str = settings.data_file_path) -> pd.DataFrame :
    """Загрузка и валидация транзакций из Excel файла"""
    try :
        logger.info(f"Загрузка данных из {file_path}")

        # Чтение файла
        df = pd.read_excel(file_path)

        if df.empty :
            raise ValueError("Файл не содержит данных")

        # Валидация и очистка данных
        clean_df, errors = DataValidator.validate_transaction_data(df)

        if errors :
            logger.warning(f"Обнаружены проблемы при загрузке данных: {errors}")

        logger.info(f"Успешно загружено {len(clean_df)} транзакций")
        return clean_df

    except Exception as e :
        logger.error(f"Ошибка загрузки транзакций: {e}")
        raise


def get_date_range(date_str: str, period: str = 'M') -> Tuple[datetime, datetime] :
    """Получение диапазона дат для анализа"""
    try :
        # Парсим дату с учетом времени
        if ' ' in date_str :
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else :
            date = datetime.strptime(date_str, '%Y-%m-%d')

        if period == 'W' :  # Неделя
            start_date = date - timedelta(days=date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=6)
        elif period == 'M' :  # Месяц
            start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = date.replace(day=28) + timedelta(days=4)
            end_date = min(next_month.replace(day=1) - timedelta(days=1), date)
        elif period == 'Y' :  # Год
            start_date = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = date
        elif period == 'ALL' :  # Все данные
            start_date = datetime(2000, 1, 1)
            end_date = date
        else :
            raise ValueError(f"Неизвестный период: {period}")

        return start_date, end_date

    except ValueError as e :
        logger.error(f"Ошибка парсинга даты {date_str}: {e}")
        raise


def filter_transactions_by_date(df: pd.DataFrame, start_date: datetime,
                                end_date: datetime) -> pd.DataFrame :
    """Фильтрация транзакций по диапазону дат"""
    mask = (df['Дата операции'] >= start_date) & (df['Дата операции'] <= end_date)
    filtered_df = df.loc[mask].copy()

    logger.info(f"Отфильтровано {len(filtered_df)} транзакций за период {start_date.date()} - {end_date.date()}")
    return filtered_df


def get_greeting(time_str: str) -> str :
    """Получение приветствия в зависимости от времени"""
    try :
        if ' ' in time_str :
            hour = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').hour
        else :
            hour = datetime.strptime(time_str, '%Y-%m-%d').hour

        if 5 <= hour < 12 :
            return "Доброе утро"
        elif 12 <= hour < 17 :
            return "Добрый день"
        elif 17 <= hour < 23 :
            return "Добрый вечер"
        else :
            return "Доброй ночи"

    except ValueError :
        return "Добрый день"  # По умолчанию


def load_user_settings() -> Dict[str, Any] :
    """Загрузка пользовательских настроек"""
    try :
        with open(settings.user_settings_path, 'r', encoding='utf-8') as f :
            settings_data = json.load(f)

        # Валидация настроек
        required_sections = ['user_currencies', 'user_stocks']
        for section in required_sections :
            if section not in settings_data :
                raise ValueError(f"Отсутствует обязательный раздел {section} в настройках")

        return settings_data

    except FileNotFoundError :
        logger.error(f"Файл настроек {settings.user_settings_path} не найден")
        raise
    except json.JSONDecodeError as e :
        logger.error(f"Ошибка парсинга JSON в настройках: {e}")
        raise


def calculate_cashback(amount: float, category: str, cashback_rules: Dict[str, float]) -> float :
    """Расчет кешбэка по сложной логике"""
    try :
        # Базовая ставка
        base_rate = cashback_rules.get('default', 0.01)

        # Повышенный кешбэк для категорий
        category_rate = cashback_rules.get(category, base_rate)

        # Дополнительный бонус для больших покупок (ИСПРАВЛЕНО)
        bonus_rate = 0.0
        if amount > 10000 :
            bonus_rate = 0.02  # +2% для покупок > 10,000
        elif amount > 5000 :
            bonus_rate = 0.01  # +1% для покупок > 5,000

        total_rate = category_rate + bonus_rate

        # Ограничение максимального кешбэка 15%
        total_rate = min(total_rate, 0.15)

        cashback = amount * total_rate

        # Округление до 2 знаков
        return round(cashback, 2)

    except Exception as e :
        logger.warning(f"Ошибка расчета кешбэка: {e}")
        return round(amount * 0.01, 2)  # Fallback 1%

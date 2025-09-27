# Transaction Analyzer

Приложение для анализа банковских транзакций с поддержкой веб-интерфейса, отчетов и аналитики.

## Функциональность

- 📊 Анализ транзакций из Excel-файлов
- 🌐 Генерация JSON данных для веб-страниц
- 📈 Отчеты и аналитика
- 💰 Расчет кешбэка и инвесткопилки
- 🔍 Поиск и фильтрация транзакций
- 💹 Интеграция с API курсов валют и акций

# Установка
## 1. Клонирование и настройка
### Клонируйте репозиторий:
```bash
git clone <repository-url>
cd transaction-analyzer
```

### Установите зависимости:
```bash
poetry install
```

### Активируйте виртуальное окружение
```bash
poetry shell
```

## 2. Подготовка данных

### Вариант A: Используйте тестовые данные

Сгенерируйте тестовые данные
```bash
python data/sample_data.py
```
### Вариант B: Загрузите свои данные
1. Поместите ваш файл с транзакциями в папку data/

2. Переименуйте его в operations.xlsx

## 3. Запуск приложения

Запуск в режиме веб-страниц (генерирует JSON для фронтенда)
```bash
python -m src.main --command web
```

Запуск в режиме отчетов (генерирует отчеты в папку reports/)
```bash
python -m src.main --command report
```

Запуск в режиме анализа (кешбэк и инвесткопилка)
```bash
python -m src.main --command analyze
```

Простой тест функциональности
```bash
python -m src.main --command test
```

## Настройки приложения

### Файл user_settings.json содержит пользовательские настройки:

Файл user_settings.json содержит пользовательские настройки:

```json
{
  "user_currencies": ["USD", "EUR", "GBP"],
  "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
  "cashback_rules": {
    "Супермаркеты": 0.05,
    "Фастфуд": 0.03,
    "Транспорт": 0.02,
    "default": 0.01
  }
}
```

### Параметры настроек:

* user_currencies - список валют для отслеживания курсов

* user_stocks - список акций для отслеживания цен

* cashback_rules - правила расчета кешбэка по категориям

# Веб-страницы API
## Главная страница
```python
# Генерирует JSON для главной страницы
from src.views import main_page

data = main_page("2023-12-20 15:30:00")
```

### Формат ответа:
```json
{
  "greeting": "Добрый день",
  "cards": [
    {
      "last_digits": "5814",
      "total_spent": 1262.00,
      "cashback": 12.62
    }
  ],
  "top_transactions": [...],
  "currency_rates": [...],
  "stock_prices": [...]
}
```
## Страница событий
```python
# Генерирует JSON для страницы событий
from src.views import events_page

data = events_page("2023-12-20", "M")  # M - месяц, W - неделя, Y - год, ALL - все данные
```

# Сервисы поиска

## Простой поиск
```python
from src.services import simple_search

# Поиск по описанию и категории
results = simple_search(transactions, "магазин")
```

## Поиск по телефонным номерам
```python
from src.services import search_by_phone

# Поиск транзакций с номерами телефонов
results = search_by_phone(transactions)
```
## Поиск переводов физлицам
```python
from src.services import search_by_person_transfers

# Поиск переводов физическим лицам
results = search_by_person_transfers(transactions)
```

# Генерация отчетов

## Траты по категории
```python
from src.reports import spending_by_category

# Траты по категории за последние 3 месяца
report = spending_by_category(transactions, "Супермаркеты", "2023-12-20")
```
## Траты по дням недели
```python
from src.reports import spending_by_weekday

# Средние траты по дням недели
report = spending_by_weekday(transactions)
```
## Все отчеты через главный модуль
```bash
python -m src.main --command report
```
#### Отчеты сохраняются в папку reports/ в формате JSON.

# Тестирование

```bash
# Запуск всех тестов
pytest tests/ -v
```
```bash
# Запуск конкретного модуля тестов
pytest tests/test_views.py -v
```
```bash
# Запуск с покрытием кода
pytest tests/ --cov=src --cov-report=html
```

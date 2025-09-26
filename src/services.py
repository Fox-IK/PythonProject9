import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Расчет суммы для инвесткопилки через округление трат."""
    try:
        total_savings = 0.0

        for transaction in transactions:
            # Проверяем, что транзакция в нужном месяце
            trans_date = datetime.strptime(transaction['Дата операции'], '%Y-%m-%d')
            if trans_date.strftime('%Y-%m') != month:
                continue

            amount = abs(transaction['Сумма операции'])
            if amount > 0:  # Только расходы
                rounded_amount = _round_up_to_nearest(amount, limit)
                savings = rounded_amount - amount
                total_savings += savings

        logger.info(f"Сумма для инвесткопилки за {month}: {total_savings}")
        return round(total_savings, 2)
    except Exception as e:
        logger.error(f"Ошибка расчета инвесткопилки: {e}")
        return 0.0


def _round_up_to_nearest(amount: float, limit: int) -> float:
    """Округление до ближайшего кратного limit."""
    return ((amount + limit - 1) // limit) * limit


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Простой поиск транзакций по описанию или категории."""
    try:
        results = []
        query_lower = query.lower()

        for transaction in transactions:
            description = transaction.get('Описание', '').lower()
            category = transaction.get('Категория', '').lower()

            if query_lower in description or query_lower in category:
                results.append(transaction)

        logger.info(f"Найдено {len(results)} транзакций по запросу '{query}'")
        return results
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        return []


def find_phone_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Поиск транзакций с телефонными номерами в описании."""
    try:
        phone_pattern = r'\+7\s?\(?\d{3}\)?\s?\d{3}[\s-]?\d{2}[\s-]?\d{2}'
        results = []

        for transaction in transactions:
            description = transaction.get('Описание', '')
            if re.search(phone_pattern, description):
                results.append(transaction)

        logger.info(f"Найдено {len(results)} транзакций с телефонными номерами")
        return results
    except Exception as e:
        logger.error(f"Ошибка поиска телефонных номеров: {e}")
        return []

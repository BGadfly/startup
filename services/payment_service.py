"""Платёжная интеграция"""

import uuid
from datetime import datetime
from typing import Dict
from fastapi import HTTPException

from db.db import get_db_connection
from services.subscription_service import create_subscription


class PaymentProcessor:
    """Базовый класс для платёжных систем"""

    @staticmethod
    def create_payment(amount: int, description: str, user_id: str) -> Dict:
        """Создаёт платёж (тестовый режим)"""
        payment_id = str(uuid.uuid4())

        # Тестовый режим (возвращает фейковую ссылку)
        return {
            "payment_id": payment_id,
            "confirmation_url": f"https://test-payment.com/pay/{payment_id}",
            "amount": amount,
            "description": description
        }

    @staticmethod
    def check_payment_status(payment_id: str) -> str:
        """Проверяет статус платежа"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM payments WHERE payment_id = ?", (payment_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return row[0]
        return "pending"
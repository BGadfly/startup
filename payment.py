# payment.py - добавь к основному файлу main.py

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sqlite3
import json


# ---------- Модели данных ----------
class SubscriptionPlan(BaseModel):
    """Модель тарифа подписки"""
    plan_id: str
    name: str
    price: int  # в рублях/копейках
    duration_days: int
    features: list[str]
    extension_limit: int  # лимит наращиваний в месяц


class PaymentRequest(BaseModel):
    """Запрос на создание платежа"""
    plan_id: str = Field(..., description="ID тарифа")
    user_id: str = Field(..., description="ID пользователя")
    promo_code: Optional[str] = Field(None, description="Промокод")


class PaymentConfirm(BaseModel):
    """Подтверждение платежа"""
    payment_id: str = Field(..., description="ID платежа")
    payment_token: Optional[str] = Field(None, description="Токен от платёжной системы")


class SubscriptionResponse(BaseModel):
    """Ответ с данными подписки"""
    subscription_id: str
    user_id: str
    plan_id: str
    status: str  # active, expired, cancelled
    expires_at: str
    extensions_used: int
    extensions_limit: int


# ---------- Тарифы подписки ----------
SUBSCRIPTION_PLANS = {
    "basic": SubscriptionPlan(
        plan_id="basic",
        name="Базовый",
        price=1990,  # 1990 рублей
        duration_days=30,
        features=["3 анализа в день", "Базовые рекомендации", "Чат с мастером"],
        extension_limit=1
    ),
    "pro": SubscriptionPlan(
        plan_id="pro",
        name="Профессиональный",
        price=4990,
        duration_days=30,
        features=["Неограниченный анализ", "Расширенные рекомендации", "Приоритетная поддержка", "Сохранение истории"],
        extension_limit=5
    ),
    "business": SubscriptionPlan(
        plan_id="business",
        name="Бизнес",
        price=14990,
        duration_days=90,
        features=["Всё из Pro", "API доступ", "Статистика салона", "Бесплатное обучение"],
        extension_limit=20
    )
}

# ---------- База данных подписок ----------
def init_subscription_db():
    """Инициализация базы данных подписок"""
    conn = sqlite3.connect("subscriptions.db")
    cursor = conn.cursor()

    # Таблица подписок пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            extensions_used INTEGER DEFAULT 0,
            extensions_limit INTEGER DEFAULT 1
        )
    """)

    # Таблица платежей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            promo_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP
        )
    """)

    # Таблица промокодов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            discount_percent INTEGER DEFAULT 10,
            valid_until TIMESTAMP,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# Вызов при старте
init_subscription_db()


# ---------- Работа с подписками ----------
def get_user_subscription(user_id: str) -> Optional[Dict]:
    """Получить активную подписку пользователя"""
    conn = sqlite3.connect("subscriptions.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM subscriptions 
        WHERE user_id = ? AND status = 'active' 
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "subscription_id": row[0],
            "user_id": row[1],
            "plan_id": row[2],
            "status": row[3],
            "created_at": row[4],
            "expires_at": row[5],
            "extensions_used": row[6],
            "extensions_limit": row[7]
        }
    return None


def create_subscription(user_id: str, plan_id: str) -> Dict:
    """Создать новую подписку"""
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Тариф не найден")

    subscription_id = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=plan.duration_days)

    conn = sqlite3.connect("subscriptions.db")
    cursor = conn.cursor()

    # Деактивируем старые подписки
    cursor.execute("""
        UPDATE subscriptions SET status = 'expired' 
        WHERE user_id = ? AND status = 'active'
    """, (user_id,))

    # Создаём новую
    cursor.execute("""
        INSERT INTO subscriptions 
        (subscription_id, user_id, plan_id, status, expires_at, extensions_limit)
        VALUES (?, ?, ?, 'active', ?, ?)
    """, (subscription_id, user_id, plan_id, expires_at, plan.extension_limit))

    conn.commit()
    conn.close()

    return {
        "subscription_id": subscription_id,
        "user_id": user_id,
        "plan_id": plan_id,
        "status": "active",
        "expires_at": expires_at.isoformat(),
        "extensions_limit": plan.extension_limit
    }


# ---------- Платёжная интеграция ----------
class PaymentProcessor:
    """Базовый класс для платёжных систем"""

    @staticmethod
    def create_payment(amount: int, description: str, user_id: str) -> Dict:
        """
        Создаёт платёж в YooKassa / Stripe
        Для теста возвращает тестовую ссылку
        """
        # Реальная интеграция с YooKassa
        # Документация: https://yookassa.ru/developers/api

        payment_id = str(uuid.uuid4())

        # Тестовый режим (замени на реальный API ключ)
        # import yookassa
        # yookassa.Configuration.account_id = "ВАШ_ID"
        # yookassa.Configuration.secret_key = "ВАШ_КЛЮЧ"
        #
        # payment = yookassa.Payment.create({
        #     "amount": {"value": amount/100, "currency": "RUB"},
        #     "payment_method_data": {"type": "bank_card"},
        #     "confirmation": {"type": "redirect", "return_url": "https://yourapp.com/success"},
        #     "description": description,
        #     "metadata": {"user_id": user_id}
        # })
        #
        # return {
        #     "payment_id": payment.id,
        #     "confirmation_url": payment.confirmation.confirmation_url
        # }

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
        # В реальном коде: запрос к YooKassa/Stripe API

        conn = sqlite3.connect("subscriptions.db")
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM payments WHERE payment_id = ?", (payment_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return row[0]
        return "pending"

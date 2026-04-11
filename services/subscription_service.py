"""Сервис для работы с подписками"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException

from core.config import SUBSCRIPTION_PLANS
from db.db import get_db_connection


def get_user_subscription(user_id: str) -> Optional[Dict]:
    """Получить активную подписку пользователя"""
    conn = get_db_connection()
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

    conn = get_db_connection()
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


def use_extension(user_id: str) -> Dict:
    """Использовать один лимит наращивания"""
    subscription = get_user_subscription(user_id)

    if not subscription:
        raise HTTPException(status_code=403, detail="Нет активной подписки")

    if subscription["extensions_used"] >= subscription["extensions_limit"]:
        raise HTTPException(status_code=429, detail="Лимит наращиваний на месяц исчерпан")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE subscriptions 
        SET extensions_used = extensions_used + 1 
        WHERE subscription_id = ?
    """, (subscription["subscription_id"],))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "extensions_used": subscription["extensions_used"] + 1,
        "extensions_left": subscription["extensions_limit"] - subscription["extensions_used"] - 1
    }
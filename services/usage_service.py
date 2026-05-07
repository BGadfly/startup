"""Сервис проверки бесплатных использований"""

from db.db import get_db_connection
from datetime import datetime


def has_free_usage(user_id: str) -> bool:
    """Проверяет, есть ли у пользователя бесплатное использование"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT used FROM free_usage WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        # Пользователь новый — есть бесплатная попытка
        return True

    return not row[0]  # True если used == 0


def mark_free_usage_used(user_id: str) -> None:
    """Отмечает бесплатное использование как использованное"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO free_usage (user_id, used, used_at) 
        VALUES (?, 1, ?)
        ON CONFLICT(user_id) DO UPDATE SET used = 1, used_at = ?
    """, (user_id, datetime.now().isoformat(), datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_remaining_usage(user_id: str) -> dict:
    """Возвращает информацию об оставшихся использованиях"""
    from services.subscription_service import get_user_subscription
    from services.promo_services import get_active_promo
    
    subscription = get_user_subscription(user_id)
    has_free = has_free_usage(user_id)
    active_promo = get_active_promo(user_id)
    
    # ✅ Проверяем активный бесплатный промокод
    if active_promo and active_promo["can_use"]:
        return {
            "has_access": True,
            "access_type": "promo",
            "remaining": active_promo["daily_limit"] - active_promo["daily_used"] if active_promo["daily_limit"] else 999,
            "total": active_promo["daily_limit"] or 999,
            "subscription_active": False,
            "promo_code": active_promo["promo_code"],
            "promo_expires": active_promo["expires_at"],
            "daily_limit": active_promo["daily_limit"],
            "daily_used": active_promo["daily_used"],
            "hourly_remaining": active_promo["hourly_limit"] - active_promo["hourly_used"] if active_promo["hourly_limit"] else None,
            "hourly_limit": active_promo["hourly_limit"]
        }

def use_analysis_credit(user_id: str) -> dict:
    """Использует одну попытку анализа"""
    from services.subscription_service import get_user_subscription, use_extension
    from services.promo_services import get_active_promo, use_promo_credit
    
    # ✅ Сначала пробуем списать с промокода
    active_promo = get_active_promo(user_id)
    if active_promo and active_promo["can_use"]:
        return use_promo_credit(user_id)
    
    # ✅ Затем с подписки
    subscription = get_user_subscription(user_id)
    if subscription and subscription["extensions_used"] < subscription["extensions_limit"]:
        result = use_extension(user_id)
        return {
            "success": True,
            "access_type": "subscription",
            "remaining": result["extensions_left"]
        }
    
    # ✅ Затем бесплатную попытку
    if has_free_usage(user_id):
        mark_free_usage_used(user_id)
        return {
            "success": True,
            "access_type": "free",
            "remaining": 0
        }
    
    return {
        "success": False,
        "message": "Лимит исчерпан",
        "require_subscription": True
    }
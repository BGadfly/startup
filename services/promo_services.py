"""Сервис работы с промокодами"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from db.db import get_db_connection


def create_promo_code(
    code: str,
    discount_percent: int = 0,
    valid_days: int = 30,
    max_uses: int = 100,
    override_plan_id: Optional[str] = None,
    override_extension_limit: Optional[int] = None,
    override_duration_days: Optional[int] = None,
    description: str = "",
    is_free: bool = False,
    daily_limit: Optional[int] = None,
    hourly_limit: Optional[int] = None,
    duration_days: int = 30
) -> Dict:
    """Создаёт новый промокод"""
    valid_until = datetime.now() + timedelta(days=valid_days)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO promocodes 
        (code, discount_percent, valid_until, max_uses, used_count,
         override_plan_id, override_extension_limit, override_duration_days,
         description, is_free, daily_limit, hourly_limit, duration_days)
        VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code.upper(), discount_percent, valid_until.isoformat(), max_uses,
        override_plan_id, override_extension_limit, override_duration_days,
        description, is_free, daily_limit, hourly_limit, duration_days
    ))
    conn.commit()
    conn.close()
    
    return {
        "code": code.upper(),
        "discount_percent": discount_percent,
        "valid_until": valid_until.isoformat(),
        "max_uses": max_uses,
        "is_free": is_free,
        "daily_limit": daily_limit,
        "hourly_limit": hourly_limit,
        "duration_days": duration_days,
        "description": description
    }


def validate_promo_code(code: str) -> Optional[Dict]:
    """Проверяет валидность промокода"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM promocodes 
        WHERE code = ? AND valid_until > ? AND used_count < max_uses
    """, (code.upper(), datetime.now().isoformat()))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "code": row[0],
        "discount_percent": row[1],
        "valid_until": row[2],
        "max_uses": row[3],
        "used_count": row[4],
        "override_plan_id": row[5],
        "override_extension_limit": row[6],
        "override_duration_days": row[7],
        "description": row[8],
        "is_free": bool(row[9]) if len(row) > 9 else False,
        "daily_limit": row[10] if len(row) > 10 else None,
        "hourly_limit": row[11] if len(row) > 11 else None,
        "duration_days": row[12] if len(row) > 12 else 30
    }


def activate_free_promo(user_id: str, code: str) -> Dict:
    """Активирует бесплатный промокод для пользователя"""
    promo = validate_promo_code(code)
    
    if not promo:
        raise ValueError("Промокод недействителен или истёк")
    
    if not promo["is_free"]:
        raise ValueError("Этот промокод не является бесплатным. Используйте его при оплате подписки.")
    
    # Проверяем, не активирован ли уже у этого пользователя
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM promo_activations 
        WHERE user_id = ? AND promo_code = ? AND expires_at > ?
    """, (user_id, code.upper(), datetime.now().isoformat()))
    
    existing = cursor.fetchone()
    if existing:
        conn.close()
        raise ValueError("Вы уже активировали этот промокод")
    
    # Активируем
    expires_at = datetime.now() + timedelta(days=promo.get("duration_days", 30) or 30)
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO promo_activations 
        (user_id, promo_code, expires_at, daily_limit, hourly_limit, 
         daily_used, hourly_used, last_hour_reset, last_day_reset)
        VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)
    """, (
        user_id, code.upper(), expires_at.isoformat(),
        promo.get("daily_limit", 0), promo.get("hourly_limit", 0),
        now, now
    ))
    
    # Увеличиваем счётчик использований промокода
    cursor.execute("""
        UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?
    """, (code.upper(),))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Промокод {code.upper()} активирован!",
        "expires_at": expires_at.isoformat(),
        "daily_limit": promo.get("daily_limit"),
        "hourly_limit": promo.get("hourly_limit"),
        "duration_days": promo.get("duration_days", 30)
    }


def get_active_promo(user_id: str) -> Optional[Dict]:
    """Получает активный бесплатный промокод пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM promo_activations 
        WHERE user_id = ? AND expires_at > ?
        ORDER BY activated_at DESC LIMIT 1
    """, (user_id, datetime.now().isoformat()))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    # ✅ Безопасное извлечение данных
    promo_id = row[0]
    promo_user_id = row[1]
    promo_code = row[2]
    activated_at = row[3] if len(row) > 3 else None
    expires_at = row[4] if len(row) > 4 else None
    daily_limit = row[5] if len(row) > 5 else 0
    hourly_limit = row[6] if len(row) > 6 else 0
    daily_used = row[7] if len(row) > 7 else 0
    hourly_used = row[8] if len(row) > 8 else 0
    last_hour_reset = row[9] if len(row) > 9 else None
    last_day_reset = row[10] if len(row) > 10 else None
    
    # Проверяем сброс лимитов
    now = datetime.now()
    
    # ✅ Безопасный парсинг дат
    try:
        last_hour = datetime.fromisoformat(last_hour_reset) if isinstance(last_hour_reset, str) else now
    except (ValueError, TypeError):
        last_hour = now
    
    try:
        last_day = datetime.fromisoformat(last_day_reset) if isinstance(last_day_reset, str) else now
    except (ValueError, TypeError):
        last_day = now
    
    current_hourly_used = hourly_used
    current_daily_used = daily_used
    
    # Сброс часового лимита (если прошёл час)
    if (now - last_hour).total_seconds() >= 3600:
        current_hourly_used = 0
        # Обновляем в БД
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE promo_activations 
                SET hourly_used = 0, last_hour_reset = ?
                WHERE id = ?
            """, (now.isoformat(), promo_id))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    # Сброс дневного лимита (если прошли сутки)
    if (now - last_day).total_seconds() >= 86400:
        current_daily_used = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE promo_activations 
                SET daily_used = 0, last_day_reset = ?
                WHERE id = ?
            """, (now.isoformat(), promo_id))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    # Проверка лимитов
    can_use = True
    if daily_limit and current_daily_used >= daily_limit:
        can_use = False
    if hourly_limit and current_hourly_used >= hourly_limit:
        can_use = False
    
    return {
        "id": promo_id,
        "user_id": promo_user_id,
        "promo_code": promo_code,
        "activated_at": activated_at,
        "expires_at": expires_at,
        "daily_limit": daily_limit,
        "hourly_limit": hourly_limit,
        "daily_used": current_daily_used,
        "hourly_used": current_hourly_used,
        "can_use": can_use
    }


def use_promo_credit(user_id: str) -> Dict:
    """Использовать одну попытку по промокоду"""
    promo = get_active_promo(user_id)
    
    if not promo or not promo["can_use"]:
        return {"success": False, "message": "Лимит исчерпан"}
    
    now = datetime.now().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE promo_activations 
        SET daily_used = daily_used + 1, 
            hourly_used = hourly_used + 1
        WHERE user_id = ? AND expires_at > ?
    """, (user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    new_daily_used = (promo["daily_used"] or 0) + 1
    new_hourly_used = (promo["hourly_used"] or 0) + 1
    
    return {
        "success": True,
        "daily_remaining": (promo["daily_limit"] - new_daily_used) if promo["daily_limit"] else None,
        "hourly_remaining": (promo["hourly_limit"] - new_hourly_used) if promo["hourly_limit"] else None
    }
"""Инициализация базы данных"""

import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "data/subscriptions.db")

def init_db():
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            discount_percent INTEGER DEFAULT 0,
            valid_until TIMESTAMP,
            max_uses INTEGER DEFAULT 100,
            used_count INTEGER DEFAULT 0,
            override_plan_id TEXT,
            override_extension_limit INTEGER,
            override_duration_days INTEGER,
            description TEXT,
            is_free BOOLEAN DEFAULT 0,
            daily_limit INTEGER DEFAULT NULL,
            hourly_limit INTEGER DEFAULT NULL,
            duration_days INTEGER DEFAULT 30
        )
    """)

    # ✅ Таблица активированных бесплатных промокодов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            promo_code TEXT NOT NULL,
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            daily_limit INTEGER DEFAULT 0,
            hourly_limit INTEGER DEFAULT 0,
            daily_used INTEGER DEFAULT 0,
            hourly_used INTEGER DEFAULT 0,
            last_hour_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_day_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS free_usage (
        user_id TEXT PRIMARY KEY,
        used BOOLEAN DEFAULT 0,
        used_at TIMESTAMP
    )
""")

    conn.commit()
    conn.close()


def get_db_connection():
    """Получить соединение с БД"""
    return sqlite3.connect("subscriptions.db")
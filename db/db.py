"""Инициализация базы данных"""

import sqlite3


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


def get_db_connection():
    """Получить соединение с БД"""
    return sqlite3.connect("subscriptions.db")
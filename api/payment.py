"""API эндпоинты для оплаты и подписок"""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import sqlite3

from core.config import SUBSCRIPTION_PLANS, SubscriptionPlan
from db.models import PaymentRequest, PaymentConfirm
from db.db import get_db_connection
from services.subscription_service import get_user_subscription, create_subscription, use_extension
from services.payment_service import PaymentProcessor

router = APIRouter(tags=["Оплата и подписки"])


@router.get("/subscription/plans", response_model=list[SubscriptionPlan])
async def get_subscription_plans():
    """Получить список тарифов подписки"""
    return list(SUBSCRIPTION_PLANS.values())


@router.post("/subscription/create-payment")
async def create_payment(request: PaymentRequest):
    """Создать платёж для подписки"""
    plan = SUBSCRIPTION_PLANS.get(request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Тариф не найден")

    amount = plan.price

    # Применяем промокод
    if request.promo_code:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT discount_percent, valid_until, max_uses, used_count 
            FROM promocodes WHERE code = ?
        """, (request.promo_code.upper(),))
        promo = cursor.fetchone()
        conn.close()

        if promo:
            discount, valid_until, max_uses, used_count = promo
            valid_until_date = datetime.fromisoformat(valid_until) if isinstance(valid_until, str) else valid_until

            if datetime.now() < valid_until_date and used_count < max_uses:
                amount = int(amount * (100 - discount) / 100)

    payment = PaymentProcessor.create_payment(
        amount=amount,
        description=f"Подписка {plan.name} для пользователя {request.user_id}",
        user_id=request.user_id
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payments (payment_id, user_id, plan_id, amount, status, promo_code)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (payment["payment_id"], request.user_id, request.plan_id, amount, request.promo_code))
    conn.commit()
    conn.close()

    return JSONResponse(content={
        "payment_id": payment["payment_id"],
        "confirmation_url": payment["confirmation_url"],
        "amount": amount,
        "currency": "RUB",
        "plan": plan.name
    })


@router.post("/subscription/confirm")
async def confirm_payment(request: PaymentConfirm):
    """Подтвердить оплату и активировать подписку"""
    conn = get_db_connection()
    cursor = conn.cursor()

    payment_status = PaymentProcessor.check_payment_status(request.payment_id)

    if payment_status == "paid":
        cursor.execute("SELECT user_id, plan_id, amount FROM payments WHERE payment_id = ?", (request.payment_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Платёж не найден")

        user_id, plan_id, amount = row

        cursor.execute("""
            UPDATE payments SET status = 'paid', paid_at = CURRENT_TIMESTAMP 
            WHERE payment_id = ?
        """, (request.payment_id,))

        subscription = create_subscription(user_id, plan_id)

        conn.commit()
        conn.close()

        return JSONResponse(content={
            "success": True,
            "message": "Подписка активирована",
            "subscription": subscription
        })

    elif payment_status == "pending":
        conn.close()
        return JSONResponse(content={
            "success": False,
            "message": "Платёж ещё не обработан. Пожалуйста, проверьте статус позже."
        }, status_code=202)

    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Платёж отклонён")


@router.get("/subscription/status/{user_id}")
async def get_subscription_status(user_id: str):
    """Проверить статус подписки пользователя"""
    subscription = get_user_subscription(user_id)

    if not subscription:
        return JSONResponse(content={
            "has_subscription": False,
            "message": "У пользователя нет активной подписки"
        })

    expires_at = datetime.fromisoformat(subscription["expires_at"])
    is_expired = datetime.now() > expires_at

    if is_expired:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE subscriptions SET status = 'expired' WHERE subscription_id = ?",
                       (subscription["subscription_id"],))
        conn.commit()
        conn.close()

        return JSONResponse(content={
            "has_subscription": False,
            "message": "Подписка истекла"
        })

    plan = SUBSCRIPTION_PLANS.get(subscription["plan_id"])

    return JSONResponse(content={
        "has_subscription": True,
        "subscription_id": subscription["subscription_id"],
        "plan": {
            "name": plan.name if plan else subscription["plan_id"],
            "price": plan.price if plan else 0,
            "features": plan.features if plan else []
        },
        "expires_at": subscription["expires_at"],
        "days_left": (expires_at - datetime.now()).days,
        "extensions_used": subscription["extensions_used"],
        "extensions_limit": subscription["extensions_limit"]
    })


@router.post("/subscription/use-extension/{user_id}")
async def use_extension_endpoint(user_id: str):
    """Уменьшить лимит наращиваний при использовании"""
    return use_extension(user_id)


@router.post("/subscription/admin/promocode")
async def create_promocode(code: str, discount_percent: int, valid_days: int = 30, max_uses: int = 1):
    """Создать промокод (для администратора)"""
    valid_until = datetime.now() + timedelta(days=valid_days)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO promocodes (code, discount_percent, valid_until, max_uses)
        VALUES (?, ?, ?, ?)
    """, (code.upper(), discount_percent, valid_until.isoformat(), max_uses))
    conn.commit()
    conn.close()

    return JSONResponse(content={
        "success": True,
        "code": code.upper(),
        "discount_percent": discount_percent,
        "valid_until": valid_until.isoformat(),
        "max_uses": max_uses
    })


@router.post("/webhook/payment")
async def payment_webhook(request: dict):
    """Webhook от платёжной системы"""
    event = request.get("event")
    payment_id = request.get("object", {}).get("id")

    if event == "payment.succeeded":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE payments SET status = 'paid', paid_at = CURRENT_TIMESTAMP 
            WHERE payment_id = ?
        """, (payment_id,))

        cursor.execute("SELECT user_id, plan_id FROM payments WHERE payment_id = ?", (payment_id,))
        row = cursor.fetchone()

        if row:
            user_id, plan_id = row
            create_subscription(user_id, plan_id)

        conn.commit()
        conn.close()

    return JSONResponse(content={"status": "ok"})
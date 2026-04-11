"""Модели данных для Pydantic"""

from typing import Optional
from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):
    """Запрос на создание платежа"""
    plan_id: str = Field(..., description="ID тарифа")
    user_id: str = Field(..., description="ID пользователя")
    promo_code: Optional[str] = Field(None, description="Промокод")


class PaymentConfirm(BaseModel):
    """Подтверждение платежа"""
    payment_id: str = Field(..., description="ID платежа")
    payment_token: Optional[str] = Field(None, description="Токен от платёжной системы")
# api/admin.py

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from services.promo_services import create_promo_code, validate_promo_code
from db.db import get_db_connection

router = APIRouter(tags=["Администрирование"])


@router.post("/admin/promocode")
async def create_special_promo(
    code: str = Query(..., description="Код промокода"),
    discount_percent: int = Query(0, description="Скидка в %"),
    valid_days: int = Query(30, description="Срок действия (дней)"),
    max_uses: int = Query(100, description="Максимум использований"),
    is_free: str = Query("false", description="Бесплатный промокод (true/false)"),
    daily_limit: str = Query(None, description="Дневной лимит"),
    hourly_limit: str = Query(None, description="Часовой лимит"),
    duration_days: str = Query("30", description="Длительность действия промокода (дней)"),
    description: str = Query("", description="Описание"),
    override_extension_limit: str = Query(None, description="Лимит наращиваний"),
    override_duration_days: str = Query(None, description="Длительность подписки")
):
    """Создать промокод"""
    
    # ✅ Преобразуем строки в нужные типы
    is_free_bool = is_free.lower() in ["true", "1", "yes"]
    daily_limit_int = int(daily_limit) if daily_limit and daily_limit.isdigit() else None
    hourly_limit_int = int(hourly_limit) if hourly_limit and hourly_limit.isdigit() else None
    duration_days_int = int(duration_days) if duration_days and duration_days.isdigit() else 30
    extension_limit_int = int(override_extension_limit) if override_extension_limit and override_extension_limit.isdigit() else None
    override_days_int = int(override_duration_days) if override_duration_days and override_duration_days.isdigit() else None
    
    result = create_promo_code(
        code=code,
        discount_percent=discount_percent,
        valid_days=valid_days,
        max_uses=max_uses,
        is_free=is_free_bool,           # ✅ Булево значение
        daily_limit=daily_limit_int,    # ✅ Число или None
        hourly_limit=hourly_limit_int,  # ✅ Число или None
        duration_days=duration_days_int,# ✅ Число
        override_extension_limit=extension_limit_int,
        override_duration_days=override_days_int,
        description=description
    )
    
    return JSONResponse(content={
        "success": True,
        "promo": result
    })
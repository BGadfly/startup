"""API эндпоинты для анализа волос"""

from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from core.ai_module import analyze_and_recommend
from services.usage_service import get_remaining_usage, use_analysis_credit

router = APIRouter(tags=["Анализ волос"])


@router.get("/analysis/access/{user_id}")
async def check_analysis_access(user_id: str):
    """Проверить доступ к анализу"""
    return get_remaining_usage(user_id)


@router.post("/analyze")
async def analyze_hair(
        photo1: UploadFile = File(..., description="Первое фото волос (сверху)"),
        photo2: UploadFile = File(..., description="Второе фото волос (спереди)"),  # ✅ Исправлено с "сзади"
        photo3: UploadFile = File(..., description="Третье фото волос (сбоку)"),
        comment: str = Form("", description="Пожелания клиента (опционально)"),
        user_id: str = Form(..., description="ID пользователя")
):
    """
    Принимает 3 фотографии и комментарий.
    Возвращает анализ характеристик волос и рекомендации по наращиванию.

    Порядок фото важен:
    - photo1: вид сверху (макушка)
    - photo2: вид сзади
    - photo3: вид сбоку
    """
    
    access = get_remaining_usage(user_id)

    if not access["has_access"]:
        raise HTTPException(
            status_code=402,
            detail={
                "message": "Лимит бесплатных использований исчерпан",
                "require_subscription": True,
                "plans_url": "/subscription/plans"
            }
        )

    photos = [photo1, photo2, photo3]
    for i, photo in enumerate(photos):
        if not photo.content_type or not photo.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Файл {photo.filename} не является изображением"
            )

    try:
        photo_bytes = [
            await photo1.read(),
            await photo2.read(),
            await photo3.read()
        ]

        analysis_result = analyze_and_recommend(photo_bytes, comment)

        usage_result = use_analysis_credit(user_id)

        return JSONResponse(content={
            "success": True,
            "user_comment": comment,
            "analysis": {
                "texture": analysis_result["texture"],
                "density": analysis_result["density"],
                "part_type": analysis_result["part_type"],
                "problem_zones": analysis_result["problem_zones"]
            },
            "recommendation": analysis_result["recommendation"],  
            "usage": usage_result  
        })

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Логируем ошибку для отладки
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при анализе: {str(e)}"
        )
"""API эндпоинты для анализа волос"""

from typing import List
from collections import Counter
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from core.ai_module import analyze_hair_from_photos
from core.config import get_hair_recommendation

router = APIRouter(tags=["Анализ волос"])


@router.post("/analyze")
async def analyze_hair(
        photo1: UploadFile = File(..., description="Первое фото волос"),
        photo2: UploadFile = File(..., description="Второе фото волос"),
        photo3: UploadFile = File(..., description="Третье фото волос"),
        comment: str = Form("", description="Комментарий к заказу (опционально)")
):
    """
    Принимает 3 фотографии и комментарий.
    Возвращает анализ и рекомендации.
    """

    # Проверяем, что все файлы - изображения
    photos = [photo1, photo2, photo3]
    for photo in photos:
        if not photo.content_type or not photo.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Файл {photo.filename} не является изображением"
            )

    try:
        # Читаем все фото в байты
        photo1_bytes = await photo1.read()
        photo2_bytes = await photo2.read()
        photo3_bytes = await photo3.read()

        # Анализируем фото с помощью существующей функции
        analysis_result = analyze_hair_from_photos(
            photo1_bytes, photo2_bytes, photo3_bytes, comment
        )

        # Получаем рекомендацию
        recommendation = get_hair_recommendation(analysis_result)

        # Формируем ответ
        return JSONResponse(content={
            "success": True,
            "user_comment": comment,
            "analysis": {
                "texture": analysis_result["texture"],
                "density": analysis_result["density"],
                "part_type": analysis_result["part_type"]
            },
            "problem_zones": analysis_result["problem_zones"],
            "individual_analyses": analysis_result["individual_analyses"],
            "recommendation": recommendation
        })

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при анализе: {str(e)}"
        )
"""API эндпоинты для анализа волос"""

from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from core.ai_module import analyze_and_recommend

router = APIRouter(tags=["Анализ волос"])


@router.post("/analyze")
async def analyze_hair(
        photo1: UploadFile = File(..., description="Первое фото волос (сверху)"),
        photo2: UploadFile = File(..., description="Второе фото волос (сзади)"),
        photo3: UploadFile = File(..., description="Третье фото волос (сбоку)"),
        comment: str = Form("", description="Комментарий к заказу (опционально)")
):
    """
    Принимает 3 фотографии и комментарий.
    Возвращает анализ характеристик волос и рекомендации по наращиванию.

    Порядок фото важен:
    - photo1: вид сверху (макушка)
    - photo2: вид спереди
    - photo3: вид сбоку
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

        # Анализируем фото (комментарий пока не используется в анализе)
        analysis_result = analyze_and_recommend([photo1_bytes, photo2_bytes, photo3_bytes])

        # Формируем ответ в соответствии с новой структурой
        return JSONResponse(content={
            "success": True,
            "user_comment": comment,
            "analysis": {
                "texture": analysis_result["texture"],
                "density": analysis_result["density"],
                "part_type": analysis_result["part_type"],
                "problem_zones": analysis_result["problem_zones"]
            },
            "recommendation": {
                "technique_name": analysis_result["recommendation"]["technique_name"],
                "materials": analysis_result["recommendation"]["materials"],
                "scheme_description": analysis_result["recommendation"]["scheme_description"],
                "instruction": analysis_result["recommendation"]["instruction"],
                "care_recommendations": analysis_result["recommendation"]["care_recommendations"]
            }
        })

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при анализе: {str(e)}"
        )
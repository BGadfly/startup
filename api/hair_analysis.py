"""API эндпоинты для анализа волос"""

from typing import List
from collections import Counter
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from core.ai_module import analyze_image
from core.config import get_extension_type, PART_RECOMMENDATIONS

router = APIRouter(tags=["Анализ волос"])


@router.post("/analyze")
async def analyze_hair(
        photos: List[UploadFile] = File(..., description="3 фотографии волос"),
        comment: str = Form(..., description="Комментарий к заказу")
):
    """Принимает 3 фотографии и комментарий. Возвращает анализ и рекомендации."""

    if len(photos) != 3:
        raise HTTPException(status_code=400, detail="Необходимо загрузить ровно 3 фотографии")

    results = []
    textures = []
    densities = []
    part_types = []

    for idx, photo in enumerate(photos):
        if not photo.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Файл {photo.filename} не является изображением")

        try:
            image_bytes = await photo.read()
            analysis = analyze_image(image_bytes)
            results.append({
                "photo_index": idx + 1,
                "filename": photo.filename,
                "texture": analysis["texture"],
                "density": analysis["density"],
                "part_type": analysis["part_type"]
            })
            textures.append(analysis["texture"])
            densities.append(analysis["density"])
            part_types.append(analysis["part_type"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при анализе {photo.filename}: {str(e)}")

    final_texture = Counter(textures).most_common(1)[0][0]
    final_density = Counter(densities).most_common(1)[0][0]
    final_part = Counter(part_types).most_common(1)[0][0]

    recommended_extension = get_extension_type(final_texture, final_density)
    part_recommendation = PART_RECOMMENDATIONS.get(final_part, "стандартный пробор")

    return JSONResponse(content={
        "comment": comment,
        "photos_analysis": results,
        "aggregated": {
            "texture": final_texture,
            "density": final_density,
            "part_type": final_part
        },
        "part_recommendation": part_recommendation,
        "recommended_extension": recommended_extension,
        "message": "Подбор выполнен успешно"
    })
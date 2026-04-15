"""AI модуль для анализа волос по 3 фотографиям"""

import cv2
import numpy as np
from skimage import feature
from typing import Dict, List, Tuple, Optional


def load_image(image_bytes: bytes) -> np.ndarray:
    """Загружает изображение из байтов"""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Не удалось загрузить изображение")
    return img


def classify_hair_texture_advanced(image_bytes: bytes) -> str:
    """
    Классифицирует текстуру волос:
    - прямые
    - волнистые
    - кудрявые
    - курчавые
    - облысение
    """
    img = load_image(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Проверка на облысение по яркости и текстуре
    h, w = gray.shape
    top_center = gray[h//4:h//2, w//3:2*w//3]
    mean_brightness = np.mean(top_center)
    brightness_variance = np.var(top_center)
    
    if mean_brightness > 180 and brightness_variance < 50:
        return "облысение"
    
    # LBP для текстуры
    lbp = feature.local_binary_pattern(gray, 8, 1, method="uniform")
    texture_score = np.std(lbp)
    
    # Дополнительные признаки для курчавых
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (h * w)
    
    if texture_score < 2.0:
        return "прямые"
    elif texture_score < 3.5:
        return "волнистые"
    elif texture_score < 5.5:
        return "кудрявые"
    elif edge_density > 0.15:
        return "курчавые"
    else:
        return "кудрявые"


def estimate_density_advanced(image_bytes: bytes) -> str:
    """
    Оценивает густоту волос:
    - редкие
    - средние
    - густые
    - облысение
    """
    img = load_image(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # Анализ теменной зоны
    top_roi = gray[h//4:h//2, w//3:2*w//3]
    
    # Адаптивная пороговая обработка
    blurred = cv2.GaussianBlur(top_roi, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    hair_pixels = cv2.countNonZero(thresh)
    total_pixels = top_roi.shape[0] * top_roi.shape[1]
    density = hair_pixels / total_pixels
    
    # Проверка на облысение
    mean_brightness = np.mean(top_roi)
    if mean_brightness > 200 and density < 0.2:
        return "облысение"
    
    if density > 0.75:
        return "густые"
    elif density > 0.45:
        return "средние"
    else:
        return "редкие"


def detect_part_type(image_bytes: bytes) -> str:
    """
    Определяет тип пробора:
    - прямой
    - сбоку
    - полукруг
    - зигзаг
    - облысение
    """
    img = load_image(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # Проверка на облысение
    top_part = gray[0:h//3, 0:w]
    if np.mean(top_part) > 200 and np.var(top_part) < 100:
        return "облысение"
    
    edges = cv2.Canny(top_part, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, 
                            minLineLength=40, maxLineGap=15)
    
    angles = []
    center_positions = []
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            if 60 < angle < 120:  # Вертикальные/горизонтальные линии
                angles.append(angle)
                center_positions.append((x1 + x2) // 2)
    
    if not angles:
        return "прямой"  # по умолчанию
    
    avg_angle = np.mean(angles)
    angle_std = np.std(angles)
    center_x = np.mean(center_positions) if center_positions else w/2
    
    # Определение типа пробора
    if angle_std > 30:
        return "зигзаг"
    elif 20 < angle_std <= 30:
        return "полукруг"
    elif center_x < w/3:
        return "сбоку"
    else:
        return "прямой"


def detect_problem_zones(image_bytes: bytes, view_type: str = "front") -> Dict:
    """
    Детектирует проблемные зоны:
    - залысины
    - лысина
    - местное выпадение
    
    Возвращает словарь с информацией о проблемах
    """
    img = load_image(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    result = {
        "has_bald_spots": False,
        "bald_type": None,  # "залысины", "лысина", "местное выпадение"
        "top_area_percentage": 0,  # процент площади сверху
        "spot_size_category": None,  # "до 5см", "5-10см", "больше 10см"
        "spot_locations": []  # список локаций проблем
    }
    
    # Анализ верхней части головы
    top_roi = gray[0:h//3, w//4:3*w//4]
    
    # Поиск областей с высокой яркостью (отсутствие волос)
    _, thresh = cv2.threshold(top_roi, 180, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bald_area = 0
    total_top_area = top_roi.shape[0] * top_roi.shape[1]
    
    # Анализ контуров проблемных зон
    max_contour_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:  # минимальная площадь проблемной зоны
            bald_area += area
            max_contour_area = max(max_contour_area, area)
            
            # Определение локации
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                if cx < top_roi.shape[1] // 3:
                    result["spot_locations"].append("левая височная")
                elif cx > 2 * top_roi.shape[1] // 3:
                    result["spot_locations"].append("правая височная")
                else:
                    result["spot_locations"].append("теменная")
    
    # Расчет процента площади
    result["top_area_percentage"] = round((bald_area / total_top_area) * 100, 1)
    
    # Определение размера зоны (в пикселях -> примерный перевод в см)
    # Приблизительно: 100 пикселей ≈ 5 см
    pixel_to_cm = 100 / 5  # 20 пикселей на см
    max_spot_size_cm = np.sqrt(max_contour_area) / pixel_to_cm if max_contour_area > 0 else 0
    
    if max_spot_size_cm < 5:
        result["spot_size_category"] = "до 5см"
    elif max_spot_size_cm < 10:
        result["spot_size_category"] = "5-10см"
    elif max_spot_size_cm > 0:
        result["spot_size_category"] = "больше 10см"
    
    # Определение типа проблемы в зависимости от процента и локаций
    if result["top_area_percentage"] > 50:
        result["has_bald_spots"] = True
        result["bald_type"] = "лысина"
    elif result["top_area_percentage"] > 20:
        result["has_bald_spots"] = True
        result["bald_type"] = "залысины"
    elif len(result["spot_locations"]) > 0:
        result["has_bald_spots"] = True
        result["bald_type"] = "местное выпадение"
    
    # Анализ височных зон для залысин (по дополнительным снимкам)
    if view_type == "side":
        temporal_roi = gray[h//3:2*h//3, w//4:3*w//4]
        temporal_brightness = np.mean(temporal_roi)
        if temporal_brightness > 160 and result["bald_type"] is None:
            result["has_bald_spots"] = True
            result["bald_type"] = "залысины"
            result["top_area_percentage"] = max(result["top_area_percentage"], 15)
    
    return result


def analyze_image(image_bytes: bytes, view_type: str = "front") -> Dict:
    """
    Анализирует одно изображение с указанием типа съемки
    
    Args:
        image_bytes: байты изображения
        view_type: тип съемки ("front" - анфас, "side" - профиль, "top" - сверху)
    """
    texture = classify_hair_texture_advanced(image_bytes)
    density = estimate_density_advanced(image_bytes)
    part_type = detect_part_type(image_bytes)
    problem_zones = detect_problem_zones(image_bytes, view_type)
    
    return {
        "texture": texture,
        "density": density,
        "part_type": part_type,
        "problem_zones": problem_zones
    }


def analyze_hair_from_photos(
    photo1_bytes: bytes, 
    photo2_bytes: bytes, 
    photo3_bytes: bytes,
    user_comment: str = ""
) -> Dict:
    """
    Анализирует волосы по трем фотографиям
    
    Args:
        photo1_bytes: анфас
        photo2_bytes: профиль
        photo3_bytes: сверху/теменная зона
        user_comment: комментарий пользователя (не используется в анализе)
    
    Returns:
        Словарь с объединенными результатами анализа
    """
    # Комментарий пользователя не используется в анализе, но сохраняется в результате
    # (программа никак не взаимодействует с комментарием)
    
    # Анализ каждой фотографии
    front_analysis = analyze_image(photo1_bytes, "front")
    side_analysis = analyze_image(photo2_bytes, "side")
    top_analysis = analyze_image(photo3_bytes, "top")
    
    # Объединение результатов с учетом приоритетов
    
    # Текстура (приоритет у фото сверху и анфас)
    texture_priority = ["курчавые", "кудрявые", "волнистые", "прямые", "облысение"]
    texture_candidates = [
        front_analysis["texture"],
        top_analysis["texture"],
        side_analysis["texture"]
    ]
    
    final_texture = "прямые"  # по умолчанию
    for texture in texture_priority:
        if texture in texture_candidates:
            final_texture = texture
            break
    
    # Густота (приоритет у фото сверху)
    density_priority = ["густые", "средние", "редкие", "облысение"]
    if top_analysis["density"] == "облысение":
        final_density = "облысение"
    elif front_analysis["density"] == "облысение":
        final_density = "облысение"
    else:
        density_candidates = [top_analysis["density"], front_analysis["density"]]
        for density in density_priority:
            if density in density_candidates:
                final_density = density
                break
    
    # Пробор (приоритет у анфас и сверху)
    part_candidates = [front_analysis["part_type"], top_analysis["part_type"]]
    part_priority = ["зигзаг", "полукруг", "сбоку", "прямой", "облысение"]
    final_part = "прямой"
    for part in part_priority:
        if part in part_candidates:
            final_part = part
            break
    
    # Проблемные зоны - объединение данных со всех фото
    combined_problems = {
        "has_bald_spots": False,
        "bald_type": None,
        "top_area_percentage": 0,
        "spot_size_category": None,
        "spot_locations": []
    }
    
    # Берем максимальные значения проблем
    for analysis in [front_analysis, side_analysis, top_analysis]:
        pz = analysis["problem_zones"]
        if pz["has_bald_spots"]:
            combined_problems["has_bald_spots"] = True
            combined_problems["top_area_percentage"] = max(
                combined_problems["top_area_percentage"], 
                pz["top_area_percentage"]
            )
            combined_problems["spot_locations"].extend(pz["spot_locations"])
            
            # Приоритет типов: лысина > залысины > местное выпадение
            if pz["bald_type"] == "лысина":
                combined_problems["bald_type"] = "лысина"
            elif pz["bald_type"] == "залысины" and combined_problems["bald_type"] != "лысина":
                combined_problems["bald_type"] = "залысины"
            elif pz["bald_type"] == "местное выпадение" and combined_problems["bald_type"] is None:
                combined_problems["bald_type"] = "местное выпадение"
            
            if pz["spot_size_category"]:
                # Берем максимальный размер
                size_priority = ["больше 10см", "5-10см", "до 5см"]
                for size in size_priority:
                    if size == pz["spot_size_category"] or size == combined_problems["spot_size_category"]:
                        combined_problems["spot_size_category"] = size
                        break
    
    combined_problems["spot_locations"] = list(set(combined_problems["spot_locations"]))
    
    return {
        "texture": final_texture,
        "density": final_density,
        "part_type": final_part,
        "problem_zones": combined_problems,
        "user_comment": user_comment,  # Сохраняем комментарий в результате
        "individual_analyses": {
            "front": front_analysis,
            "side": side_analysis,
            "top": top_analysis
        }
    }


# Пример использования
if __name__ == "__main__":
    # Пример загрузки и анализа с комментарием
    with open("photo1.jpg", "rb") as f:
        photo1 = f.read()
    with open("photo2.jpg", "rb") as f:
        photo2 = f.read()
    with open("photo3.jpg", "rb") as f:
        photo3 = f.read()
    
    user_comment = "У меня сухие кончики и выпадение после родов"
    
    result = analyze_hair_from_photos(photo1, photo2, photo3, user_comment)
    
    print("Результаты анализа:")
    print(f"Текстура: {result['texture']}")
    print(f"Густота: {result['density']}")
    print(f"Пробор: {result['part_type']}")
    print(f"Проблемные зоны: {result['problem_zones']}")
    print(f"Комментарий пользователя: {result['user_comment']}")

    # Добавьте в конец ai_module.py функцию для Flutter

def get_flutter_response(photo1_bytes, photo2_bytes, photo3_bytes, user_comment=""):
    """
    Функция для интеграции с Flutter приложением
    Возвращает JSON-строку с результатами анализа и рекомендацией
    """
    import json
    from config import get_hair_recommendation
    
    # Анализируем фото
    analysis_result = analyze_hair_from_photos(
        photo1_bytes, 
        photo2_bytes, 
        photo3_bytes, 
        user_comment
    )
    
    # Получаем рекомендацию от DeepSeek
    recommendation = get_hair_recommendation(analysis_result)
    
    # Формируем ответ для Flutter
    response = {
        "success": True,
        "analysis": {
            "texture": analysis_result["texture"],
            "density": analysis_result["density"],
            "part_type": analysis_result["part_type"],
            "problem_zones": analysis_result["problem_zones"]
        },
        "recommendation": {
            "technique": recommendation["technique"],
            "materials": recommendation["materials"],
            "scheme_description": recommendation["scheme_description"],
            "instructions": recommendation["instructions"],
            "care_recommendations": recommendation["care_recommendations"]
        },
        "user_comment": user_comment
    }
    
    return json.dumps(response, ensure_ascii=False)


# Функция для обработки запроса от Flutter
def process_flutter_request(request_json):
    """
    Обрабатывает запрос от Flutter приложения
    Ожидает JSON с полями:
    {
        "photo1": "base64_string",
        "photo2": "base64_string", 
        "photo3": "base64_string",
        "comment": "user comment"
    }
    """
    import json
    import base64
    
    data = json.loads(request_json) if isinstance(request_json, str) else request_json
    
    # Декодируем base64 фото
    photo1_bytes = base64.b64decode(data["photo1"])
    photo2_bytes = base64.b64decode(data["photo2"])
    photo3_bytes = base64.b64decode(data["photo3"])
    comment = data.get("comment", "")
    
    return get_flutter_response(photo1_bytes, photo2_bytes, photo3_bytes, comment)
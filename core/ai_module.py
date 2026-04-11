"""AI модуль для анализа волос"""

import cv2
import numpy as np
from skimage import feature


def classify_hair_texture(image_bytes):
    """Классифицирует текстуру волос (прямые, волнистые, кудрявые)"""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Не удалось загрузить изображение")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lbp = feature.local_binary_pattern(gray, 8, 1, method="uniform")
    texture_score = np.std(lbp)

    if texture_score < 2.0:
        return "прямые"
    elif texture_score < 4.0:
        return "волнистые"
    else:
        return "кудрявые"


def estimate_density(image_bytes, roi_x=100, roi_y=200, roi_w=200, roi_h=200):
    """Оценивает густоту волос (густые, средние, редкие)"""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Не удалось загрузить изображение")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    roi_x = min(roi_x, w - 1)
    roi_y = min(roi_y, h - 1)
    roi_w = min(roi_w, w - roi_x)
    roi_h = min(roi_h, h - roi_y)

    roi = gray[roi_y:roi_y + roi_h, roi_x:roi_x + roi_w]
    _, thresh = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY)
    hair_pixels = cv2.countNonZero(thresh)
    total_pixels = roi_w * roi_h
    density = hair_pixels / total_pixels

    if density > 0.8:
        return "густые"
    elif density > 0.5:
        return "средние"
    else:
        return "редкие"


def classify_hair_part(image_bytes):
    """Определяет пробор волос (от 1 до 5)"""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Не удалось загрузить изображение")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    top_part = gray[0:h // 3, 0:w]
    edges = cv2.Canny(top_part, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=50, maxLineGap=10)

    part_score = 0
    center_line_detected = False
    side_line_detected = False
    zigzag_detected = False

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

            if 70 < angle < 110:
                center_x = (x1 + x2) // 2

                if w // 3 < center_x < 2 * w // 3:
                    center_line_detected = True
                    part_score += 2
                elif center_x < w // 3 or center_x > 2 * w // 3:
                    side_line_detected = True
                    part_score += 1

    left_half = top_part[:, :w // 2]
    right_half = top_part[:, w // 2:]

    diff = np.abs(
        left_half.astype(np.float32) - cv2.resize(right_half, (left_half.shape[1], left_half.shape[0])).astype(
            np.float32))
    asymmetry_score = np.mean(diff)

    if asymmetry_score > 30 and not center_line_detected:
        zigzag_detected = True
        part_score += 3

    if center_line_detected and part_score >= 2:
        return 1
    elif side_line_detected and not center_line_detected:
        return 2
    elif zigzag_detected:
        return 3
    elif part_score == 0:
        top_center = top_part[h // 6:h // 3, w // 3:2 * w // 3]
        mean_intensity = np.mean(top_center)
        if mean_intensity > 150:
            return 4
        else:
            return 5
    else:
        return 2


def analyze_image(image_bytes):
    """Анализирует одно изображение и возвращает метки"""
    texture = classify_hair_texture(image_bytes)
    density = estimate_density(image_bytes)
    part_type = classify_hair_part(image_bytes)

    return {
        "texture": texture,
        "density": density,
        "part_type": part_type
    }
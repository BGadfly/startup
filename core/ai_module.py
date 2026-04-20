import base64
import json
import re
import requests
import time
from io import BytesIO
from PIL import Image
from typing import Dict, List, Optional

# =========================
# 🔧 КОНФИГУРАЦИЯ API
# =========================
API_KEY = 'sk_gzRXyIxocRxqxbiKPDiV0YvVfh4MLgTc789е'
API_URL = "https://gen.pollinations.ai/v1/chat/completions"
MAX_RETRIES = 3
RETRY_DELAY = 3


# =========================
# 🌐 ФУНКЦИЯ ЗАПРОСА С ПОВТОРАМИ
# =========================
def make_api_request(payload: dict, timeout: int = 60) -> dict:
    """Отправляет запрос к API с автоматическими повторами при ошибках"""

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=timeout)

            if response.status_code == 200:
                return response.json()

            # 502, 503, 504 - временные ошибки сервера
            if response.status_code in [502, 503, 504, 404]:
                print(f"   ⚠️ Сервер временно недоступен (ошибка {response.status_code})")
                if attempt < MAX_RETRIES - 1:
                    print(f"   🔄 Повторная попытка через {RETRY_DELAY} сек... (попытка {attempt + 2}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                    continue

            raise Exception(f"API error {response.status_code}: {response.text[:200]}")

        except requests.exceptions.Timeout:
            print(f"   ⚠️ Таймаут запроса")
            if attempt < MAX_RETRIES - 1:
                print(f"   🔄 Повторная попытка через {RETRY_DELAY} сек...")
                time.sleep(RETRY_DELAY)
                continue
            raise
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️ Ошибка соединения")
            if attempt < MAX_RETRIES - 1:
                print(f"   🔄 Повторная попытка через {RETRY_DELAY} сек...")
                time.sleep(RETRY_DELAY)
                continue
            raise

    raise Exception(f"Не удалось получить ответ после {MAX_RETRIES} попыток")


# =========================
# 🖼️ ПОДГОТОВКА КОЛЛАЖА ИЗ 3 ФОТО
# =========================
def create_collage(image_bytes_list: List[bytes]) -> bytes:
    images = []
    max_height = 0

    for img_bytes in image_bytes_list:
        img = Image.open(BytesIO(img_bytes))
        images.append(img)
        if img.height > max_height:
            max_height = img.height

    resized_images = []
    total_width = 0

    for img in images:
        new_width = int(img.width * (max_height / img.height))
        resized = img.resize((new_width, max_height), Image.Resampling.LANCZOS)
        resized_images.append(resized)
        total_width += new_width

    collage = Image.new('RGB', (total_width, max_height), (255, 255, 255))
    x_offset = 0

    for img in resized_images:
        collage.paste(img, (x_offset, 0))
        x_offset += img.width

    img_byte_arr = BytesIO()
    collage.save(img_byte_arr, format='JPEG', quality=85)
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue()


def encode_image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode('utf-8')


# =========================
# 🔍 АНАЛИЗ ВОЛОС
# =========================
def analyze_hair_characteristics(image_bytes_list: List[bytes]) -> dict:
    """Анализирует волосы и возвращает характеристики"""
    print("   📊 Анализ характеристик волос...")

    collage_bytes = create_collage(image_bytes_list)
    image_base64 = encode_image_to_base64(collage_bytes)

    prompt = """
    Проанализируй коллаж из 3 фото головы (слева-направо: сверху, сзади, сбоку).

    Ответь строго в JSON формате без каких-либо пояснений. Используй только эти ключи:
    {
        "texture": "прямые" или "волнистые" или "курчавые" или "лысый",
        "density": "густые" или "средние" или "редкие" или "отсутствует",
        "part_type": число 0-5,
        "problem_zones": "перечень проблемных зон через запятую"
    }

    Правила:
    - texture: если нет волос → "лысый"
    - density: если нет волос → "отсутствует"
    - part_type: 0=лысый, 1-5=зона пробора слева-направо, 3=нет пробора
    - problem_zones: зоны: "лобная", "теменная", "височная левая", "височная правая", "затылочная", "макушка", "пробор". Если проблем нет → "отсутствуют"

    ВАЖНО: Верни ТОЛЬКО JSON объект.
    """

    payload = {
        "model": "gemini-fast",  # Эта модель поддерживает vision
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }],
        "temperature": 0.3,
        "max_tokens": 300
    }

    response_data = make_api_request(payload, timeout=60)
    raw = response_data["choices"][0]["message"]["content"]
    print(f"   RAW ответ: {raw[:150]}...")
    return parse_analysis_response(raw)


def parse_analysis_response(text: str) -> dict:
    """Парсит ответ ИИ и гарантирует наличие всех ключей"""

    defaults = {
        "texture": "прямые",
        "density": "средние",
        "part_type": 3,
        "problem_zones": "отсутствуют"
    }

    # Очищаем текст от markdown
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Ищем JSON
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if not match:
        print(f"   ⚠️ JSON не найден, использую значения по умолчанию")
        return defaults

    try:
        result = json.loads(match.group(0))

        # Заполняем отсутствующие ключи
        for key in defaults:
            if key not in result:
                result[key] = defaults[key]

        # Корректировка для лысых
        if result.get("texture") == "лысый":
            result["density"] = "отсутствует"
            result["part_type"] = 0

        return result

    except json.JSONDecodeError as e:
        print(f"   ⚠️ Ошибка парсинга JSON: {e}")
        return defaults


# =========================
# 💇 ГЕНЕРАЦИЯ РЕКОМЕНДАЦИИ
# =========================
def generate_recommendation(characteristics: dict) -> dict:
    """Генерирует рекомендацию по технике наращивания/замещения"""
    print("   💈 Подбор техники наращивания...")

    texture = characteristics.get("texture", "прямые")
    density = characteristics.get("density", "средние")
    part_type = characteristics.get("part_type", 3)
    problem_zones = characteristics.get("problem_zones", "отсутствуют")

    prompt = f"""
    Ты мастер по наращиванию волос. Подбери технику исходя из характеристик:
    - Структура: {texture}
    - Густота: {density}
    - Пробор: {part_type} (0=лысый, 1-5=зона слева-направо)
    - Проблемные зоны: {problem_zones}

    Выбери из техник: ленточное наращивание, голливудское наращивание, капсульное наращивание, микро-капсульное наращивание, афро-наращивание. Для проблемных зон используй замещение.

    Ответь строго в JSON без комментариев:
    {{
        "technique_name": "название техники",
        "materials": "список материалов одной строкой через запятую",
        "scheme_description": "описание схемы размещения (1-2 предложения)",
        "instruction": "что крепить, в каком порядке, в какой зоне. 2-3 предложения.",
        "care_recommendations": "рекомендации по уходу. 1-2 предложения."
    }}

    ПРАВИЛА:
    - Не используй трессы нигде кроме голливудского наращивания.
    - Если лысый → предлагай замещение (система замещения волос, парик).
    - Для редких волос → микро-капсульное или ленточное.
    - Для густых → капсульное или голливудское.
    - Для курчавых → афро-наращивание.
    - Без воды, только суть.
    """

    payload = {
        "model": "openai",  # Для текста достаточно обычной модели
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 500
    }

    response_data = make_api_request(payload, timeout=30)
    raw = response_data["choices"][0]["message"]["content"]
    return parse_recommendation_response(raw)


def parse_recommendation_response(text: str) -> dict:
    """Парсит ответ с рекомендацией"""

    defaults = {
        "technique_name": "Микро-капсульное наращивание",
        "materials": "микрокапсулы, кератин, щипцы",
        "scheme_description": "Равномерное распределение по затылочной и височным зонам.",
        "instruction": "Начать с затылка, затем виски. Капсулы крепить на расстоянии 1см от корня.",
        "care_recommendations": "Мыть через 48 часов. Расчесывать от концов к корням."
    }

    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            for key in defaults:
                if key not in result:
                    result[key] = defaults[key]
            return result
    except json.JSONDecodeError:
        pass

    return defaults


# =========================
# 🎯 ОСНОВНАЯ ФУНКЦИЯ
# =========================
def analyze_and_recommend(image_bytes_list: List[bytes]) -> dict:
    """Анализирует волосы и возвращает полную рекомендацию"""

    if len(image_bytes_list) != 3:
        raise ValueError("Требуется ровно 3 фото: сверху, сзади, сбоку")

    char = analyze_hair_characteristics(image_bytes_list)
    rec = generate_recommendation(char)

    return {
        "texture": char['texture'],
        "density": char['density'],
        "part_type": char['part_type'],
        "problem_zones": char['problem_zones'],
        "recommendation": rec
    }

'''
# =========================
# 🧪 ТЕСТИРОВАНИЕ
# =========================
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 АНАЛИЗ ВОЛОС И ПОДБОР ТЕХНИКИ НАРАЩИВАНИЯ")
    print("=" * 60)

    test_images = [
        r"C:\Практика\prstartup\image\img.png",
        r"C:\Практика\prstartup\image\img_1.png",
        r"C:\Практика\prstartup\image\img_2.png"
    ]

    try:
        image_bytes_list = []
        photo_types = ["сверху", "сзади", "сбоку"]

        for i, path in enumerate(test_images):
            print(f"📂 Загрузка фото {i + 1}/3 ({photo_types[i]}): {path}")
            try:
                with open(path, "rb") as f:
                    image_bytes_list.append(f.read())
                print(f"   ✅ Успешно")
            except FileNotFoundError:
                print(f"   ❌ Файл не найден: {path}")
                exit(1)

        print("\n📤 Анализ фото и подбор техники...")
        print("   ⏳ Ожидайте (10-30 секунд)...")

        result = analyze_and_recommend(image_bytes_list)

        chars = result["characteristics"]
        rec = result["recommendation"]

        print("\n" + "=" * 60)
        print("📊 ХАРАКТЕРИСТИКИ ВОЛОС")
        print("=" * 60)
        print(f"💇 Структура:      {chars['texture']}")
        print(f"📏 Густота:        {chars['density']}")
        print(f"🎯 Зона пробора:   {chars['part_type']}")
        print(f"⚠️ Проблемные зоны: {chars['problem_zones']}")

        print("\n" + "=" * 60)
        print("💈 РЕКОМЕНДАЦИЯ МАСТЕРА")
        print("=" * 60)
        print(f"\n🔧 ТЕХНИКА: {rec['technique_name']}")
        print(f"\n📦 МАТЕРИАЛЫ: {rec['materials']}")
        print(f"\n📐 СХЕМА: {rec['scheme_description']}")
        print(f"\n📋 ИНСТРУКЦИЯ: {rec['instruction']}")
        print(f"\n🧴 УХОД: {rec['care_recommendations']}")
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
'''

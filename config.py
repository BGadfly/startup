"""Конфигурация и интеграция с DeepSeek API"""

import os
import json
import requests
from typing import Dict, Optional


class DeepSeekConfig:
    """Конфигурация для работы с DeepSeek API"""
    
    # API конфигурация
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # Установите переменную окружения или вставьте ключ
    
    # Модель для использования
    MODEL = "deepseek-chat"
    
    # Шаблон промпта
    PROMPT_TEMPLATE = """я мастер, подбери технику наращивания или вид замещения волос и напиши инструкцию исходя из характеристик волос и комментария:

характеристики: структура: {texture}, густота: {density}, пробор: {part_type}, проблемные зоны: {problem_zones}

комментарий: {comment}

Напиши:
название техники - только название
материалы - список(одно предложение)
описание схемы - абзац
инструкция (что крепить, в каком порядке и в какой зоне) - до 3 абзацев
рекомендации по уходу - абзац

постарайся не "лить воду"
выбирай из техник: ленточное наращивание, голливудское наращивание, капсульное наращивание, микро-капсульное наращивание, афро-наращивание.
для замещения в проблемных зонах предлагай что хочешь
не используй трессы нигде кроме голливудского наращивания."""
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Получить заголовки для API запроса"""
        if not cls.API_KEY:
            raise ValueError("DEEPSEEK_API_KEY не установлен. Пожалуйста, установите переменную окружения или вставьте ключ в config.py")
        
        return {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def format_problem_zones(cls, problem_zones: Dict) -> str:
        """Форматирует информацию о проблемных зонах для промпта"""
        if not problem_zones.get("has_bald_spots"):
            return "отсутствуют"
        
        zones_text = []
        if problem_zones.get("bald_type"):
            zones_text.append(f"тип: {problem_zones['bald_type']}")
        if problem_zones.get("top_area_percentage", 0) > 0:
            zones_text.append(f"занимает {problem_zones['top_area_percentage']}% площади сверху")
        if problem_zones.get("spot_size_category"):
            zones_text.append(f"размер зоны: {problem_zones['spot_size_category']}")
        if problem_zones.get("spot_locations"):
            zones_text.append(f"локации: {', '.join(problem_zones['spot_locations'])}")
        
        return f"есть проблемные зоны ({', '.join(zones_text)})" if zones_text else "есть проблемные зоны"
    
    @classmethod
    def build_prompt(cls, analysis_result: Dict) -> str:
        """Строит промпт на основе результатов анализа"""
        problem_zones = analysis_result.get("problem_zones", {})
        formatted_zones = cls.format_problem_zones(problem_zones)
        
        return cls.PROMPT_TEMPLATE.format(
            texture=analysis_result.get("texture", "не определено"),
            density=analysis_result.get("density", "не определено"),
            part_type=analysis_result.get("part_type", "не определен"),
            problem_zones=formatted_zones,
            comment=analysis_result.get("user_comment", "нет комментария")
        )
    
    @classmethod
    def get_recommendation(cls, analysis_result: Dict) -> Dict[str, str]:
        """
        Отправляет запрос к DeepSeek API и получает рекомендацию
        
        Args:
            analysis_result: результат анализа из ai_module.py
        
        Returns:
            Словарь с полями:
            - technique: название техники
            - materials: материалы
            - scheme_description: описание схемы
            - instructions: инструкция
            - care_recommendations: рекомендации по уходу
            - full_response: полный ответ API
        """
        if not cls.API_KEY:
            return cls._get_mock_response(analysis_result)
        
        prompt = cls.build_prompt(analysis_result)
        
        payload = {
            "model": cls.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты опытный мастер по наращиванию волос. Отвечай строго по шаблону, без лишней воды."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
        
        try:
            response = requests.post(
                cls.API_URL,
                headers=cls.get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            return cls._parse_response(ai_response)
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к DeepSeek API: {e}")
            return cls._get_mock_response(analysis_result)
    
    @classmethod
    def _parse_response(cls, ai_response: str) -> Dict[str, str]:
        """Парсит ответ API на составные части"""
        result = {
            "technique": "",
            "materials": "",
            "scheme_description": "",
            "instructions": "",
            "care_recommendations": "",
            "full_response": ai_response
        }
        
        lines = ai_response.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if line_lower.startswith('название техники') or line_lower.startswith('название'):
                current_section = 'technique'
                # Извлекаем текст после двоеточия
                if ':' in line:
                    result['technique'] = line.split(':', 1)[1].strip()
                continue
            elif line_lower.startswith('материалы'):
                current_section = 'materials'
                if ':' in line:
                    result['materials'] = line.split(':', 1)[1].strip()
                continue
            elif line_lower.startswith('описание схемы'):
                current_section = 'scheme_description'
                if ':' in line:
                    result['scheme_description'] = line.split(':', 1)[1].strip()
                continue
            elif line_lower.startswith('инструкция'):
                current_section = 'instructions'
                if ':' in line:
                    result['instructions'] = line.split(':', 1)[1].strip()
                continue
            elif line_lower.startswith('рекомендации'):
                current_section = 'care_recommendations'
                if ':' in line:
                    result['care_recommendations'] = line.split(':', 1)[1].strip()
                continue
            
            # Добавляем текст к текущей секции
            if current_section and line.strip():
                if result[current_section]:
                    result[current_section] += ' ' + line.strip()
                else:
                    result[current_section] = line.strip()
        
        # Заполняем пустые поля
        for key in result:
            if not result[key] and key != 'full_response':
                result[key] = "Информация не указана"
        
        return result
    
    @classmethod
    def _get_mock_response(cls, analysis_result: Dict) -> Dict[str, str]:
        """Возвращает тестовый ответ при отсутствии API ключа"""
        texture = analysis_result.get("texture", "")
        density = analysis_result.get("density", "")
        problem_zones = analysis_result.get("problem_zones", {})
        
        # Базовая логика для тестового ответа
        if problem_zones.get("has_bald_spots"):
            technique = "Микро-капсульное наращивание с замещением"
            materials = "Капсулы из кератина (0.5-0.8мм), натуральные волосы, защитный спрей"
            scheme = f"Коррекция пробора {analysis_result.get('part_type', 'стандартный')} с маскировкой проблемных зон"
            instructions = f"1. Очистить и обезжирить волосы. 2. Выделить зоны для замещения: {', '.join(problem_zones.get('spot_locations', ['теменная']))}. 3. Крепить микро-капсулы от затылка к макушке. 4. В проблемных зонах использовать более частый шаг крепления (1-1.5см). 5. Создать естественный объем за счет правильного распределения прядей."
            care = "Использовать бессульфатный шампунь, не спать на мокрых волосах, расчесывать специальной щеткой, посещать коррекцию каждые 2-3 месяца."
        elif texture == "курчавые" or texture == "кудрявые":
            technique = "Афро-наращивание"
            materials = "Натуральные кудрявые волосы, специальный крючок, узелковая техника"
            scheme = f"Плетение базы под структуру {texture} волос"
            instructions = "1. Заплести базовые косички в шахматном порядке. 2. Вплетать пряди методом узелкового крепления. 3. Начинать с нижней затылочной зоны, двигаясь вверх. 4. Оставить свободными краевые зоны для естественности."
            care = "Увлажнять специальными спреями, не расчесывать на сухую, использовать шелковую наволочку."
        elif density == "редкие":
            technique = "Ленточное наращивание"
            materials = "Ленты из натуральных волос (4-6см), термолента, клейкая основа"
            scheme = f"Щадящее наращивание для {density} волос с минимальной нагрузкой"
            instructions = "1. Сделать горизонтальный пробор в затылочной зоне. 2. Крепить ленты от затылка к вискам с отступом 1-1.5см от корней. 3. Каждый последующий ряд на 1-2см выше предыдущего. 4. Использовать ленты разной длины для естественного перехода."
            care = "Мыть голову в вертикальном положении, использовать несмываемый кондиционер, сушить феном в щадящем режиме."
        else:
            technique = "Капсульное наращивание"
            materials = "Термокапсулы из кератина, натуральные волосы, термощипцы"
            scheme = f"Классическое наращивание для {texture} волос, тип пробора: {analysis_result.get('part_type', 'стандартный')}"
            instructions = "1. Разделить волосы на зоны: затылок, виски, макушка. 2. Начинать с нижней затылочной зоны, крепить капсулы в шахматном порядке. 3. Отступать 0.5-1см от корней. 4. На макушке и висках использовать более мелкие капсулы. 5. Формировать пробор после завершения наращивания."
            care = "Избегать масел на корнях за 2 дня до коррекции, использовать кератиновый шампунь, не расчесывать мокрые волосы."
        
        return {
            "technique": technique,
            "materials": materials,
            "scheme_description": scheme,
            "instructions": instructions,
            "care_recommendations": care,
            "full_response": f"Mock response for texture={texture}, density={density}"
        }


# Функция для удобного вызова из приложения
def get_hair_recommendation(analysis_result: Dict) -> Dict[str, str]:
    """
    Основная функция для получения рекомендации от DeepSeek
    
    Args:
        analysis_result: результат из analyze_hair_from_photos
    
    Returns:
        Словарь с рекомендацией
    """
    return DeepSeekConfig.get_recommendation(analysis_result)


# Пример использования
if __name__ == "__main__":
    # Пример результата анализа
    test_analysis = {
        "texture": "кудрявые",
        "density": "средние",
        "part_type": "прямой",
        "problem_zones": {
            "has_bald_spots": True,
            "bald_type": "залысины",
            "top_area_percentage": 25.5,
            "spot_size_category": "5-10см",
            "spot_locations": ["левая височная", "правая височная"]
        },
        "user_comment": "Волосы тонкие, нужен объем и маскировка залысин"
    }
    
    # Получаем рекомендацию
    recommendation = get_hair_recommendation(test_analysis)
    
    # Выводим результат
    print("=" * 50)
    print(f"ТЕХНИКА: {recommendation['technique']}")
    print(f"\nМАТЕРИАЛЫ: {recommendation['materials']}")
    print(f"\nОПИСАНИЕ СХЕМЫ: {recommendation['scheme_description']}")
    print(f"\nИНСТРУКЦИЯ: {recommendation['instructions']}")
    print(f"\nРЕКОМЕНДАЦИИ ПО УХОДУ: {recommendation['care_recommendations']}")
    print("=" * 50)



    # В конце config.py добавьте:

from flask import Flask, request, jsonify
from flask_cors import CORS
import base64

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        
        # Декодируем base64 фото
        photo1_bytes = base64.b64decode(data['photo1'])
        photo2_bytes = base64.b64decode(data['photo2'])
        photo3_bytes = base64.b64decode(data['photo3'])
        comment = data.get('comment', '')
        
        # Импортируем функции из ai_module
        from ai_module import analyze_hair_from_photos
        from config import get_hair_recommendation
        
        # Анализируем фото
        analysis_result = analyze_hair_from_photos(
            photo1_bytes, photo2_bytes, photo3_bytes, comment
        )
        
        # Получаем рекомендацию
        recommendation = get_hair_recommendation(analysis_result)
        
        # Формируем ответ
        response = {
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
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
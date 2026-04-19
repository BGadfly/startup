import json
import requests
import numpy as np
import cv2
from http.server import HTTPServer, BaseHTTPRequestHandler

# Импортируем ваш существующий код анализа
from your_hair_analysis_module import analyze_image

class AliceHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Читаем запрос от Алисы
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request_json = json.loads(post_data)

        try:
            # Извлекаем все изображения из запроса
            image_bytes_list = self.extract_images_from_alice_request(request_json)

            if len(image_bytes_list) != 3:
                raise ValueError("Необходимо ровно 3 фотографии")

            # Анализируем каждое фото
            results = []
            for i, image_bytes in enumerate(image_bytes_list):
                result = analyze_image(image_bytes)
                results.append({
                    f"photo_{i+1}": {
                        "texture": result['texture'],
                        "density": result['density'],
                        "part_type": result['part_type']
            }})

            # Формируем итоговый ответ
            final_result = self.aggregate_results(results)
            response = self.create_alice_response(final_result)

        except Exception as e:
            response = self.create_error_response(f"Ошибка: {str(e)}")

        # Отправляем ответ Алисе
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def extract_images_from_alice_request(self, request_json):
        """Извлекает все изображения из запроса Алисы"""
        images = []
        if 'request' in request_json and 'attachments' in request_json['request']:
            attachments = request_json['request']['attachments']
            for attachment in attachments:
                if attachment['type'] == 'Image':
                    image_url = attachment['image']['original_secure_url']
                    response = requests.get(image_url)
                    response.raise_for_status()
                    images.append(response.content)
        return images


    def aggregate_results(self, results):
        """Объединяет результаты анализа трёх фото"""
        # Простая агрегация — берём наиболее часто встречающиеся значения
        textures = [r['photo_1']['texture'] for r in results]
        densities = [r['photo_1']['density'] for r in results]
        part_types = [r['photo_1']['part_type'] for r in results]

        from collections import Counter
        texture_final = Counter(textures).most_common(1)[0][0]
        density_final = Counter(densities).most_common(1)[0][0]
        part_final = Counter(part_types).most_common(1)[0][0]

        return {
            "texture": texture_final,
            "density": density_final,
            "part_type": part_final,
            "details": results
        }

    def create_alice_response(self, result):
        """Создаёт ответ в формате, понятном Алисе"""
        text = (
            f"По результатам анализа трёх фотографий:\n"
            f"• Тип текстуры волос: {result['texture']}.\n"
            f"• Плотность волос: {result['density']}.\n"
            f"• Тип пробора: {result['part_type']}.\n\n"
            "Анализ завершён!"
        )
        return {
            "version": "1.0",
            "response": {
                "text": text,
                "tts": text,
                "end_session": False
            }
        }

    def create_error_response(self, error_message):
        """Создаёт ответ с ошибкой"""
        return {
            "version": "1.0",
            "response": {
                "text": f"Извините, произошла ошибка: {error_message}",
                "tts": f"Извините, произошла ошибка: {error_message}",
                "end_session": True
            }
        }

def run_server(port=8000):
    server = HTTPServer(('localhost', port), AliceHandler)
    print(f"Сервер запущен на порту {port}")
    server.serve_forever()

if __name__ == '__main__':
    run_server()

"""Главный файл приложения"""

from fastapi import FastAPI
from api import hair_analysis, payment
from db.db import init_db

# Инициализируем базу данных
init_db()

# Создаём приложение
app = FastAPI(
    title="Hair Extension API",
    description="API для подбора наращивания волос с оплатой подписки",
    version="1.0.0"
)

# Подключаем роутеры
app.include_router(hair_analysis.router)
app.include_router(payment.router)


@app.get("/")
def root():
    return {
        "message": "Hair Extension API is running",
        "endpoints": [
            "POST /analyze - анализ волос",
            "GET /subscription/plans - тарифы",
            "POST /subscription/create-payment - создать платёж",
            "POST /subscription/confirm - подтвердить оплату",
            "GET /subscription/status/{user_id} - статус подписки",
            "POST /subscription/use-extension/{user_id} - использовать лимит"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
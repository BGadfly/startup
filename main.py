"""Главный файл приложения"""

import os
from fastapi import FastAPI
from api import hair_analysis, payment, admin
from db.db import init_db

# ✅ Создаём директорию для данных
os.makedirs("data", exist_ok=True)

# ✅ Устанавливаем путь к БД в папку data (чтобы сохранялась в volume)
import db.db as db_module
if not os.environ.get("DB_PATH"):
    db_module.DB_PATH = "data/subscriptions.db"

# Инициализируем базу данных (создаст файл data/subscriptions.db)
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
app.include_router(admin.router, prefix="/api")


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


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    # ✅ Внутри Docker используем 0.0.0.0, локально — 127.0.0.1
    host = "0.0.0.0" if os.environ.get("DOCKER") else "127.0.0.1"
    uvicorn.run(app, host=host, port=8000)
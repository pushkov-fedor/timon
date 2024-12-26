# app/main.py

import logging

from fastapi import FastAPI

from app.api import channels, webhooks

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI()

app.include_router(channels.router, prefix="/channels", tags=["channels"])
app.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"])

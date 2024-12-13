import logging

from fastapi import FastAPI

from app.api import channels

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI()

app.include_router(channels.router, prefix="/channels", tags=["channels"])

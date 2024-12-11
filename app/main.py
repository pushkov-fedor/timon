from fastapi import FastAPI

from app.api import channels

app = FastAPI()

app.include_router(channels.router, prefix="/channels", tags=["channels"])

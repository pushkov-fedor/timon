from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class SubscriptionCreate(BaseModel):
    channel_url: HttpUrl
    callback_url: HttpUrl


class SubscriptionResponse(BaseModel):
    id: int
    channel_id: int
    callback_url: str
    created_at: datetime
    is_active: bool
    channel_title: str | None = None
    channel_photo_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

    # Добавляем маппинг полей
    @classmethod
    def model_validate(cls, obj):
        # Создаем копию данных объекта
        data = {
            "id": obj.id,
            "channel_id": obj.channel_id,
            "callback_url": obj.callback_url,
            "created_at": obj.created_at,
            "is_active": obj.is_active,
            "channel_title": obj.title,  # маппинг title -> channel_title
            "channel_photo_url": obj.photo_url  # маппинг photo_url -> channel_photo_url
        }
        return super().model_validate(data) 
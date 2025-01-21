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

    model_config = ConfigDict(from_attributes=True) 
# app/api/webhooks.py

from fastapi import APIRouter, Depends

from app.api.deps import get_webhook_service
from app.schemas.post import PostWebhook
from app.services.webhook_service import WebhookService

router = APIRouter()

@router.post("/rss")
async def process_rss_webhook(
    post: PostWebhook,
    webhook_service: WebhookService = Depends(get_webhook_service)
):
    """Process incoming webhook from Huginn RSS agent"""
    await webhook_service.process_post(post)
    return {"status": "success"} 
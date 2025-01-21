from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.subscription import Subscription
from tests.factories.post import create_test_post_webhook


def test_process_webhook(client: TestClient, db_session: Session):
    """Test successful webhook processing"""
    # Create test channel in database
    channel = Channel(
        channel_name="test_channel",
        is_monitored=True
    )
    db_session.add(channel)
    db_session.flush()
    
    # Create subscription
    subscription = Subscription(
        channel_id=channel.id,
        callback_url="http://callback.com/webhook"
    )
    db_session.add(subscription)
    db_session.commit()

    # Create test post data
    post_data = create_test_post_webhook(
        url="https://t.me/test_channel/1234",
        title="Test Post"
    )

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=AsyncMock(return_value={"status": "success"})
        )

        response = client.post("/webhook/rss", json=post_data.model_dump())
        
        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        
        mock_post.assert_called_once()


def test_process_webhook_invalid_data(client: TestClient):
    """Test webhook processing with invalid data"""
    invalid_data = {
        "id": "test_1",
        # Missing required fields
    }
    
    response = client.post("/webhook/rss", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_process_webhook_channel_not_found(client: TestClient):
    """Test webhook processing for non-existent channel"""
    post_data = create_test_post_webhook(
        url="https://t.me/nonexistent/1234"
    )
    
    response = client.post("/webhook/rss", json=post_data.model_dump())
    assert response.status_code == 404
    assert "Channel not found" in response.json()["detail"]
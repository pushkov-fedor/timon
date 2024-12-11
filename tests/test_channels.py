# ./tests/test_channels.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_create_channel(client: TestClient, db_session: Session):
    response = client.post(
        "/channels/",
        json={"channel_url": "https://t.me/test_channel"}
    )
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["username"] == "test_channel"

def test_create_duplicate_channel(client: TestClient, db_session: Session):
    # Создаем первый канал
    response = client.post(
        "/channels/",
        json={"channel_url": "https://t.me/test_channel"}
    )
    print(f"First response status: {response.status_code}")
    print(f"First response body: {response.json()}")
    assert response.status_code == 200

    # Пытаемся создать дубликат
    response = client.post(
        "/channels/",
        json={"channel_url": "https://t.me/test_channel"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Channel already exists"

def test_create_channel_invalid_url(client: TestClient, db_session: Session):
    response = client.post(
        "/channels/",
        json={"channel_url": "not_a_url"}
    )
    assert response.status_code == 422
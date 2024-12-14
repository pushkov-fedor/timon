# ./tests/unit/test_huginn_client.py
from unittest.mock import MagicMock, patch

import pytest
import requests
from bs4 import BeautifulSoup

from app.core.exceptions.http_exceptions import HTTPException
from app.services.huginn_client import HuginnClient


@pytest.fixture
def mock_requests_session():
    """
    Фикстура для мокирования requests.Session.
    Создает мок сессии с предустановленными успешными ответами для всех типов запросов.
    Возвращает: MagicMock объект, имитирующий requests.Session
    """
    with patch('requests.Session') as mock:
        session = MagicMock()
        # Настраиваем успешные ответы по умолчанию
        response = MagicMock()
        response.status_code = 200
        response.text = '<html><meta name="csrf-token" content="fake-csrf-token"></html>'
        response.json.return_value = {"status": "ok"}
        session.get.return_value = response
        session.post.return_value = response
        session.request.return_value = response
        mock.return_value = session
        yield session


@pytest.fixture
def huginn_client(mock_requests_session):
    """
    Фикстура для создания тестового экземпляра HuginnClient.
    Мокирует настройки и создает клиент с тестовыми параметрами.
    Возвращает: Настроенный экземпляр HuginnClient
    """
    with patch('app.services.huginn_client.settings') as mock_settings:
        # Настраиваем тестовые настройки
        mock_settings.HUGINN_URL = "http://test-huginn:3000"
        mock_settings.HUGINN_ADMIN_USERNAME = "admin"
        mock_settings.HUGINN_ADMIN_PASSWORD = "password"
        
        client = HuginnClient()
        return client


class TestHuginnClient:
    def test_authenticate_success(self, mock_requests_session, huginn_client):
        """
        Тест успешной аутентификации в Huginn.
        Проверяет:
        - Корректный вызов GET и POST запросов
        - Правильное извлечение и сохранение CSRF-токена
        """
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.text = '<html><meta name="csrf-token" content="fake-csrf-token"></html>'
        mock_requests_session.get.return_value = login_response
        mock_requests_session.post.return_value = login_response

        huginn_client._authenticate()
        
        assert mock_requests_session.get.called
        assert mock_requests_session.post.called
        assert huginn_client.csrf_token == "fake-csrf-token"

    def test_authenticate_failed_login(self, mock_requests_session, huginn_client):
        """
        Тест неудачной аутентификации.
        Проверяет:
        - Корректную обработку ошибки аутентификации
        - Генерацию правильного исключения с кодом 401
        """
        error_response = MagicMock()
        error_response.status_code = 200
        error_response.text = "Invalid Login or password"
        mock_requests_session.post.return_value = error_response

        with pytest.raises(HTTPException) as exc:
            huginn_client._authenticate()
        assert exc.value.status_code == 401

    def test_create_rss_agent_success(self, huginn_client, mock_requests_session):
        """
        Тест успешного создания RSS агента.
        Проверяет:
        - Корректное формирование POST запроса
        - Правильные параметры создания агента
        - Возврат ID созданного агента
        """
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"id": 1}
        mock_requests_session.request.return_value = response

        agent_id = huginn_client.create_rss_agent("test_channel")

        assert agent_id == 1
        args, kwargs = mock_requests_session.request.call_args
        assert args[0] == "POST"
        assert "agents.json" in args[1]
        assert kwargs['json']['agent']['type'] == "Agents::RssAgent"

    def test_create_post_agent_success(self, huginn_client, mock_requests_session):
        """
        Тест успешного создания Post агента.
        Проверяет:
        - Корректное формирование POST запроса
        - Правильные параметры создания агента
        - Возврат ID созданного агента
        """
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"id": 2}
        mock_requests_session.request.return_value = response

        agent_id = huginn_client.create_post_agent("test_channel")

        assert agent_id == 2
        args, kwargs = mock_requests_session.request.call_args
        assert args[0] == "POST"
        assert kwargs['json']['agent']['type'] == "Agents::PostAgent"

    def test_link_agents_success(self, huginn_client, mock_requests_session):
        """
        Тест успешного связывания агентов.
        Проверяет:
        - Корректное формирование PUT запроса
        - Правильные параметры связывания агентов
        """
        response = MagicMock()
        response.status_code = 200
        mock_requests_session.request.return_value = response

        huginn_client.link_agents(1, 2)

        args, kwargs = mock_requests_session.request.call_args
        assert args[0] == "PUT"
        assert "/agents/1.json" in args[1]
        assert kwargs['json']['agent']['receiver_ids'] == [2]

    def test_delete_agent_success(self, huginn_client, mock_requests_session):
        """
        Тест успешного удаления агента.
        Проверяет:
        - Корректное формирование DELETE запроса
        - Правильный URL для удаления агента
        """
        response = MagicMock()
        response.status_code = 200
        mock_requests_session.request.return_value = response

        huginn_client.delete_agent(1)

        args, kwargs = mock_requests_session.request.call_args
        assert args[0] == "DELETE"
        assert "/agents/1.json" in args[1]

    def test_get_agent_status_success(self, huginn_client, mock_requests_session):
        """
        Тест получения статуса агента.
        Проверяет:
        - Корректное формирование GET запроса
        - Правильную обработку ответа
        - Возврат статуса агента
        """
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"status": "ok"}
        mock_requests_session.request.return_value = response

        status = huginn_client.get_agent_status(1)

        assert status == {"status": "ok"}
        args, kwargs = mock_requests_session.request.call_args
        assert args[0] == "GET"
        assert "/agents/1.json" in args[1]

    def test_get_agent_links_success(self, huginn_client, mock_requests_session):
        """
        Тест получения связей агента.
        Проверяет:
        - Корректное формирование GET запроса
        - Правильную обработку ответа с информацией о связях
        - Возврат структурированных данных о связях
        """
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "source_ids": [1],
            "receiver_ids": [2]
        }
        mock_requests_session.request.return_value = response

        links = huginn_client.get_agent_links(1)

        assert links == {"sources": [1], "receivers": [2]}
        args, kwargs = mock_requests_session.request.call_args
        assert args[0] == "GET"
        assert "/agents/1.json" in args[1]

    def test_make_authenticated_request_retry_auth(self, huginn_client, mock_requests_session):
        """
        Тест повторной аутентификации при истечении сессии.
        Проверяет:
        - Обработку 302 редиректа (признак истечения сессии)
        - Повторную попытку запроса после реаутентификации
        - Успешное выполнение запроса после повторной аутентификации
        """
        redirect_response = MagicMock()
        redirect_response.status_code = 302
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": "success"}
        
        mock_requests_session.request.side_effect = [redirect_response, success_response]

        response = huginn_client._make_authenticated_request("GET", "/test")

        assert response.status_code == 200
        assert mock_requests_session.request.call_count >= 2

    def test_make_authenticated_request_error(self, huginn_client, mock_requests_session):
        """
        Тест обработки ошибок при выполнении запроса.
        Проверяет:
        - Корректную обработку ошибки сервера (500)
        - Генерацию соответствующего исключения
        """
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        mock_requests_session.request.return_value = error_response

        with pytest.raises(HTTPException) as exc:
            huginn_client._make_authenticated_request("GET", "/test")
        assert exc.value.status_code == 500
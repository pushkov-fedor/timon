import logging
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions.http_exceptions import HTTPException

logger = logging.getLogger(__name__)

class HuginnClient:
    def __init__(self):
        self.base_url = settings.HUGINN_URL
        self.admin_username = settings.HUGINN_ADMIN_USERNAME
        self.admin_password = settings.HUGINN_ADMIN_PASSWORD
        self.session = requests.Session()
        self.csrf_token = None
        self._authenticate()

    def _get_csrf_token(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')
        csrf = soup.find('meta', attrs={'name': 'csrf-token'})
        if not csrf:
            raise HTTPException(status_code=500, detail="CSRF token not found in Huginn login page")
        return csrf.get('content')

    def _authenticate(self):
        logger.info(f"Attempting to authenticate with Huginn at {self.base_url}")
        
        # Get login page
        login_url = f"{self.base_url}/users/sign_in"
        logger.info(f"Getting login page from {login_url}")
        
        try:
            response = self.session.get(login_url)
            logger.info(f"Login page response status: {response.status_code}")
            logger.debug(f"Login page content: {response.text[:500]}")  # First 500 chars
            
            if response.status_code != 200:
                logger.error(f"Failed to get login page. Status: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to load Huginn login page")
            
            self.csrf_token = self._get_csrf_token(response.text)
            logger.info(f"Got CSRF token: {self.csrf_token[:10]}...")  # First 10 chars
            
            # Login
            login_data = {
                "user[login]": self.admin_username,
                "user[password]": self.admin_password,
                "user[remember_me]": "1",
                "authenticity_token": self.csrf_token,
                "commit": "Log in"
            }
            
            logger.info("Sending login request...")
            logger.debug(f"Login data: {login_data}")
            
            response = self.session.post(
                login_url,
                data=login_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'text/html,application/json',
                    'X-CSRF-Token': self.csrf_token
                }
            )
            
            logger.info(f"Login response status: {response.status_code}")
            logger.debug(f"Login response content: {response.text[:500]}")
            
            if "Invalid Login or password" in response.text:
                logger.error("Invalid credentials")
                raise HTTPException(status_code=401, detail="Invalid Huginn credentials")
            
            if response.status_code != 200:
                logger.error(f"Login failed with status {response.status_code}")
                raise HTTPException(status_code=500, detail="Failed to authenticate with Huginn")
            
            self.csrf_token = self._get_csrf_token(response.text)
            logger.info("Successfully authenticated with Huginn")
            
        except requests.RequestException as e:
            logger.error(f"Request error during authentication: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")

    def create_rss_agent(self, channel_username: str) -> int:
        logger.info(f"Creating RSS agent for channel: {channel_username}")
        
        payload = {
            "agent": {
                "type": "Agents::RssAgent",
                "name": f"RSS Monitor - {channel_username}",
                "schedule": "every_1m",
                "options": {
                    "expected_update_period_in_days": "2",
                    "url": [f"http://rsshub:1200/telegram/channel/{channel_username}"],
                    "mode": "on_change",
                    "type": "json",
                    "clean": "false"
                }
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-CSRF-Token': self.csrf_token
        }
        
        response = self._make_authenticated_request(
            "POST",
            "/agents.json",
            json=payload,
            headers=headers
        )
        
        try:
            return response.json()['id']
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse Huginn response: {e}")
            logger.error(f"Response content: {response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create RSS agent: {str(e)}"
            )

    def _make_authenticated_request(
        self, 
        method: str, 
        endpoint: str, 
        retry_auth: bool = True,
        **kwargs
    ) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop('headers', {})
        headers['X-CSRF-Token'] = self.csrf_token
        
        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Request params: {kwargs}")
        
        response = self.session.request(method, url, headers=headers, **kwargs)
        
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        logger.debug(f"Response content: {response.text[:500]}")  # Логируем только первые 500 символов
        
        # Если получили редирект на страницу логина и это первая попытка
        if response.status_code == 302 and retry_auth:
            logger.info("Session expired, re-authenticating...")
            self._authenticate()
            return self._make_authenticated_request(
                method, 
                endpoint, 
                retry_auth=False,  # Предотвращаем бесконечную рекурсию
                **kwargs
            )
            
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Huginn request failed: {response.text}"
            )
            
        return response

    def create_post_agent(self, channel_username: str) -> int:
        """Create a Post agent that will send events to the webhook URL"""
        logger.info(f"Creating Post agent for channel: {channel_username}")
        
        webhook_url = f"{settings.APP_HOST}/webhook/rss"
        logger.info(f"Configuring Post agent to send webhooks to: {webhook_url}")
        
        payload = {
            "agent": {
                "type": "Agents::PostAgent",
                "name": f"Post Agent - {channel_username}",
                "payload_mode": "merge",
                "options": {
                    "post_url": webhook_url,
                    "expected_receive_period_in_days": "2",
                    "content_type": "json",
                    "method": "post",
                    "payload": {
                        "title": "{{ title }}",
                        "link": "{{ url }}",
                        "guid": "{{ guid }}",
                        "description": "{{ description }}",
                        "published": "{{ published }}"
                    },
                    "headers": {
                        "Content-Type": "application/json"
                    }
                }
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-CSRF-Token': self.csrf_token
        }
        
        response = self._make_authenticated_request(
            "POST",
            "/agents.json",
            json=payload,
            headers=headers
        )
        
        try:
            return response.json()['id']
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse Huginn response: {e}")
            logger.error(f"Response content: {response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create post agent: {str(e)}"
            )

    def link_agents(self, source_agent_id: int, target_agent_id: int) -> None:
        """Link two agents together so the source agent can send events to the target agent"""
        logger.info(f"Linking agents {source_agent_id} -> {target_agent_id}")
        
        payload = {
            "agent": {
                "receiver_ids": [target_agent_id]
            },
            "commit": "Update"
        }
        
        endpoint = f"/agents/{source_agent_id}.json"
        response = self._make_authenticated_request(
            "PUT",
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to link agents. Response: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to link agents {source_agent_id} and {target_agent_id}"
            )

    def delete_agent(self, agent_id: int) -> None:
        endpoint = f"/agents/{agent_id}.json"
        response = self._make_authenticated_request("DELETE", endpoint)
        if response.status_code not in [200, 204]:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Failed to delete agent {agent_id} in Huginn"
            ) 

    def start_agent(self, agent_id: int) -> None:
        """Start a Huginn agent by ID"""
        logger.info(f"Starting agent {agent_id}")
        
        endpoint = f"/agents/{agent_id}/run"
        response = self._make_authenticated_request(
            "POST",
            endpoint,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code not in [200, 202]:
            logger.error(f"Failed to start agent {agent_id}. Response: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to start agent {agent_id}"
            )

    def get_agent_status(self, agent_id: int) -> dict:
        """Get status of a Huginn agent"""
        endpoint = f"/agents/{agent_id}.json"
        response = self._make_authenticated_request("GET", endpoint)
        
        if response.status_code != 200:
            logger.error(f"Failed to get agent status. Response: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get agent status for {agent_id}"
            )
        
        return response.json()

    def get_agent_links(self, agent_id: int) -> list:
        """Get agent's links (sources and receivers)"""
        endpoint = f"/agents/{agent_id}.json"
        response = self._make_authenticated_request("GET", endpoint)
        
        if response.status_code != 200:
            logger.error(f"Failed to get agent info. Response: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get agent info for {agent_id}"
            )
        
        agent_data = response.json()
        # В Huginn есть два типа связей:
        # source_ids - агенты, от которых получаем события
        # receiver_ids - агенты, которым отправляем события
        sources = agent_data.get("source_ids", [])
        receivers = agent_data.get("receiver_ids", [])
        
        logger.debug(f"Agent {agent_id} sources: {sources}")
        logger.debug(f"Agent {agent_id} receivers: {receivers}")
        
        return {
            "sources": sources,
            "receivers": receivers
        }
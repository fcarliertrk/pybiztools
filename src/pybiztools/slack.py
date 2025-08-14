import os
from typing import Optional, Any

from aiohttp import ClientSession

from .logger import setup_logger

logger = setup_logger('pybiztools.slack')


class SlackService:

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.session = None
        self.api_base_url = os.getenv("SLACK_API_BASE_URL", "")

    async def _get_session(self):
        if self.session is None:
            self.session = ClientSession()
        return self.session

    async def send_message(self, message: dict) -> Optional[Any]:
        try:
            session = await self._get_session()
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json",
            }
            async with session.post(
                self.api_base_url + "/chat.postMessage", headers=headers, json=message
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Error while sending Slack message, error is: {error_text}"
                    )
                    return None
                return await response.json()
        except Exception as err:
            logger.error(f"Error while posting to Slack API, err is: {err}")
            return None

    async def __aenter__(self) -> "SlackService":
        await self._get_session()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None

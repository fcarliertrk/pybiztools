from typing import Optional, Any
from azure.communication.email.aio import EmailClient
from .logger import logger


class EmailService:
    def __init__(self, conn_str: str) -> None:
        self.client: EmailClient = EmailClient.from_connection_string(conn_str)

    async def send_email(self, message: dict) -> Optional[Any]:
        try:
            result = await self.client.begin_send(message)
            return result
        except Exception as err:
            logger.error(f"Error while sending email, err is: {err}")
            logger.error(f"Message is: {message}")
        return None

    async def __aenter__(self) -> "EmailService":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        await self.client.close()

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pybiztools.email import EmailService


class TestEmailService:

    @pytest.fixture
    @patch("pybiztools.email.EmailClient")
    def email_service(self, mock_email_client):
        mock_client = AsyncMock()
        mock_email_client.from_connection_string.return_value = mock_client
        service = EmailService("test_connection_string")
        service.mock_client = mock_client  # Store reference for test access
        return service

    def test_init(self, email_service):
        assert email_service.client is not None
        assert hasattr(email_service.client, "from_connection_string")

    @patch("pybiztools.email.EmailClient")
    def test_init_creates_client_with_connection_string(self, mock_email_client):
        mock_client = MagicMock()
        mock_email_client.from_connection_string.return_value = mock_client

        service = EmailService("test_conn_str")

        mock_email_client.from_connection_string.assert_called_once_with(
            "test_conn_str"
        )
        assert service.client == mock_client

    @pytest.mark.asyncio
    @patch("pybiztools.email.logger")
    async def test_send_email_success(self, mock_logger, email_service):
        mock_result = AsyncMock()
        email_service.client = AsyncMock()
        email_service.client.begin_send.return_value = mock_result

        message = {
            "senderAddress": "sender@example.com",
            "recipients": {"to": [{"address": "recipient@example.com"}]},
            "content": {"subject": "Test Email", "plainText": "Test message"},
        }

        result = await email_service.send_email(message)

        email_service.client.begin_send.assert_called_once_with(message)
        assert result == mock_result
        mock_logger.error.assert_not_called()

    @pytest.mark.asyncio
    @patch("pybiztools.email.logger")
    async def test_send_email_exception(self, mock_logger, email_service):
        email_service.client = AsyncMock()
        email_service.client.begin_send.side_effect = Exception("Email sending failed")

        message = {"test": "message"}

        result = await email_service.send_email(message)

        assert result is None
        mock_logger.error.assert_any_call(
            "Error while sending email, err is: Email sending failed"
        )
        mock_logger.error.assert_any_call("Message is: {'test': 'message'}")

    @pytest.mark.asyncio
    async def test_context_manager_enter(self, email_service):
        async with email_service as service:
            assert service == email_service

    @pytest.mark.asyncio
    async def test_context_manager_exit(self, email_service):
        email_service.client = AsyncMock()

        async with email_service:
            pass

        email_service.client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_exit_with_exception(self, email_service):
        email_service.client = AsyncMock()

        try:
            async with email_service:
                raise ValueError("Test exception")
        except ValueError:
            pass

        email_service.client.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("pybiztools.email.logger")
    async def test_send_email_with_complex_message(self, mock_logger, email_service):
        mock_result = AsyncMock()
        email_service.client = AsyncMock()
        email_service.client.begin_send.return_value = mock_result

        complex_message = {
            "senderAddress": "noreply@company.com",
            "recipients": {
                "to": [
                    {"address": "user1@example.com", "displayName": "User One"},
                    {"address": "user2@example.com", "displayName": "User Two"},
                ],
                "cc": [{"address": "manager@company.com"}],
                "bcc": [{"address": "audit@company.com"}],
            },
            "content": {
                "subject": "Important Update",
                "plainText": "This is the plain text version",
                "html": "<h1>This is the HTML version</h1>",
            },
            "attachments": [
                {
                    "name": "document.pdf",
                    "contentType": "application/pdf",
                    "contentInBase64": "base64encodedcontent",
                }
            ],
        }

        result = await email_service.send_email(complex_message)

        email_service.client.begin_send.assert_called_once_with(complex_message)
        assert result == mock_result
        mock_logger.error.assert_not_called()

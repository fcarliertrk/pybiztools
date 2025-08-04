import pytest
from unittest.mock import AsyncMock, patch
from pybiztools.slack import SlackService


class TestSlackService:

    @pytest.fixture
    def slack_service(self):
        return SlackService("test_bot_token")

    def test_init(self, slack_service):
        assert slack_service.bot_token == "test_bot_token"
        assert slack_service.session is None
        assert slack_service.api_base_url == ""

    @patch.dict("os.environ", {"SLACK_API_BASE_URL": "https://custom-slack-api.com"})
    def test_init_with_custom_api_url(self):
        service = SlackService("token")
        assert service.api_base_url == "https://custom-slack-api.com"

    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, slack_service):
        with patch("pybiztools.slack.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            result = await slack_service._get_session()

            mock_session_class.assert_called_once()
            assert slack_service.session == mock_session
            assert result == mock_session

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self, slack_service):
        existing_session = AsyncMock()
        slack_service.session = existing_session

        result = await slack_service._get_session()

        assert result == existing_session

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"SLACK_API_BASE_URL": "https://slack.com/api"})
    async def test_send_message_success(self, slack_service):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "ok": True,
            "message": {"ts": "1234567890.123"},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        slack_service.session = mock_session
        slack_service.api_base_url = "https://slack.com/api"

        message = {
            "channel": "#general",
            "text": "Hello, World!",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "Hello, *World*!"},
                }
            ],
        }

        result = await slack_service.send_message(message)

        expected_headers = {
            "Authorization": "Bearer test_bot_token",
            "Content-Type": "application/json",
        }

        mock_session.post.assert_called_once_with(
            "https://slack.com/api/chat.postMessage",
            headers=expected_headers,
            json=message,
        )
        assert result == {"ok": True, "message": {"ts": "1234567890.123"}}

    @pytest.mark.asyncio
    @patch("pybiztools.slack.logger")
    async def test_send_message_http_error(self, mock_logger, slack_service):
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request: channel_not_found"

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        slack_service.session = mock_session
        slack_service.api_base_url = "https://slack.com/api"

        message = {"channel": "#nonexistent", "text": "Test"}

        result = await slack_service.send_message(message)

        assert result is None
        mock_logger.error.assert_called_once_with(
            "Error while sending Slack message, error is: Bad Request: channel_not_found"
        )

    @pytest.mark.asyncio
    @patch("pybiztools.slack.logger")
    async def test_send_message_exception(self, mock_logger, slack_service):
        mock_session = AsyncMock()
        mock_session.post.side_effect = Exception("Network error")
        slack_service.session = mock_session

        message = {"channel": "#general", "text": "Test"}

        result = await slack_service.send_message(message)

        assert result is None
        mock_logger.error.assert_called_once_with(
            "Error while posting to Slack API, err is: Network error"
        )

    @pytest.mark.asyncio
    async def test_send_message_creates_session_if_none(self, slack_service):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"ok": True}

        with patch("pybiztools.slack.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session

            slack_service.api_base_url = "https://slack.com/api"
            message = {"channel": "#general", "text": "Test"}

            result = await slack_service.send_message(message)

            mock_session_class.assert_called_once()
            assert slack_service.session == mock_session
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_context_manager_enter(self, slack_service):
        with patch("pybiztools.slack.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            async with slack_service as service:
                assert service == slack_service
                assert slack_service.session == mock_session

    @pytest.mark.asyncio
    async def test_context_manager_exit_with_session(self, slack_service):
        mock_session = AsyncMock()
        slack_service.session = mock_session

        async with slack_service:
            pass

        mock_session.close.assert_called_once()
        assert slack_service.session is None

    @pytest.mark.asyncio
    async def test_context_manager_exit_without_session(self, slack_service):
        slack_service.session = None

        async with slack_service:
            pass

        assert slack_service.session is None

    @pytest.mark.asyncio
    async def test_context_manager_exit_with_exception(self, slack_service):
        mock_session = AsyncMock()
        slack_service.session = mock_session

        try:
            async with slack_service:
                raise ValueError("Test exception")
        except ValueError:
            pass

        mock_session.close.assert_called_once()
        assert slack_service.session is None

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"SLACK_API_BASE_URL": "https://slack.com/api"})
    async def test_send_complex_message(self, slack_service):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "ok": True,
            "channel": "C1234567890",
            "ts": "1405894322.002768",
            "message": {"text": "Complex message", "user": "U2147483698"},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        slack_service.session = mock_session
        slack_service.api_base_url = "https://slack.com/api"

        complex_message = {
            "channel": "#general",
            "text": "Fallback text",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "System Alert"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "The system is experiencing high CPU usage: *95%*",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Investigate"},
                            "action_id": "investigate_button",
                        }
                    ],
                },
            ],
            "attachments": [
                {
                    "color": "danger",
                    "fields": [
                        {"title": "CPU Usage", "value": "95%", "short": True},
                        {"title": "Memory Usage", "value": "78%", "short": True},
                    ],
                }
            ],
        }

        result = await slack_service.send_message(complex_message)

        expected_headers = {
            "Authorization": "Bearer test_bot_token",
            "Content-Type": "application/json",
        }

        mock_session.post.assert_called_once_with(
            "https://slack.com/api/chat.postMessage",
            headers=expected_headers,
            json=complex_message,
        )
        assert result["ok"] is True
        assert "ts" in result

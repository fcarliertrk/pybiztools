import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pybiztools.google_drive import GoogleDrive


class TestGoogleDrive:

    @pytest.fixture
    @patch.dict("os.environ", {"SERVICE_ACCOUNT_FILE": "/path/to/service_account.json"})
    @patch(
        "builtins.open",
        mock_open(read_data='{"type": "service_account", "project_id": "test"}'),
    )
    @patch("pybiztools.google_drive.ServiceAccountCreds")
    def google_drive(self, mock_creds):
        return GoogleDrive()

    @patch.dict("os.environ", {"SERVICE_ACCOUNT_FILE": "/path/to/service_account.json"})
    @patch(
        "builtins.open",
        mock_open(read_data='{"type": "service_account", "project_id": "test"}'),
    )
    @patch("pybiztools.google_drive.ServiceAccountCreds")
    def test_init(self, mock_creds):
        drive = GoogleDrive()

        mock_creds.assert_called_once()
        assert drive.drive_api is None

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    async def test_initialize(self, mock_aiogoogle_class, google_drive):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        mock_drive_api = MagicMock()
        mock_aiogoogle.discover.return_value = mock_drive_api

        result = await google_drive.initialize()

        mock_aiogoogle.discover.assert_called_once_with("drive", "v3")
        assert google_drive.drive_api == mock_drive_api
        assert result == google_drive

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    async def test_get_folder_id_found(self, mock_aiogoogle_class, google_drive):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        mock_aiogoogle.as_service_account.return_value = {
            "files": [{"id": "folder123", "name": "Test Folder"}]
        }
        google_drive.drive_api = MagicMock()

        result = await google_drive.get_folder_id("Test Folder")

        assert result == "folder123"
        mock_aiogoogle.as_service_account.assert_called_once()

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    async def test_get_folder_id_not_found(self, mock_aiogoogle_class, google_drive):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        mock_aiogoogle.as_service_account.return_value = {"files": []}
        google_drive.drive_api = MagicMock()

        result = await google_drive.get_folder_id("Nonexistent Folder")

        assert result is None

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    @patch("pybiztools.google_drive.logger")
    async def test_create_folder(self, mock_logger, mock_aiogoogle_class, google_drive):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        mock_aiogoogle.as_service_account.return_value = {"id": "new_folder_id"}
        google_drive.drive_api = MagicMock()

        result = await google_drive.create_folder("New Folder")

        assert result == "new_folder_id"
        mock_logger.info.assert_called_once_with(
            "Folder New Folder created with ID: new_folder_id"
        )

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    @patch("pybiztools.google_drive.logger")
    async def test_create_folder_with_parent(
        self, mock_logger, mock_aiogoogle_class, google_drive
    ):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        mock_aiogoogle.as_service_account.return_value = {"id": "child_folder_id"}
        google_drive.drive_api = MagicMock()

        result = await google_drive.create_folder("Child Folder", "parent_folder_id")

        assert result == "child_folder_id"
        # Verify the folder metadata includes parent
        call_args = mock_aiogoogle.as_service_account.call_args
        metadata = call_args[0][0].json
        assert "parents" in metadata
        assert metadata["parents"] == ["parent_folder_id"]

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    @patch("pybiztools.google_drive.logger")
    @patch("builtins.open", mock_open(read_data=b"test file content"))
    @patch("os.path.basename", return_value="test_file.txt")
    async def test_upload_file(
        self, mock_basename, mock_logger, mock_aiogoogle_class, google_drive
    ):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        mock_aiogoogle.as_service_account.return_value = {"id": "uploaded_file_id"}
        google_drive.drive_api = MagicMock()

        result = await google_drive.upload_file(
            "/path/to/test_file.txt", "folder_id", "text/plain"
        )

        assert result == "uploaded_file_id"
        mock_logger.info.assert_called_once_with(
            "File uploaded with ID uploaded_file_id"
        )

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    async def test_get_folder_permissions(self, mock_aiogoogle_class, google_drive):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        mock_aiogoogle.as_service_account.return_value = {
            "permissions": [
                {"type": "user", "emailAddress": "user1@example.com", "role": "reader"},
                {"type": "user", "emailAddress": "user2@example.com", "role": "writer"},
                {"type": "domain", "domain": "example.com", "role": "reader"},
            ]
        }
        google_drive.drive_api = MagicMock()

        result = await google_drive.get_folder_permissions(
            "folder_id", ["user1@example.com"]
        )

        expected = {"user1@example.com", "user2@example.com"}
        assert result == expected

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    @patch("pybiztools.google_drive.logger")
    async def test_get_folder_permissions_error(
        self, mock_logger, mock_aiogoogle_class, google_drive
    ):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        mock_aiogoogle.as_service_account.side_effect = Exception("Permission error")
        google_drive.drive_api = MagicMock()

        with pytest.raises(Exception):
            await google_drive.get_folder_permissions("folder_id", ["user@example.com"])

        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    @patch("pybiztools.google_drive.logger")
    async def test_delete_folder(self, mock_logger, mock_aiogoogle_class, google_drive):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle
        google_drive.drive_api = MagicMock()

        await google_drive.delete_folder("folder_to_delete")

        mock_aiogoogle.as_service_account.assert_called_once()
        mock_logger.info.assert_called_once_with(
            "Permanently deleted folder with id folder_to_delete"
        )

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    @patch("pybiztools.google_drive.logger")
    async def test_share_folder_recursively_success(
        self, mock_logger, mock_aiogoogle_class, google_drive
    ):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle

        # Mock get_folder_permissions to return empty set (no existing permissions)
        google_drive.get_folder_permissions = AsyncMock(return_value=set())

        # Mock successful permission creation
        mock_aiogoogle.as_service_account.return_value = {"id": "permission_id_123"}
        google_drive.drive_api = MagicMock()

        emails = ["user1@example.com", "user2@example.com"]
        result = await google_drive.share_folder_recursively(
            "folder_id", emails, "commenter"
        )

        expected = {
            "user1@example.com": "permission_id_123",
            "user2@example.com": "permission_id_123",
        }
        assert result == expected
        assert mock_logger.info.call_count == 2

    @pytest.mark.asyncio
    async def test_share_folder_recursively_empty_emails(self, google_drive):
        with pytest.raises(ValueError, match="Email addresses list cannot be empty"):
            await google_drive.share_folder_recursively("folder_id", [])

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    @patch("pybiztools.google_drive.logger")
    async def test_share_folder_recursively_existing_permissions(
        self, mock_logger, mock_aiogoogle_class, google_drive
    ):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle

        # Mock get_folder_permissions to return existing permissions
        google_drive.get_folder_permissions = AsyncMock(
            return_value={"user1@example.com"}
        )

        # Mock successful permission creation for new user only
        mock_aiogoogle.as_service_account.return_value = {"id": "permission_id_456"}
        google_drive.drive_api = MagicMock()

        emails = ["user1@example.com", "user2@example.com"]
        result = await google_drive.share_folder_recursively(
            "folder_id", emails, "reader"
        )

        # Only user2 should get new permission (user1 already has access)
        expected = {"user2@example.com": "permission_id_456"}
        assert result == expected
        # Only one info call for the new permission
        mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    @patch("pybiztools.google_drive.Aiogoogle")
    @patch("pybiztools.google_drive.logger")
    async def test_share_folder_recursively_permission_error(
        self, mock_logger, mock_aiogoogle_class, google_drive
    ):
        mock_aiogoogle = AsyncMock()
        mock_aiogoogle_class.return_value.__aenter__.return_value = mock_aiogoogle

        # Mock get_folder_permissions to return empty set
        google_drive.get_folder_permissions = AsyncMock(return_value=set())

        # Mock permission creation failure
        mock_aiogoogle.as_service_account.side_effect = Exception("Permission denied")
        google_drive.drive_api = MagicMock()

        emails = ["user1@example.com"]
        result = await google_drive.share_folder_recursively(
            "folder_id", emails, "commenter"
        )

        expected = {"user1@example.com": None}
        assert result == expected
        mock_logger.error.assert_called_once()

import os
import json

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds

from .logger import logger

# Define the auth scopes
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")


class GoogleDrive:
    def __init__(self):
        # Initialize ServiceAccountCreds
        with open(SERVICE_ACCOUNT_FILE, "r") as file:
            self.service_account_creds = ServiceAccountCreds(
                scopes=SCOPES, **json.load(file)
            )
        self.drive_api = None

    async def initialize(self):
        """Initialize the Google Drive API client"""
        async with Aiogoogle(
            service_account_creds=self.service_account_creds
        ) as aiogoogle:
            self.drive_api = await aiogoogle.discover("drive", "v3")
            return self

    async def get_folder_id(self, folder_name):
        """Get the folder id by name asynchronously"""
        async with Aiogoogle(
            service_account_creds=self.service_account_creds
        ) as aiogoogle:
            # Search for folders with the specified name
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
            results = await aiogoogle.as_service_account(
                self.drive_api.files.list(
                    q=query, pageSize=10, fields="files(id, name)"
                )
            )

            # Return the first matching folder if found
            files = results.get("files", [])
            if files:
                return files[0]["id"]

            return None

    # TODO: Update the create folder function to be create_if_not_exists...
    async def create_folder(self, folder_name, parent_folder_id=None):
        """Create a folder with the specified name asynchronously"""
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_folder_id:
            folder_metadata["parents"] = [parent_folder_id]

        async with Aiogoogle(
            service_account_creds=self.service_account_creds
        ) as aiogoogle:
            # Create the folder
            folder = await aiogoogle.as_service_account(
                self.drive_api.files.create(json=folder_metadata, fields="id")
            )

            logger.info(f"Folder {folder_name} created with ID: {folder.get('id')}")
            return folder.get("id")

    async def upload_file(self, file_path, folder_id, mimetype):
        """Upload file to the specified folder asynchronously"""
        file_name = os.path.basename(file_path)

        # For file uploads with Aiogoogle, we need to use multipart upload
        async with Aiogoogle(
            service_account_creds=self.service_account_creds
        ) as aiogoogle:
            # First prepare the metadata
            file_metadata = {"name": file_name, "parents": [folder_id]}

            # Read file content
            with open(file_path, "rb") as file_content:
                file_data = file_content.read()

            # Upload file using multipart upload
            file = await aiogoogle.as_service_account(
                self.drive_api.files.create(
                    json=file_metadata,
                    upload_file=file_data,
                    fields="id",
                    uploadType="multipart",
                    contentType=mimetype,
                )
            )

            logger.info(f"File uploaded with ID {file.get('id')}")
            return file.get("id")

    async def get_folder_permissions(self, folder_id, email_addresses):
        async with Aiogoogle(
            service_account_creds=self.service_account_creds
        ) as aiogoogle:
            try:
                permissions_response = await aiogoogle.as_service_account(
                    self.drive_api.permissions.list(
                        fileId=folder_id,
                        fields="permissions(id, emailAddress, role, type)",
                        supportsAllDrives=True,
                    )
                )
                permissions = permissions_response.get("permissions", [])
                return {
                    permission["emailAddress"]
                    for permission in permissions
                    if permission.get("type") == "user" and "emailAddress" in permission
                }
            except Exception as err:
                logger.error(
                    f"Error checking folder sharing for {folder_id}, error is {str(err)}"
                )
                raise err

    async def delete_folder(self, folder_id):
        async with Aiogoogle(
            service_account_creds=self.service_account_creds
        ) as aiogoogle:
            await aiogoogle.as_service_account(
                self.drive_api.files.delete(fileId=folder_id, supportsAllDrives=True)
            )
            logger.info(f"Permanently deleted folder with id {folder_id}")

    async def share_folder_recursively(
        self, folder_id, email_addresses, role="commenter"
    ):
        if not email_addresses:
            raise ValueError("Email addresses list cannot be empty")

        results = {}
        folder_permissions = await self.get_folder_permissions(
            folder_id, email_addresses
        )
        emails_to_share_folder_with = [
            email for email in email_addresses if email not in folder_permissions
        ]

        async with Aiogoogle(
            service_account_creds=self.service_account_creds
        ) as aiogoogle:
            for email in emails_to_share_folder_with:
                # Create permission data for this user
                permission_data = {
                    "type": "user",  # Use "group" for a Google Group
                    "role": role,
                    "emailAddress": email,
                }

                try:
                    # Create the permission
                    result = await aiogoogle.as_service_account(
                        self.drive_api.permissions.create(
                            fileId=folder_id,
                            json=permission_data,
                            fields="id",
                            supportsAllDrives=True,
                            moveToNewOwnersRoot=False,
                        )
                    )

                    # Store the permission ID
                    permission_id = result.get("id")
                    results[email] = permission_id
                    logger.info(
                        f"Folder {folder_id} shared with {email}, permission ID: {permission_id}"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to share folder {folder_id} with {email}: {str(e)}"
                    )
                    results[email] = None

        return results

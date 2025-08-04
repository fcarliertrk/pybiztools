# PyBizTools

A Python package providing shared business utilities for database connections, email services, logging, Google Drive integration, and Slack messaging.

## Overview

PyBizTools is a collection of reusable business tools designed to simplify common enterprise integrations. Originally extracted from manufacturing operations shared utilities, this package provides clean, async-first interfaces for:

- **Database Operations**: Async SQL Server connections with connection pooling
- **Email Services**: Azure Communication Services email integration
- **Google Drive**: File upload, folder management, and sharing capabilities
- **Slack Integration**: Message posting and API interactions
- **Logging**: Configurable logging with file rotation and environment-based levels

## Features

### DatabaseConnection
- Async SQL Server connectivity using aioodbc
- Connection pooling for performance
- Support for parameterized queries
- Results as tuples or dictionaries
- Context manager support

### EmailService
- Azure Communication Email integration
- Async email sending
- Error handling and logging

### GoogleDrive
- Service account authentication
- Folder creation and management
- File uploads with metadata
- Recursive folder sharing
- Permission management

### SlackService
- Bot token authentication
- Message posting to channels
- Error handling and retry logic
- Async HTTP client management

### Logger
- Environment-based log level configuration
- File rotation with configurable size limits
- Console and file output
- Structured logging format

## Requirements

- Python 3.13+
- Dependencies (automatically installed):
  - `aioodbc>=0.5.0`
  - `azure-communication-email>=1.0.0`
  - `aiogoogle>=5.11.0`
  - `aiohttp>=3.9.0`

## Installation

### From Source

1. Clone or download the project
2. Build the package:
   ```bash
   cd pybiztools
   uv build
   ```

### As a Dependency

Add to your project using uv:

```bash
# From local source
uv add /path/to/pybiztools

# From built wheel
uv add /path/to/pybiztools/dist/pybiztools-0.1.0-py3-none-any.whl

# From PyPI (when published)
uv add pybiztools
```

## Usage

### Basic Import
```python
from pybiztools import (
    DatabaseConnection,
    DatabaseConnectionConfig,
    EmailService,
    GoogleDrive,
    SlackService,
    logger,
    setup_logger
)
```

### Database Example
```python
import asyncio
from pybiztools import DatabaseConnection, DatabaseConnectionConfig

async def main():
    # Create database configuration
    db_config = DatabaseConnectionConfig(
        driver="ODBC Driver 18 for SQL Server",
        server="your_server.database.windows.net",
        database="your_database",
        db_user="your_username",
        db_pass="your_password"
    )
    
    async with DatabaseConnection(db_config) as db:
        # Execute query with results as dictionaries
        results = await db.execute_query(
            "SELECT * FROM users WHERE active = ?", 
            (True,), 
            as_dict=True
        )
        print(results)

asyncio.run(main())
```

### Email Example
```python
import asyncio
from pybiztools import EmailService

async def main():
    email_service = EmailService("your_connection_string")
    
    message = {
        "senderAddress": "sender@example.com",
        "recipients": {
            "to": [{"address": "recipient@example.com"}]
        },
        "content": {
            "subject": "Test Email",
            "plainText": "Hello from PyBizTools!"
        }
    }
    
    async with email_service:
        result = await email_service.send_email(message)
        print(f"Email sent: {result}")

asyncio.run(main())
```

### Google Drive Example
```python
import asyncio
from pybiztools import GoogleDrive

async def main():
    # Requires SERVICE_ACCOUNT_FILE environment variable
    drive = GoogleDrive()
    await drive.initialize()
    
    # Create folder
    folder_id = await drive.create_folder("My Project Folder")
    
    # Upload file
    file_id = await drive.upload_file(
        "/path/to/file.pdf", 
        folder_id, 
        "application/pdf"
    )
    
    # Share with users
    await drive.share_folder_recursively(
        folder_id, 
        ["user1@example.com", "user2@example.com"], 
        role="commenter"
    )

asyncio.run(main())
```

### Slack Example
```python
import asyncio
from pybiztools import SlackService

async def main():
    slack = SlackService("your_bot_token")
    
    message = {
        "channel": "#general",
        "text": "Hello from PyBizTools!",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hello from *PyBizTools*!"
                }
            }
        ]
    }
    
    async with slack:
        result = await slack.send_message(message)
        print(f"Message sent: {result}")

asyncio.run(main())
```

### Logging Example
```python
from pybiztools import logger, setup_logger
import logging

# Use default logger
logger.info("This is an info message")
logger.error("This is an error message")

# Create custom logger
custom_logger = setup_logger("my_app", logging.DEBUG)
custom_logger.debug("Custom debug message")
```

## Configuration

### Environment Variables

The package uses several environment variables for configuration:

#### Database (DatabaseConnection)
The DatabaseConnection class now uses a configuration object instead of environment variables:

```python
from pybiztools import DatabaseConnectionConfig

config = DatabaseConnectionConfig(
    driver="ODBC Driver 18 for SQL Server",  # or your preferred ODBC driver
    server="your_server.database.windows.net",
    database="your_database_name",
    db_user="your_username",
    db_pass="your_password"
)
```

#### Google Drive (GoogleDrive)
- `SERVICE_ACCOUNT_FILE`: Path to Google service account JSON file

#### Slack (SlackService)
- `SLACK_API_BASE_URL`: Slack API base URL (optional, defaults to standard Slack API)

#### Logging (Logger)
- `LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_DIR`: Directory for log files (defaults to "logs")

## Development

### Building the Package

```bash
# Install uv if not already installed
pip install uv

# Build the package
uv build
```

This creates:
- `dist/pybiztools-0.1.0.tar.gz` (source distribution)
- `dist/pybiztools-0.1.0-py3-none-any.whl` (wheel distribution)

### Testing

The package includes comprehensive tests in the `src/pybiztools/tests/` directory:

```bash
# Install test dependencies
uv sync --extra test

# Run tests using uv
uv run pytest src/pybiztools/tests/

# Run tests with verbose output
uv run pytest src/pybiztools/tests/ -v

# Run specific test file
uv run pytest src/pybiztools/tests/test_db.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions, please create an issue in the project repository.

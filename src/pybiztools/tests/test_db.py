import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pybiztools.db import DatabaseConnection, DatabaseConnectionConfig


class TestDatabaseConnection:

    @pytest.fixture
    def db_connection(self):
        config = DatabaseConnectionConfig(
            driver="ODBC Driver 18 for SQL Server",
            server="test_server",
            database="test_database",
            db_user="test_user",
            db_pass="test_pass"
        )
        return DatabaseConnection(config)

    def test_init(self, db_connection):
        assert db_connection.pool is None
        assert "Driver=ODBC Driver 18 for SQL Server" in db_connection.conn_str
        assert "Server=test_server" in db_connection.conn_str
        assert "Database=test_database" in db_connection.conn_str
        assert "UID=test_user" in db_connection.conn_str
        assert "PWD=test_pass" in db_connection.conn_str

    def test_database_connection_config_creation(self):
        config = DatabaseConnectionConfig(
            driver="ODBC Driver 18 for SQL Server",
            server="localhost",
            database="testdb",
            db_user="user",
            db_pass="pass"
        )
        assert config.driver == "ODBC Driver 18 for SQL Server"
        assert config.server == "localhost"
        assert config.database == "testdb"
        assert config.db_user == "user"
        assert config.db_pass == "pass"


    @pytest.mark.asyncio
    @patch("pybiztools.db.aioodbc")
    async def test_connect_creates_pool(self, mock_aioodbc, db_connection):
        mock_pool = AsyncMock()
        mock_aioodbc.create_pool = AsyncMock(return_value=mock_pool)

        result = await db_connection.connect()

        mock_aioodbc.create_pool.assert_called_once_with(
            dsn=db_connection.conn_str, autocommit=True
        )
        assert db_connection.pool == mock_pool
        assert result == mock_pool

    @pytest.mark.asyncio
    @patch("pybiztools.db.aioodbc")
    async def test_connect_reuses_existing_pool(self, mock_aioodbc, db_connection):
        existing_pool = AsyncMock()
        db_connection.pool = existing_pool

        result = await db_connection.connect()

        mock_aioodbc.create_pool.assert_not_called()
        assert result == existing_pool

    @pytest.mark.asyncio
    @patch("pybiztools.db.aioodbc")
    async def test_execute_query_select_as_tuples(self, mock_aioodbc, db_connection):
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()

        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire = MagicMock(return_value=mock_acquire_context)
        mock_cursor_context = AsyncMock()
        mock_cursor_context.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_context.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor = MagicMock(return_value=mock_cursor_context)
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall = AsyncMock(return_value=[(1, "John"), (2, "Jane")])
        mock_cursor.execute = AsyncMock()

        db_connection.pool = mock_pool

        result = await db_connection.execute_query("SELECT * FROM users")

        mock_cursor.execute.assert_called_once_with("SELECT * FROM users")
        mock_cursor.fetchall.assert_called_once()
        assert result == [(1, "John"), (2, "Jane")]

    @pytest.mark.asyncio
    @patch("pybiztools.db.aioodbc")
    async def test_execute_query_select_as_dict(self, mock_aioodbc, db_connection):
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()

        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire = MagicMock(return_value=mock_acquire_context)
        mock_cursor_context = AsyncMock()
        mock_cursor_context.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_context.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor = MagicMock(return_value=mock_cursor_context)
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall = AsyncMock(return_value=[(1, "John"), (2, "Jane")])
        mock_cursor.execute = AsyncMock()

        db_connection.pool = mock_pool

        result = await db_connection.execute_query("SELECT * FROM users", as_dict=True)

        expected = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        assert result == expected

    @pytest.mark.asyncio
    @patch("pybiztools.db.aioodbc")
    async def test_execute_query_with_params(self, mock_aioodbc, db_connection):
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()

        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire = MagicMock(return_value=mock_acquire_context)
        mock_cursor_context = AsyncMock()
        mock_cursor_context.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_context.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor = MagicMock(return_value=mock_cursor_context)
        mock_cursor.description = None
        mock_cursor.rowcount = 1
        mock_cursor.execute = AsyncMock()

        db_connection.pool = mock_pool

        result = await db_connection.execute_query(
            "UPDATE users SET name = ? WHERE id = ?", ("Updated Name", 1)
        )

        mock_cursor.execute.assert_called_once_with(
            "UPDATE users SET name = ? WHERE id = ?", ("Updated Name", 1)
        )
        assert result == 1

    @pytest.mark.asyncio
    @patch("pybiztools.db.aioodbc")
    async def test_execute_query_non_select_returns_rowcount(
        self, mock_aioodbc, db_connection
    ):
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()

        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire = MagicMock(return_value=mock_acquire_context)
        mock_cursor_context = AsyncMock()
        mock_cursor_context.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_context.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor = MagicMock(return_value=mock_cursor_context)
        mock_cursor.description = None
        mock_cursor.rowcount = 3
        mock_cursor.execute = AsyncMock()

        db_connection.pool = mock_pool

        result = await db_connection.execute_query("DELETE FROM users WHERE active = 0")

        assert result == 3

    @pytest.mark.asyncio
    @patch("pybiztools.logger.logger")
    async def test_execute_query_handles_exception(self, mock_logger, db_connection):
        db_connection.pool = None

        with pytest.raises(Exception):
            await db_connection.execute_query("SELECT * FROM users")

        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_close_with_pool(self, db_connection):
        mock_pool = AsyncMock()
        mock_pool.close = MagicMock()
        mock_pool.wait_closed = AsyncMock()
        db_connection.pool = mock_pool

        await db_connection.close()

        mock_pool.close.assert_called_once()
        mock_pool.wait_closed.assert_called_once()
        assert db_connection.pool is None

    @pytest.mark.asyncio
    async def test_close_without_pool(self, db_connection):
        db_connection.pool = None

        await db_connection.close()

        assert db_connection.pool is None

    @pytest.mark.asyncio
    @patch("pybiztools.db.aioodbc")
    async def test_context_manager(self, mock_aioodbc, db_connection):
        mock_pool = AsyncMock()
        mock_pool.close = MagicMock()
        mock_pool.wait_closed = AsyncMock()
        mock_aioodbc.create_pool = AsyncMock(return_value=mock_pool)

        async with db_connection as db:
            assert db == db_connection
            assert db_connection.pool == mock_pool

        mock_pool.close.assert_called_once()
        mock_pool.wait_closed.assert_called_once()
        assert db_connection.pool is None

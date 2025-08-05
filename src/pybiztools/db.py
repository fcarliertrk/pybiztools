from dataclasses import dataclass
from typing import Optional, List, Tuple, Any, Union, Dict

import aioodbc


@dataclass
class DatabaseConnectionConfig:
    driver: str
    server: str
    database: str
    db_user: str
    db_pass: str


class DatabaseConnection:
    def __init__(self, config: DatabaseConnectionConfig) -> None:
        self.pool: Optional[aioodbc.Pool] = None
        self.conn_str: str = (
            f"Driver={config.driver};"
            f"Server={config.server};"
            f"Database={config.database};"
            f"UID={config.db_user};"
            f"PWD={config.db_pass};"
            "TrustServerCertificate=yes;"
        )

    async def connect(self) -> aioodbc.Pool:
        """Initialize the connection pool"""
        if self.pool is None:
            self.pool = await aioodbc.create_pool(dsn=self.conn_str, autocommit=True)
        return self.pool

    async def execute_query(
        self,
        query: str,
        params: Optional[Union[str, Tuple[Any, ...]]] = None,
        as_dict: bool = False,
    ) -> Union[List[Tuple[Any, ...]], List[Dict[str, Any]], int]:
        """
        Execute a query and return results or affected row count

        Args:
            query: The SQL query to execute
            params: Query parameters (optional)
            as_dict: If True, returns results as dictionaries instead of tuples

        Returns:
            For SELECT: List of tuples or dictionaries depending on as_dict parameter
            For UPDATE/INSERT/DELETE: Number of affected rows
        """
        try:
            pool = await self.connect()
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    if params:
                        await cur.execute(query, params)
                    else:
                        await cur.execute(query)

                    # Check if this is a SELECT statement that would return results
                    if cur.description is not None:
                        if as_dict:
                            # Get column names from cursor description
                            columns = [column[0] for column in cur.description]

                            # Fetch all results as tuples
                            rows = await cur.fetchall()

                            # Convert each row tuple to a dictionary using column names as keys
                            return [dict(zip(columns, row)) for row in rows]
                        else:
                            return await cur.fetchall()
                    else:
                        # For non-query statements (UPDATE, INSERT, DELETE), return row count
                        return cur.rowcount
        except Exception as err:
            from .logger import logger

            logger.error(f"Error while executing query: {err}")
            raise

    async def close(self) -> None:
        """Close the connection pool - call this at application shutdown"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def __aenter__(self) -> "DatabaseConnection":
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        await self.close()

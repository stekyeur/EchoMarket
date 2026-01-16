from database.connection import get_db_connection, close_db_connection


class BaseRepository:
    """Base repository with common database operations."""

    def _execute_query(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
        """Execute a SELECT query and return results."""
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(query, params)

            if fetch_one:
                return cur.fetchone()
            if fetch_all:
                return cur.fetchall()
            return None
        finally:
            close_db_connection(conn)

    def _execute_write(self, query: str, params: tuple = None, returning: bool = False):
        """Execute an INSERT/UPDATE/DELETE query."""
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(query, params)

            result = None
            if returning:
                result = cur.fetchone()

            conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            close_db_connection(conn)

    def _execute_many(self, queries: list):
        """Execute multiple queries in a single transaction."""
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            results = []
            for query, params, returning in queries:
                cur.execute(query, params)
                if returning:
                    results.append(cur.fetchone())

            conn.commit()
            return results
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            close_db_connection(conn)

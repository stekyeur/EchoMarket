import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from config.settings import get_config

config = get_config()


class DatabasePool:
    """Singleton database connection pool manager."""

    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_pool()
        return cls._instance

    @classmethod
    def _initialize_pool(cls):
        """Initialize the connection pool."""
        try:
            cls._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=config.DB_POOL_MIN,
                maxconn=config.DB_POOL_MAX,
                **config.DB_CONFIG,
                sslmode='require'
            )
            print("Veritabani Baglanti Havuzu Basariyla Olusturuldu.")
        except Exception as e:
            print(f"Havuz Olusturma Hatasi: {e}")
            cls._pool = None

    @classmethod
    def get_connection(cls):
        """Get a connection from the pool."""
        if cls._pool is None:
            cls._initialize_pool()
        return cls._pool.getconn() if cls._pool else None

    @classmethod
    def put_connection(cls, conn):
        """Return a connection to the pool."""
        if cls._pool and conn:
            cls._pool.putconn(conn)

    @classmethod
    def close_all(cls):
        """Close all connections in the pool."""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None


# Initialize pool singleton
_db_pool = DatabasePool()


def get_db_connection():
    """Get a database connection from the pool."""
    return DatabasePool.get_connection()


def close_db_connection(conn):
    """Return a connection to the pool."""
    DatabasePool.put_connection(conn)


@contextmanager
def db_connection():
    """Context manager for database connections.

    Usage:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute(...)
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        close_db_connection(conn)


@contextmanager
def db_transaction():
    """Context manager for database transactions with auto-commit/rollback.

    Usage:
        with db_transaction() as (conn, cur):
            cur.execute(...)
            # Auto-commits on success, rollbacks on exception
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        yield conn, cur
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        close_db_connection(conn)

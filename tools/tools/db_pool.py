from psycopg2 import pool


class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@db:5432/db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DatabasePool:
    _pool = None

    @classmethod
    def init_pool(cls):
        if cls._pool is None:
            cls._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=Config.SQLALCHEMY_DATABASE_URI
            )

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            raise Exception("Database pool is not initialized")
        return cls._pool.getconn()

    @classmethod
    def release_connection(cls, conn):
        if cls._pool is not None:
            cls._pool.putconn(conn)

    @classmethod
    def close_pool(cls):
        if cls._pool is not None:
            cls._pool.closeall()

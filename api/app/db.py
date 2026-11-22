"""Acceso a PostgreSQL/PostGIS mediante un pool de conexiones."""
import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool = None


def _dsn():
    return "postgresql://{u}:{p}@{h}:{port}/{db}".format(
        u=os.environ.get("POSTGRES_USER", "vigia"),
        p=os.environ.get("POSTGRES_PASSWORD", "cambiar_en_local"),
        h=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        db=os.environ.get("POSTGRES_DB", "vigiaslp"),
    )


def pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(_dsn(), min_size=1, max_size=5, kwargs={"row_factory": dict_row}, open=True)
    return _pool


def conexion():
    return pool().connection()

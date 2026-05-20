import psycopg2
from contextlib import contextmanager


@contextmanager
def postgres_connection(host, port, user, password, dbname):
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def pg_data_warehouse_conn():
    return postgres_connection(
        host="d2026.unipartrail.local",
        port=5433,
        user="admin",
        password="MileyHalifax16!",
        dbname="data_warehouse",
    )


@contextmanager
def postgres_cursor(conn):
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

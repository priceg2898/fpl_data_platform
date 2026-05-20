from collections.abc import Iterator
from contextlib import contextmanager

import pyodbc


@contextmanager
def mssql_connection(
    server: str,
    database: str,
    username: str,
    password: str,
    driver: str = "ODBC Driver 18 for SQL Server",
) -> Iterator[pyodbc.Connection]:
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )

    conn = pyodbc.connect(conn_str)

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def j211_conn():
    return mssql_connection(
        server="J211.unipartrail.local",
        database="T1_Control",
        username="QlikSense_Admin",
        password="J2dGwTZeyNbU8DKE",
    )

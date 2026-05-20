from shared.connectors.db.factory import create_db_engine
from shared.config.settings import Settings
from sqlalchemy import text
from random import randint


def main():
    settings = Settings()

    sql = text("""
    INSERT INTO test (col_a, col_b)
    VALUES (:col_a, :col_b)
    """)

    params = {
        "col_a": randint(0, 1000),
        "col_b": randint(0, 1000),
    }

    engine = create_db_engine(settings)
    with engine.begin() as conn:
        conn.execute(sql, params)


if __name__ == "__main__":
    main()

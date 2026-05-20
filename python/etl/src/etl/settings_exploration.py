from shared.connectors.db.factory import create_db_engine
from shared.config.settings import Settings
from sqlalchemy import text


def main():
    settings = Settings()

    engine = create_db_engine(settings)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM test"))
        print(result.fetchall())


if __name__ == "__main__":
    main()

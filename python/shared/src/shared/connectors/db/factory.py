from sqlalchemy import create_engine
from shared.config.settings import Settings


def create_postgres_engine(db):
    url = (
        f"postgresql+psycopg2://"
        f"{db.username}:{db.password.get_secret_value()}"
        f"@{db.host}:{db.port}/{db.database}"
    )

    return create_engine(url, pool_pre_ping=True)


def create_mssql_engine(db):
    url = (
        f"mssql+pyodbc://"
        f"{db.username}:{db.password.get_secret_value()}"
        f"@{db.host}:{db.port}/{db.database}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
    )

    return create_engine(url, pool_pre_ping=True)


def create_db_engine(settings: Settings):
    db = settings.db

    if db.backend == "postgres":
        return create_postgres_engine(db)

    if db.backend == "mssql":
        return create_mssql_engine(db)

    raise ValueError(f"Unsupported backend: {db.backend}")

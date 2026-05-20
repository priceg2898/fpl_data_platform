import os
from dotenv import load_dotenv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]  # adjust if needed
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def j211_conn():
    user = os.environ["J211_USER"]
    pw = os.environ["J211_USER_PW"]
    j211_conn = f"mssql+pyodbc://{user}:{pw}@10.158.182.211:1433/T3_ProcessRunner?driver=ODBC%20Driver%2018%20for%20SQL%20Server&Encrypt=no&TrustServerCertificate=yes&ConnectionTimeout=5"

    return j211_conn

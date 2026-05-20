import time
from sqlalchemy import create_engine, text
from python.process_runner_db.Connectors.mssql import j211_conn
from .sql_code import sql_code
from python.process_runner_db.Utils.logging import logging, update_log_level
from python.process_runner_db.Connectors.process_runner import process_files_from_db


def main():
    j211_engine = create_engine(j211_conn(), pool_pre_ping=True)
    sleep_seconds = 5

    logging.info("Starting service...")
    logging.info(f"Initial Log level: {(logging.getLogger()).level}")
    import os
    import getpass

    logging.info(f"User: {getpass.getuser()}")
    logging.info(f"Session Name: {os.environ.get('SESSIONNAME')}")

    while True:
        logger = logging.getLogger()
        update_log_level(logger)

        try:
            with j211_engine.begin() as conn:
                sql = sql_code(3)
                if sql:
                    conn.execute(text(sql))

            with j211_engine.begin() as conn:
                sql = sql_code(1)
                if sql:
                    result = conn.execute(text(sql))
                    rows = result.mappings().all()
                    logging.debug("Executed sql code 1")

            if rows:
                for row in rows:
                    try:
                        processed = process_files_from_db(row)
                        if processed:
                            with j211_engine.begin() as conn:
                                sql = sql_code(2)
                                if sql:
                                    conn.execute(text(f"{sql}"), {"id": row["id"]})
                                    logging.debug("Executed sql code 2")
                        else:
                            pass
                    except Exception:
                        logging.exception(f"Error processing row {row['id']}")

                time.sleep(sleep_seconds)

            else:
                logging.debug(f"No rows to process... Waiting {sleep_seconds}s")
                time.sleep(sleep_seconds)

        except Exception:
            logging.exception("Unhandled error in main loop")
            time.sleep(60)


if __name__ == "__main__":
    main()

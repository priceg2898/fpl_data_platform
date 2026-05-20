import os
from dotenv import load_dotenv
from python.process_runner_db.Utils.logging import logging


load_dotenv()


def sql_code(code_id: int) -> dict:
    environment = os.environ.get("PROD_DEV_FLAG", "").strip().upper()
    sql_code_dict, return_list = {}, ""

    if environment not in ["DEV", "PROD"]:
        logging.error("PROD_DEV_FLAG environment variable must be one of PROD / DEV")
    else:
        if environment == "DEV":
            sql_code_dict = {
                1: "SELECT * FROM T3_ProcessRunner.dbo.process_runner_master__DEV WHERE enabled = 1 AND rows_pending = 1",
                2: "UPDATE T3_ProcessRunner.dbo.process_runner_master__DEV SET rows_pending = NULL WHERE id = :id",
                3: "SELECT 1",
            }

        elif environment == "PROD":
            sql_code_dict = {
                1: "SELECT * FROM T3_ProcessRunner.dbo.process_runner_master WHERE enabled = 1 AND rows_pending = 1",
                2: "UPDATE T3_ProcessRunner.dbo.process_runner_master SET rows_pending = NULL WHERE id = :id",
                3: "UPDATE T3_ProcessRunner.dbo.process_runner__verify_is_up SET UpdatedAt = GETDATE()",
            }
        try:
            return_list = sql_code_dict[code_id]
        except KeyError:
            logging.error(
                f"sql code id {code_id} is not defined for sql_code_dict "
                f"for environment {environment}"
            )

    return return_list

import os
from datetime import datetime
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from croniter import croniter
import shlex
from python.process_runner_db.Utils.logging import logging


path_to_process_runner_exe = r"C:\Program Files\Innowera\Process Runner DB\ProRDB.exe"


def process_files_from_db(row) -> bool:
    """
    Iterates over rows from SQL with 'file_path' and 'schedule' fields
    and runs files that are due based on cron schedules.
    """
    now = datetime.now()
    file_path = row["file_path"]
    schedule = row.get("schedule", None)
    schedule_tolerance_secs = row.get("schedule_tolerance_secs", None)
    processing = False
    if should_run(schedule, now, tolerance_seconds=schedule_tolerance_secs):
        processing = True
        start_time = datetime.now()
        logging.info(
            f"Running row {row['id']}, file_path: {file_path}, schedule: {schedule}, args: {row.get('args', '')}"
        )
        run_process_runner(
            path_to_executable=r"C:\Program Files\Innowera\Process Runner DB\ProRDB.exe",
            file_path=file_path,
            args=row.get("args", ""),
        )
        end_time = datetime.now()
        logging.info(
            f"Row {row['id']} ran in {(end_time - start_time).total_seconds()}s"
        )
    else:
        logging.debug(f"Skipping row {row['id']}")
    return processing


def run_process_runner(path_to_executable: str, file_path: str, args: str = None):
    BASE_DIR = Path(__file__).resolve().parents[2]  # adjust if needed
    ENV_PATH = BASE_DIR / ".env"

    load_dotenv(dotenv_path=ENV_PATH)
    args = args or ""
    parsed_args = shlex.split(args, posix=False)
    environment = os.environ.get("PROD_DEV_FLAG", "").strip().upper()
    cmd = [path_to_executable, file_path] + parsed_args
    result = None

    if environment == "DEV":
        dev_cmd = ["cmd", "/c", "echo", "Dry run executable call:"] + cmd
        result = subprocess.run(dev_cmd, capture_output=True, text=True, check=True)
        logging.debug(f"stdout: {result.stdout}")

    elif environment == "PROD":
        if not os.path.exists(path_to_executable):
            logging.error(f"Executable not found: {path_to_executable}")
        if not os.path.exists(file_path):
            logging.error(f"Input file not found: {file_path}")

        printable_cmd = shlex.join(cmd)
        logging.info(f"Executing Command: {printable_cmd}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=os.path.dirname(file_path),
                timeout=300,
            )

            logging.info("Process completed successfully.")
            if result.stdout:
                logging.info(f"stdout: {result.stdout}")

        except subprocess.TimeoutExpired as e:
            logging.error("Process timed out after 5 minutes.")
            logging.error(f"Partial stdout: {e.stdout}")
            logging.error(f"Partial stderr: {e.stderr}")
            raise

        except subprocess.CalledProcessError as e:
            logging.error(f"Innowera failed with Exit Code: {e.returncode}")
            logging.error(f"Error Details (stderr): {e.stderr}")
            logging.error(f"Standard Output: {e.stdout}")
            raise

    else:
        if environment:
            logging.error(
                f"PROD_DEV_FLAG='{environment}' invalid. Valid values: DEV or PROD"
            )
        else:
            logging.error(
                "PROD_DEV_FLAG Environment Variable not set. Valid values: DEV or PROD"
            )

    return result


def should_run(
    schedule: str, now: datetime = None, tolerance_seconds: int = 60
) -> bool:
    if not schedule:
        return True  # blank schedule → always run

    now = now or datetime.now()
    cron_iter = croniter(schedule, now)
    prev_time = cron_iter.get_prev(datetime)
    return (now - prev_time).total_seconds() <= tolerance_seconds

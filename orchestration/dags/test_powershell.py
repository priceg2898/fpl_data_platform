from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime
import os

default_args = {
    "owner": "airflow",
    "start_date": datetime(2026, 4, 7),
}


def print_container_info():
    print("Hostname:", os.uname().nodename)


with DAG(
    "run_windows_commands",
    default_args=default_args,
    schedule="*/15 * * * *",
    catchup=False,
) as dag:
    print_info_task = PythonOperator(
        task_id="print_container_info",
        python_callable=print_container_info,
    )

    run_powershell = SSHOperator(
        task_id="run_powershell_script",
        ssh_conn_id="ssh_d2026_to_j217",
        command='powershell -Command "Get-Process"',
    )

    print_info_task >> run_powershell

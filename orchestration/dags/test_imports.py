from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator


def test_imports():
    print("Airflow DAG is running!")
    import math

    print("math.sqrt(16) =", math.sqrt(16))
    try:
        print("requests imported successfully!")
    except ImportError:
        print("requests is NOT installed!")


dag = DAG(
    dag_id="test_imports_dag",
    start_date=datetime(2026, 4, 2),
    schedule="*/15 * * * *",
    catchup=False,
    tags=["example"],
)

check_imports = PythonOperator(
    task_id="check_imports_task", python_callable=test_imports, dag=dag
)

check_imports

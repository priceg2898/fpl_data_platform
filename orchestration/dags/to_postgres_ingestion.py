import json
from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.standard.operators.python import BranchPythonOperator
# from airflow.datasets import Dataset


# ----------------------------
# Dataset (shared contract)
# ----------------------------
from datasets import materials_dataset__j211

# ----------------------------
# Config
# ----------------------------
daily_extracts = [
    "j211__MM_SAP_DS_MARA",
    "j211__MM_SAP_DS_MVKE",
]


# ----------------------------
# DAG
# ----------------------------
with DAG(
    dag_id="j211_materials_ingestion",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["ingestion", "materials"],
) as dag:
    # ----------------------------
    # 1. Run ETL per table
    # ----------------------------
    run_etl_tasks = []

    for table_id in daily_extracts:
        config = {
            "id": table_id,
            "triggered_by": "airflow",
        }

        run_etl = DockerOperator(
            task_id=f"run_{table_id}",
            image="data-platform-ephemeral__etl:latest",
            command=(
                "poetry run python -m etl.to_postgres.main "
                f"--config '{json.dumps(config)}'"
            ),
            docker_url="unix://var/run/docker.sock",
            network_mode="bridge",
            do_xcom_push=True,  # assumes your container prints JSON only
        )

        run_etl_tasks.append(run_etl)

    # ----------------------------
    # 2. Aggregate results
    # ----------------------------
    @task
    def aggregate_results(*results):
        """
        results = list of XCom outputs from DockerOperator tasks
        """
        parsed = []

        for r in results:
            import ast
            import json

            if isinstance(r, str):
                try:
                    r = json.loads(r)
                except json.JSONDecodeError:
                    r = ast.literal_eval(r)

            parsed.append(r)

        return any(item.get("has_updates") for item in parsed)

    # ----------------------------
    # 3. Decide branch
    # ----------------------------
    def decide(has_updates: bool):
        return "emit_dataset" if has_updates else "skip_dataset"

    # ----------------------------
    # 4. Dataset emit (ONLY ONE PLACE)
    # ----------------------------
    emit_dataset = EmptyOperator(
        task_id="emit_dataset",
        outlets=[materials_dataset__j211],
    )

    skip_dataset = EmptyOperator(
        task_id="skip_dataset",
    )

    # ----------------------------
    # 5. Wire everything
    # ----------------------------
    results = [t.output for t in run_etl_tasks]

    has_updates = aggregate_results(*results)

    decide_task = BranchPythonOperator(
        task_id="decide",
        python_callable=decide,
        op_args=[has_updates],
    )

    run_etl_tasks >> has_updates >> decide_task >> [emit_dataset, skip_dataset]


# ----------------------------
# DBT DAG (event-driven)
# ----------------------------
with DAG(
    dag_id="dbt_transform_gold",
    start_date=datetime(2024, 1, 1),
    schedule=[materials_dataset__j211],
    catchup=False,
    tags=["dbt", "transform"],
) as dbt_dag:
    run_pwd = DockerOperator(
        task_id="pwd",
        image="data-platform-ephemeral__etl:latest",
        command="pwd",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
    )

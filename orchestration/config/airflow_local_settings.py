import logging

logging.getLogger("airflow.models.dagbag.BundleDagBag").setLevel(logging.WARNING)
logging.getLogger("airflow.models.dagbag.BundleDagBag").propagate = False

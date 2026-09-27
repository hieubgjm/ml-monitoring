"""Orchestrate Evidently drift analysis and notify Alertmanager on task failure."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from airflow import DAG
from airflow.exceptions import AirflowException, AirflowSkipException
from airflow.operators.python import PythonOperator


logger = logging.getLogger(__name__)

EVIDENTLY_URL = os.getenv("EVIDENTLY_URL", "http://evidently:8001")
ALERTMANAGER_URL = os.getenv(
    "ALERTMANAGER_URL", "http://alertmanager:9093/api/v2/alerts"
)
HTTP_TIMEOUT_SECONDS = 15
MINIMUM_PRODUCTION_SAMPLES = 100


# ============================================
# ALERTING
# ============================================

def notify_alertmanager(context: dict[str, Any]) -> None:
    """Post a task failure to Alertmanager without masking the original failure."""
    task_instance = context["task_instance"]
    dag_id = task_instance.dag_id
    task_id = task_instance.task_id
    run_id = context["run_id"]

    alert = {
        "labels": {
            "alertname": "AirflowTaskFailed",
            "severity": "critical",
            "component": "airflow",
            "dag_id": dag_id,
            "task_id": task_id,
            "run_id": run_id,
        },
        "annotations": {
            "summary": f"Airflow task failed: {dag_id}.{task_id}",
            "description": (
                f"DAG run {run_id} failed after retry attempts were exhausted. "
                "Open the Airflow task logs to investigate."
            ),
            "airflow_log_url": task_instance.log_url,
        },
        "startsAt": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = requests.post(ALERTMANAGER_URL, json=[alert], timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        logger.info("Sent Airflow failure alert for %s.%s", dag_id, task_id)
    except requests.RequestException:
        # A notification failure must never replace the original task error.
        logger.exception("Could not send Airflow failure alert to Alertmanager")


# ============================================
# DAG TASKS
# ============================================

def verify_evidently_ready(**context: Any) -> None:
    """Require reference and production data before spending work on analysis."""
    dag_run = context.get("dag_run")
    if dag_run and dag_run.conf.get("force_failure", False):
        raise AirflowException("Intentional failure requested to test Alertmanager")

    response = requests.get(f"{EVIDENTLY_URL}/health", timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    health = response.json()

    if not health.get("reference_data_loaded", False):
        raise AirflowSkipException("Reference data is not loaded in Evidently yet")

    production_data_count = health.get("production_data_count", 0)
    if production_data_count < MINIMUM_PRODUCTION_SAMPLES:
        raise AirflowSkipException(
            f"Only {production_data_count} production samples are available; "
            f"waiting for {MINIMUM_PRODUCTION_SAMPLES}"
        )


def trigger_drift_analysis() -> None:
    """Run Evidently analysis after its data prerequisites have been met."""
    response = requests.post(
        f"{EVIDENTLY_URL}/analyze",
        json={"window_size": MINIMUM_PRODUCTION_SAMPLES, "threshold": 0.1},
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    logger.info("Evidently drift analysis completed: %s", response.json())


# ============================================
# DAG DEFINITION
# ============================================

default_args = {
    "owner": "ml-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "on_failure_callback": notify_alertmanager,
}

with DAG(
    dag_id="model_drift_monitoring",
    description="Validate Evidently readiness and run scheduled drift analysis.",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["ml-monitoring", "evidently", "alerting"],
) as model_drift_monitoring:
    verify_readiness = PythonOperator(
        task_id="verify_evidently_ready",
        python_callable=verify_evidently_ready,
    )

    analyze_drift = PythonOperator(
        task_id="trigger_drift_analysis",
        python_callable=trigger_drift_analysis,
    )

    verify_readiness >> analyze_drift

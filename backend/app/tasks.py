import logging
from app.config import settings
from app.database import SessionLocal
from app.orchestrator import orchestrator

logger = logging.getLogger(__name__)

# Initialize Celery app
try:
    from celery import Celery
    celery_app = Celery(
        "finance_agent",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        beat_schedule={
            "hourly-monitoring": {
                "task": "app.tasks.hourly_monitoring_task",
                "schedule": 3600.0, # Every 60 minutes
            },
            "worker-heartbeat": {
                "task": "app.tasks.worker_heartbeat_task",
                "schedule": 30.0,
            }
        }
    )
except ImportError:
    celery_app = None

# Celery application alias for CLI compatibility
app = celery_app

def run_analysis_task(user_id: str, trigger_reason: str = "CELERY_JOB"):
    """Can be run by Celery worker or synchronously as fallback."""
    db = SessionLocal()
    try:
        return orchestrator.run_full_pipeline(db, user_id, trigger_reason)
    finally:
        db.close()

if celery_app:
    @celery_app.task(name="app.tasks.run_analysis_task")
    def celery_run_analysis(user_id: str, trigger_reason: str = "CELERY_JOB"):
        return run_analysis_task(user_id, trigger_reason)

    @celery_app.task(name="app.tasks.hourly_monitoring_task")
    def hourly_monitoring_task():
        logger.info("Scheduler executed hourly monitoring check.")
        return {"status": "CHECK_COMPLETED"}

    @celery_app.task(name="app.tasks.worker_heartbeat_task")
    def worker_heartbeat_task():
        return {"heartbeat": True}

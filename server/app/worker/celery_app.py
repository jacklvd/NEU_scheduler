from celery import Celery
import os
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "neu_scheduler_worker",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="US/Eastern",
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
    task_routes={
        "app.worker.tasks.cache_courses": {"queue": "cache"},
        "app.worker.tasks.generate_ai_suggestion": {"queue": "ai"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

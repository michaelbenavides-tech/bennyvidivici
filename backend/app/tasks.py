from celery import Celery

from app.config import get_settings

settings = get_settings()
celery_app = Celery("ai_sgp", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="app.tasks.ping")
def ping() -> str:
    return "pong"

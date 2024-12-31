from celery import Celery

from adumbra.config import Config
from adumbra.database import connect_mongo

connect_mongo("Celery_Worker")

celery = Celery(
    Config.NAME, backend=Config.CELERY_RESULT_BACKEND, broker=Config.CELERY_BROKER_URL
)
celery.autodiscover_tasks(["adumbra.workers.tasks"])


if __name__ == "__main__":
    celery.start()

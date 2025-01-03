from celery import Celery

from adumbra.config import CONFIG
from adumbra.database import connect_mongo

connect_mongo("Celery_Worker")

celery = Celery(
    CONFIG.name, backend=CONFIG.celery.result_backend, broker=CONFIG.celery.broker_url
)
celery.autodiscover_tasks(["adumbra.workers.tasks"])


if __name__ == "__main__":
    celery.start()

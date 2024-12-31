from flask_socketio import SocketIO

from adumbra.config import Config


def create_socket():
    return SocketIO(message_queue=Config.CELERY_BROKER_URL)

from flask_socketio import SocketIO

from adumbra.config import CONFIG


def create_socket():
    return SocketIO(message_queue=CONFIG.celery.broker_url)

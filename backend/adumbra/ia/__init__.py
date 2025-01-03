import logging

import eventlet
import requests
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from adumbra.config import CONFIG
from adumbra.database import create_from_json
from adumbra.ia.api import blueprint as api

eventlet.monkey_patch(thread=False)


def create_app():

    # Dunno why observer.start() does not return
    # We disable it and see later if this is fixable
    # if Config.FILE_WATCHER:
    #   run_watcher()

    flask = Flask(__name__, static_url_path="", static_folder="../dist")

    flask.config.from_object(CONFIG)

    CORS(flask)

    flask.wsgi_app = ProxyFix(flask.wsgi_app)
    flask.register_blueprint(api)

    return flask


app = create_app()

logger = logging.getLogger("gunicorn.error")
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)


if CONFIG.initialize_from_file:
    create_from_json(CONFIG.initialize_from_file)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def index(path):

    if app.debug:
        return requests.get(f"http://frontend:8080/{path}", timeout=5).text

    return app.send_static_file("index.html")

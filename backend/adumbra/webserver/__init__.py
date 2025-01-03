import eventlet

eventlet.monkey_patch(thread=False)

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# monkey patching must be done before importing the remaining modules
# https://eventlet.readthedocs.io/en/latest/patching.html#monkeypatching-the-standard-library

import logging
import os

import requests
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from adumbra.config import CONFIG
from adumbra.database import ImageModel, connect_mongo, create_from_json
from adumbra.webserver.api import blueprint as api
from adumbra.webserver.authentication import login_manager
from adumbra.webserver.sockets import socketio
from adumbra.webserver.util import thumbnails

connect_mongo("webserver")

socketio = SocketIO()


def create_app():

    # Dunno why observer.start() does not return
    # We disable it and see later if this is fixable
    # if Config.FILE_WATCHER:
    #   run_watcher()

    flask = Flask(
        __name__,
        # static_url_path='', # this option seem's to cause trouble with path handling
        static_folder="../dist",
    )

    flask.config.from_object(CONFIG.flask)

    CORS(flask)

    flask.wsgi_app = ProxyFix(flask.wsgi_app)
    flask.register_blueprint(api)

    login_manager.init_app(flask)

    # socketio = SocketIO(flask, async_mode='eventlet',
    socketio.init_app(
        flask,
        async_mode="eventlet",
        cors_allowed_origins="*",
        message_queue=CONFIG.celery.broker_url,
    )
    # Remove all poeple who were annotating when
    # the server shutdown
    ImageModel.objects.update(annotating=[])
    thumbnails.generate_thumbnails()

    return flask


app = create_app()

logger = logging.getLogger("gunicorn.error")
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)


if CONFIG.initialize_from_file:
    create_from_json(CONFIG.initialize_from_file)


@app.route("/assets/<path:filepath>")
def data(filepath):
    return send_file(os.path.join("../dist/assets", filepath))


@app.route("/<path:path>")
@app.route("/<string:path>")
@app.route("/", defaults={"path": ""})
def index(path):
    if app.debug:
        return requests.get(f"http://frontend:8080/{path}", timeout=30).text

    return app.send_static_file("index.html")


# proxy to call AI services
@app.route("/api/model/<path:path>", methods=["GET", "POST", "PUT"])
def proxy_request(path):
    json_data = None
    form_data = None
    image = None

    print("try to proxy", flush=True)
    target_proxy = os.getenv("TARGET_PROXY", "http://annotator_ia:6000")

    # Prepare the URL for the target server using the extracted host, port, and path
    target_url = f"{target_proxy}/api/model/{path}"

    print("proxy target url:", target_url, request.method, flush=True)

    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        # Handle JSON request
        json_data = request.get_json()
    elif content_type.startswith("multipart/form-data"):
        # Handle form data request
        form_data = request.form.get("data")
        image = request.files.get("image")

    # Forward the request to the target server
    if request.method == "GET":
        print("in GET", flush=True)
        response = requests.get(target_url, timeout=30)
    elif request.method == "POST":
        print("will call with:", form_data, flush=True)
        if form_data is not None and image is not None:
            response = requests.post(
                target_url, data={"data": form_data}, files={"image": image}, timeout=30
            )
        elif json_data is not None:
            response = requests.post(target_url, json=json_data, timeout=30)
        print("response:", response, flush=True)
    elif request.method == "PUT":
        print("not handled right now", flush=True)
        response = requests.put(target_url, json=request.get_json(), timeout=30)

    print("proxy reply:", response, flush=True)
    # Return the response from the target server
    return jsonify(response.json()), response.status_code

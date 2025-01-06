import json
import logging
import zipfile
from pathlib import Path

from flask_restx import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage

from adumbra.config import CONFIG
from adumbra.database.assistant import AssistantDBModel
from adumbra.ia.util.segmentation_helpers import run_segmentation

logger = logging.getLogger("gunicorn.error")


def flask_request_to_segmentation_response(parser: reqparse.RequestParser):
    args = parser.parse_args()
    data = json.loads(args["data"])
    logger.info(f"data: {data}")
    image_file = args["image"]
    response = run_segmentation(
        config=CONFIG.ia.sam2,
        image_stream=image_file.stream,
        foreground_xy=data.pop("points"),
        **data,
    )
    code = 200 if not response["disabled"] else 400
    return response, code


api = Namespace("model", description="Model related operations")


@api.route("/")
class Model(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("name", type=str, required=False, help="Name of the model")
    get_parser.add_argument(
        "model_type", type=str, required=False, help="Type of the model"
    )

    post_parser = reqparse.RequestParser()
    post_parser.add_argument("name", type=str, required=True, help="Name of the model")
    post_parser.add_argument(
        "model_type",
        type=str,
        required=True,
        choices=("sam2", "zim"),
        help="Type of the model",
    )
    post_parser.add_argument(
        "parameters", type=dict, required=False, help="Additional parameters"
    )
    post_parser.add_argument(
        "assets",
        location="assets",
        type=FileStorage,
        required=True,
        action="append",
        help=".zip file of all assets referred to in parameters",
    )

    @api.expect(get_parser)
    def get(self):
        args = self.get_parser.parse_args()
        kwargs = {}
        for key in "name", "model_type":
            if val := args.get(key):
                kwargs[key] = val
        matches = AssistantDBModel.objects(**kwargs)
        return json.loads(matches.to_json()), 200

    @api.expect(post_parser)
    def post(self):
        args = self.post_parser.parse_args()
        name = args["name"]
        model_type = args["model_type"]
        parameters = args.get("parameters", {})
        files = args["assets"]
        if not isinstance(files, list):
            files = [files]

        save_path = Path("/models") / model_type / name
        save_path.mkdir(parents=True, exist_ok=True)
        for file in files:
            file: FileStorage
            if zipfile.is_zipfile(file.stream):
                with zipfile.ZipFile(file.stream, "r") as zip_ref:
                    zip_ref.extractall(save_path)
            else:
                file.save(save_path / file.filename)

        new_model = AssistantDBModel(
            name=name, model_type=model_type, parameters=parameters
        )
        new_model.save()

        return {"message": "Model created successfully"}, 201


@api.route("/sam2")
class Sam2Segmentation(Resource):
    sam2_args = reqparse.RequestParser()
    sam2_args.add_argument("data", type=str, required=True)
    sam2_args.add_argument(
        "image", location="files", type=FileStorage, required=True, help="Image"
    )

    @api.expect(sam2_args)
    def post(self):
        return flask_request_to_segmentation_response(self.sam2_args)


@api.route("/zim")
class ZimSegmentation(Resource):
    zim_args = reqparse.RequestParser()
    zim_args.add_argument("data", type=str, required=True)
    zim_args.add_argument(
        "image", location="files", type=FileStorage, required=True, help="Image"
    )

    @api.expect(zim_args)
    def post(self):
        return flask_request_to_segmentation_response(self.zim_args)

import json
import logging
from pathlib import Path

import numpy as np
from flask_restx import Namespace, Resource, reqparse
from PIL import Image
from werkzeug.datastructures import FileStorage

from adumbra.database.assistant import AssistantModel
from adumbra.ia.util.helpers import getSegmentation
from adumbra.ia.util.sam2 import SAM2
from adumbra.ia.util.zim import ZIM

logger = logging.getLogger("gunicorn.error")

api = Namespace("model", description="Model related operations")

image_upload = reqparse.RequestParser()
image_upload.add_argument(
    "image", location="files", type=FileStorage, required=True, help="Image"
)

sam2_args = reqparse.RequestParser()
sam2_args.add_argument("data", type=str, required=True)
sam2_args.add_argument(
    "image", location="files", type=FileStorage, required=True, help="Image"
)

zim_args = reqparse.RequestParser()
zim_args.add_argument("data", type=str, required=True)
zim_args.add_argument(
    "image", location="files", type=FileStorage, required=True, help="Image"
)

sam2 = SAM2()
zim = ZIM()


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
        help=".zip file of all assets referred to in parameters",
    )

    @api.expect(get_parser)
    def get(self):
        args = self.get_parser.parse_args()
        kwargs = {}
        for key in "name", "model_type":
            if val := args.get(key):
                kwargs[key] = val
        matches = AssistantModel.objects(**kwargs)
        return json.loads(matches.to_json()), 200

    @api.expect(post_parser)
    def post(self):
        args = self.post_parser.parse_args()
        name = args["name"]
        model_type = args["model_type"]
        parameters = args.get("parameters", {})
        files = args["files"]

        save_path = Path("/models") / model_type / name
        save_path.mkdir(parents=True, exist_ok=True)
        for file in files:
            file: FileStorage
            file.save(save_path / file.filename)

        new_model = AssistantModel(
            name=name, model_type=model_type, parameters=parameters
        )
        new_model.save()

        return {"message": "Model created successfully"}, 201


@api.route("/sam2")
class Sam2Segmentation(Resource):

    @api.expect(image_upload)
    def post(self):
        """COCO data test"""
        if sam2.is_loaded is False:
            return {"disabled": True, "message": "SAM2 is disabled"}, 400

        args = sam2_args.parse_args()
        data = json.loads(args["data"])
        logger.info(f"data: {data}")

        sam2.setPredictor(
            float(data["threshold"]), float(data["maxhole"]), float(data["maxsprinkle"])
        )
        points = data["points"][0]

        img_file = args["image"]
        im = Image.open(img_file.stream).convert("RGB")
        im = np.asarray(im)

        sam2.setImage(im)
        sam2.calcMasks(np.array([points]), np.array([1]))
        segmentation = getSegmentation("sam2", sam2.masks)
        return {"segmentation": segmentation}


@api.route("/zim")
class ZimSegmentation(Resource):

    @api.expect(image_upload)
    def post(self):
        """COCO data test"""
        if zim.is_loaded is False:
            return {"disabled": True, "message": "ZIM is disabled"}, 400

        args = zim_args.parse_args()
        data = json.loads(args["data"])
        points = data["points"][0]

        img_file = args["image"]
        im = Image.open(img_file.stream).convert("RGB")
        im = np.asarray(im)

        zim.setImage(im)
        zim.calcMasks(np.array([points]), np.array([1]))
        segmentation = getSegmentation("zim", zim.masks)
        return {"segmentation": segmentation}

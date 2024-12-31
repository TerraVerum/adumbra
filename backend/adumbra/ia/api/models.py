import json
import logging
import os

import numpy as np
from flask_restx import Namespace, Resource, reqparse
from PIL import Image
from werkzeug.datastructures import FileStorage

from adumbra.config import Config

logger = logging.getLogger("gunicorn.error")

SAM2_LOADED = os.path.isfile(Config.SAM2_MODEL_FILE)
if SAM2_LOADED:
    from adumbra.ia.util.sam2 import model as sam2
else:
    logger.warning("SAM2 model is disabled.")


ZIM_LOADED = os.path.isdir(Config.ZIM_MODEL_FILE)
if ZIM_LOADED:
    from adumbra.ia.util.zim import model as zim
else:
    logger.warning("ZIM model is disabled.")


api = Namespace("model", description="Model related operations")

image_upload = reqparse.RequestParser()
image_upload.add_argument(
    "image", location="files", type=FileStorage, required=True, help="Image"
)

sam_args = reqparse.RequestParser()
sam_args.add_argument("data", type=str, required=True)
sam_args.add_argument(
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


@api.route("/sam2")
class MaskRCNN(Resource):

    @api.expect(image_upload)
    def post(self):
        """COCO data test"""
        if not SAM2_LOADED:
            return {"disabled": True, "message": "SAM2 is disabled"}, 400

        args = sam2_args.parse_args()
        # logger.warning("args: {}".format(args))
        data = json.loads(args["data"])
        logger.info(f"data: {data}")

        sam2.setPredictor(
            float(data["threshold"]), float(data["maxhole"]), float(data["maxsprinkle"])
        )
        points = data["points"][0]

        img_file = args["image"]
        im = Image.open(img_file.stream).convert("RGB")
        im = np.asarray(im)

        logger.warning("points: {}".format(points))
        sam2.setImage(im)
        sam2.calcMasks(np.array([points]), np.array([1]))
        sam2.getSegmentation()
        return {"segmentation": sam2.getSegmentation()}


@api.route("/zim")
class MaskRCNN(Resource):

    @api.expect(image_upload)
    def post(self):
        """COCO data test"""
        if not ZIM_LOADED:
            return {"disabled": True, "message": "ZIM is disabled"}, 400

        args = zim_args.parse_args()
        # logger.warning("args: {}".format(args))
        data = json.loads(args["data"])
        points = data["points"][0]

        img_file = args["image"]
        im = Image.open(img_file.stream).convert("RGB")
        im = np.asarray(im)

        logger.warning("points: {}".format(points))
        zim.setImage(im)
        zim.calcMasks(np.array([points]), np.array([1]))
        zim.getSegmentation()
        return {"segmentation": zim.getSegmentation()}

import json
import logging

import numpy as np
from flask_restx import Namespace, Resource, reqparse
from PIL import Image
from werkzeug.datastructures import FileStorage

from adumbra.ia.util.helpers import getSegmentation
from adumbra.ia.util.sam2 import model as sam2
from adumbra.ia.util.zim import model as zim

logger = logging.getLogger("gunicorn.error")


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

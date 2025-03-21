import datetime
import logging

from flask_login import current_user, login_required
from flask_restx import Namespace, Resource, reqparse

from adumbra.database import AnnotationModel
from adumbra.util import api_bridge

logger = logging.getLogger("gunicorn.error")

api = Namespace("annotation", description="Annotation related operations")

create_annotation = reqparse.RequestParser()
create_annotation.add_argument("image_id", type=int, required=True, location="json")
create_annotation.add_argument("category_id", type=int, location="json")
create_annotation.add_argument("isbbox", type=bool, location="json")
create_annotation.add_argument("metadata", type=dict, location="json")
create_annotation.add_argument("segmentation", type=list, location="json")
create_annotation.add_argument("keypoints", type=list, location="json")
create_annotation.add_argument("color", location="json")

update_annotation = reqparse.RequestParser()
update_annotation.add_argument("category_id", type=int, location="json")


@api.route("/")
class Annotation(Resource):

    @login_required
    def get(self):
        """Returns all annotations"""
        return api_bridge.queryset_to_json(
            current_user.annotations.exclude("paper_object").all()
        )

    @api.expect(create_annotation)
    @login_required
    def post(self):
        """Creates an annotation"""
        args = create_annotation.parse_args()
        image_id = args.get("image_id")
        category_id = args.get("category_id")
        isbbox = args.get("isbbox")
        metadata = args.get("metadata", {})
        segmentation = args.get("segmentation", [])
        keypoints = args.get("keypoints", [])

        image = current_user.images.filter(id=image_id, deleted=False).first()
        if image is None:
            return {"message": "Invalid image id"}, 400

        logger.info(
            f"{current_user.username} has created an annotation for image {image_id} with {isbbox}"
        )
        logger.info(
            f"{current_user.username} has created an annotation for image {image_id}"
        )

        try:
            annotation = AnnotationModel(
                image_id=image_id,
                category_id=category_id,
                metadata=metadata,
                segmentation=segmentation,
                keypoints=keypoints,
                isbbox=isbbox,
            )
            annotation.save()
        except (ValueError, TypeError) as e:
            return {"message": str(e)}, 400

        return api_bridge.queryset_to_json(annotation)


@api.route("/<int:annotation_id>")
class AnnotationId(Resource):

    @login_required
    def get(self, annotation_id):
        """Returns annotation by ID"""
        annotation = current_user.annotations.filter(id=annotation_id).first()

        if annotation is None:
            return {"message": "Invalid annotation id"}, 400

        return api_bridge.queryset_to_json(annotation)

    @login_required
    def delete(self, annotation_id):
        """Deletes an annotation by ID"""
        annotation = current_user.annotations.filter(id=annotation_id).first()

        if annotation is None:
            return {"message": "Invalid annotation id"}, 400

        image = current_user.images.filter(
            id=annotation.image_id, deleted=False
        ).first()
        # Set image thumbnail to be regenerated
        image.update(regenerate_thumbnail=True)

        annotation.update(set__deleted=True, set__deleted_date=datetime.datetime.now())
        return {"success": True}

    @api.expect(update_annotation)
    @login_required
    def put(self, annotation_id):
        """Updates an annotation by ID"""
        annotation = current_user.annotations.filter(id=annotation_id).first()

        if annotation is None:
            return {"message": "Invalid annotation id"}, 400

        args = update_annotation.parse_args()

        new_category_id = args.get("category_id")
        annotation.update(category_id=new_category_id)
        logger.info(
            f"{current_user.username} has updated category for annotation (id: {annotation.id})"
        )
        newAnnotation = current_user.annotations.filter(id=annotation_id).first()
        return api_bridge.queryset_to_json(newAnnotation)

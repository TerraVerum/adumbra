import datetime

from flask import send_file
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource

from adumbra.database import ExportModel, fix_ids
from adumbra.util import api_bridge

api = Namespace("export", description="Export related operations")


@api.route("/<int:export_id>")
class DatasetExportsRoot(Resource):

    @login_required
    def get(self, export_id):
        """Returns exports"""
        export = ExportModel.objects(id=export_id).first()
        if export is None:
            return {"message": "Invalid export ID"}, 400

        dataset = current_user.datasets.filter(id=export.dataset_id).first()
        if dataset is None:
            return {"message": "Invalid dataset ID"}, 400

        time_delta = datetime.datetime.utcnow() - export.created_at
        d = fix_ids(export)
        d["ago"] = api_bridge.to_human_timedelta_str(time_delta)
        return d

    @login_required
    def delete(self, export_id):
        """Returns exports"""
        export = ExportModel.objects(id=export_id).first()
        if export is None:
            return {"message": "Invalid export ID"}, 400

        dataset = current_user.datasets.filter(id=export.dataset_id).first()
        if dataset is None:
            return {"message": "Invalid dataset ID"}, 400

        export.delete()
        return {"success": True}


@api.route("/<int:export_id>/download")
class DatasetExportsDownload(Resource):

    @login_required
    def get(self, export_id):
        """Returns exports"""

        export = ExportModel.objects(id=export_id).first()
        if export is None:
            return {"message": "Invalid export ID"}, 400

        dataset = current_user.datasets.filter(id=export.dataset_id).first()
        if dataset is None:
            return {"message": "Invalid dataset ID"}, 400

        if not current_user.can_download(dataset):
            return {
                "message": (
                    "You do not have permission to download the dataset's annotations"
                )
            }, 403

        encoded_dataset_name = dataset.name.encode("utf-8")
        return send_file(
            export.path,
            download_name=f"{encoded_dataset_name}-{'-'.join(export.tags).encode('utf-8')}.json",
            as_attachment=True,
        )

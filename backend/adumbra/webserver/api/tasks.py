from flask_login import login_required
from flask_restx import Namespace, Resource

from adumbra.database import TaskModel
from adumbra.util import api_bridge

api = Namespace("tasks", description="Task related operations")


@api.route("/")
class Task(Resource):
    @login_required
    def get(self):
        """Returns all tasks"""
        query = TaskModel.objects.only(
            "group",
            "id",
            "name",
            "completed",
            "progress",
            "priority",
            "creator",
            "desciption",
            "errors",
            "warnings",
        ).all()
        return api_bridge.queryset_to_json(query)


@api.route("/<int:task_id>")
class TaskId(Resource):
    @login_required
    def delete(self, task_id):
        """Deletes task"""
        task = TaskModel.objects(id=task_id).first()

        if task is None:
            return {"message": "Invalid task id"}, 400

        if not task.completed:
            return {"message": "Task is not completed"}, 400

        task.delete()
        return {"success": True}


@api.route("/<int:task_id>/logs")
class TaskIdLogs(Resource):
    @login_required
    def get(self, task_id):
        """Deletes task"""
        task = TaskModel.objects(id=task_id).first()
        if task is None:
            return {"message": "Invalid task id"}, 400

        return {"logs": task.logs}

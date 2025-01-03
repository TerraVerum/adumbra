from flask_restx import Namespace, Resource

from adumbra.config import CONFIG
from adumbra.database import TaskModel, UserModel
from adumbra.workers.tasks import long_task

api = Namespace("info", description="Software related operations")


@api.route("/")
class Info(Resource):
    def get(self):
        """Returns information about current version"""

        return {
            "name": "Adumbra",
            "author": "Nathan Jessurun, James Drakes, SixK",
            # "demo": "",
            "repo": "https://github.com/TerraVerum/adumbra",
            "git": {"tag": CONFIG.version},
            "login_enabled": not CONFIG.login_disabled,
            "total_users": UserModel.objects.count(),
            "allow_registration": CONFIG.allow_registration,
        }


@api.route("/long_task")
class TaskTest(Resource):
    def get(self):
        """Returns information about current version"""
        task_model = TaskModel(group="test", name="Testing Celery")
        task_model.save()

        task = long_task.delay(20, task_model.id)
        return {"id": task.id, "state": task.state}

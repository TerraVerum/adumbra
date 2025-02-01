import uuid

from adumbra.control import ImageController, ImageState
from drawinsight.event_bus import (
    EventBus,
    EventBusMixin,
    handles_state_change,
    set_global_event_bus,
)
from drawinsight.publishers import PrintPublisher
from drawinsight.types.models import Function, Image, Job, JobPipeline
from drawinsight.types.v1_events import (
    FunctionAddEvent,
    ImageAddEvent,
    JobAddEvent,
    JobPipelineAddEvent,
    JobPipelineRunEvent,
)
from drawinsight.utils.formatters import ANSIColors
from flask import Flask, jsonify, request
from spectralis.constants import SETTINGS
from spectralis.control import FunctionController, JobController, JobQueueController
from spectralis.types import FunctionState, JobQueueControllerState, JobState

from drawinsight.types.v1_events import AddEvent, AppEventV1, UpdateEvent

from drawinsight.types.enums import ObjectTypeEnum

app = Flask(__name__)


class APIWrapper(EventBusMixin):
    def __init__(self):
        super().__init__()
        self.ControllerId = uuid.uuid4()
        old_bus = set_global_event_bus(EventBus())
        FunctionController(ControllerId=self.ControllerId)
        JobQueueController(ControllerId=self.ControllerId)
        JobController(ControllerId=self.ControllerId, asset_path="/")
        ImageController(ControllerId=self.ControllerId, asset_path="/")
        self.seen_images = {}
        self.jobs = {}
        self.init_bus(ControllerId=self.ControllerId)
        set_global_event_bus(old_bus)
        self.get_event_bus().event_callbacks.add_publisher(
            PrintPublisher(colors=ANSIColors())
        )

    @handles_state_change(JobState)
    def on_job_update(self, state: JobState):
        if state.Job is not None:
            self.jobs[str(state.Job.Id)] = state.Job

    @handles_state_change(JobQueueControllerState)
    def on_jobs_update(self, state: JobQueueControllerState):
        pass

    @handles_state_change(FunctionState)
    def on_function_update(self, state: FunctionState):
        pass

    @handles_state_change(ImageState)
    def on_image_update(self, state: ImageState):
        if state.Image is not None:
            self.seen_images[str(state.Image.Id)] = state.Image


api_wrapper = APIWrapper()


# Image Resource
@app.route("/images", methods=["POST"])
def create_image():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    volume_image = Image(
        Id=uuid.UUID(data["Id"]),
        Path=data["Path"],
        Width=data.get("Width", -1),
        Height=data.get("Height", -1),
    )
    api_wrapper.post_event(ImageAddEvent(Object=volume_image))
    return jsonify({"message": "Image created", "image_id": str(volume_image.Id)}), 201


@app.route("/images/<string:image_id>", methods=["GET"])
def get_image(image_id):
    image = api_wrapper.seen_images.get(image_id)
    if not image:
        return jsonify({"error": "Image not found"}), 404
    return jsonify({"image": image.model_dump()})


# Function Resource
@app.route("/functions", methods=["POST"])
def create_function():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    segmentation_function = Function(Filename=data["Filename"])
    api_wrapper.post_event(FunctionAddEvent(Object=segmentation_function))
    return (
        jsonify(
            {
                "message": "Function created",
                "function_id": str(segmentation_function.Id),
            }
        ),
        201,
    )


# Job Resource
@app.route("/jobs", methods=["POST"])
def create_job():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    job = Job(
        Parameter=data.get("Parameter", {}),
        JobInput=data.get("JobInput", {}),
        JobOutput=data.get("JobOutput", {}),
        FunctionId=data["FunctionId"],
    )
    api_wrapper.post_event(JobAddEvent(Object=job))
    return jsonify({"message": "Job created", "job_id": str(job.Id)}), 201


@app.route("/jobs/<string:job_id>", methods=["GET"])
def get_job(job_id):
    job = api_wrapper.jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"job": job.model_dump_json()})


# Job Pipeline Resource
@app.route("/job-pipelines", methods=["POST"])
def create_job_pipeline():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    job_pipeline = JobPipeline(
        JobIds=data.get("JobIds", []),
        JobStageMappings=data.get("JobStageMappings", {}),
    )
    api_wrapper.post_event(JobPipelineAddEvent(Object=job_pipeline))
    return (
        jsonify(
            {"message": "Job pipeline created", "pipeline_id": str(job_pipeline.Id)}
        ),
        201,
    )


@app.route("/job-pipelines/<string:pipeline_id>/run", methods=["POST"])
def run_job_pipeline(pipeline_id):
    api_wrapper.post_event(JobPipelineRunEvent(JobPipelineId=pipeline_id))
    return jsonify({"message": "Pipeline run started", "pipeline_id": pipeline_id}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6543, debug=True)

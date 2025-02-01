import json
from pathlib import Path
import time
from turtle import width
import uuid

from adumbra.database import DatasetModel, ImageModel, TaskModel
from adumbra.workers import celery
from adumbra.workers.socket import create_socket
from adumbra.workers.tasks.thumbnails import thumbnail_generate_single_image
from adumbra.workers.tasks.helpers.drawinsight_helpers import create_job_pipeline, get_image, get_job, int_to_uuid4, run_job_pipeline, spectralis_add_image, create_function, create_job, uuid4_to_int


@celery.task
def split_volume_into_layers(task_id, dataset_id, volume_path):
    task = TaskModel.objects.get(id=task_id)
    dataset = DatasetModel.objects.get(id=dataset_id)

    task.update(status="PROGRESS")
    socket = create_socket()

    volume_model = ImageModel(dataset_id=-1, path=volume_path, width=0, height=0).save()
    volume_model.drawinsight_id = str(int_to_uuid4(volume_model.id))
    volume_model = volume_model.save()
    create_image_response = spectralis_add_image(volume_model)
    if create_image_response.get("status") == "error":
        task.error(f"Error creating image: {create_image_response.get('message')}")
        return
    
    volume = get_image(volume_model.drawinsight_id)
    if volume.get("status") == "error":
        task.error(f"Error getting image: {volume.get('message')}")
        return

    layer_segmentation_function_response = create_function("/workspace/drawinsight-assets/xrayrecon/main.py")
    if layer_segmentation_function_response.get("status") == "error":
        task.error(f"Error creating function: {layer_segmentation_function_response.get('message')}")
        return

    layer_segmentation_function_id = layer_segmentation_function_response["function_id"]
    layer_segmentation_job_input = {"Images": [volume.get("image")]}
    layer_segmentation_job_output = {"Images": []}
    output_path = Path(f"/datasets/{dataset.name}")
    output_path.mkdir(parents=True, exist_ok=True)
    layer_segmentation_job_response = create_job(
        function_id=layer_segmentation_function_id,
        parameter={"AssetPath": str(output_path)},
        job_input=layer_segmentation_job_input,
        job_output=layer_segmentation_job_output,
    )
    if layer_segmentation_job_response.get("status") == "error":
        task.error(f"Error creating job: {layer_segmentation_job_response.get('message')}")
        return

    layer_segmentation_job_id = layer_segmentation_job_response["job_id"]
    job_pipeline_response = create_job_pipeline(
        job_ids=[layer_segmentation_job_id],
        job_stage_mappings={},
    )
    if job_pipeline_response.get("status") == "error":
        task.error(f"Error creating job pipeline: {job_pipeline_response.get('message')}")
        return
    
    job_pipeline_id = job_pipeline_response["pipeline_id"]
    pipeline_response = run_job_pipeline(job_pipeline_id)
    if pipeline_response.get("status") == "error":
        task.error(f"Error running job pipeline: {pipeline_response.get('message')}")
        return
    
    while True:
        time.sleep(5)

        # Step 5: Get the job
        layer_segmentation_job_response = get_job(layer_segmentation_job_id)
        if layer_segmentation_job_response.get("status") != "error":
            if json.loads(layer_segmentation_job_response["job"]).get("Status") != "Running":
                break



    layer_segmentation_job = json.loads(layer_segmentation_job_response["job"])
    images = layer_segmentation_job['JobOutput'].get('Images', [])
    for image in images:
        image_id = image.get('Id')
        image_id = uuid4_to_int(uuid.UUID(image_id))
        image_path = image.get('Path')
        layer = ImageModel.create_from_path(image_path, dataset_id).save()
        layer.drawinsight_id = str(image_id)
        layer.save()

    for image in ImageModel.objects(regenerate_thumbnail=True).all():
        thumbnail_generate_single_image.delay(image.id)

    task.set_progress(100, socket=socket)


__all__ = ["split_volume_into_layers"]

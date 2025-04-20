import json
import os
import time
from base64 import b64encode

import requests

from adumbra.database import AnnotationModel, DatasetModel, ImageModel, TaskModel
from adumbra.database.categories import CategoryModel
from adumbra.workers import celery
from adumbra.workers.socket import create_socket

jobs_api_port = os.getenv("JOBS_API_PORT", 6543)


@celery.task
def segment_task(task_id, dataset_id, job_zip_path, job_name):
    task = TaskModel.objects.get(id=task_id)
    images = ImageModel.objects(dataset_id=dataset_id)
    image_blobs = []
    for image in images:
        with open(image.path, "rb") as f:
            image_blobs.append(
                {"blob": str(b64encode(f.read()).decode()), "id": image.id}
            )
    task.update(status="PROGRESS")
    socket = create_socket()

    data = {
        "name": job_name,
        "input_schema": """{"images":[{"blob":"", "id":""}]}""",
    }

    files = {}
    if job_zip_path is not None:
        with open(job_zip_path, "rb") as f:
            files["zip_file"] = ("file.zip", f, "application/zip")
            response = requests.post(
                f"http://jobs:{jobs_api_port}/api/job_infos",
                files=files,
                data=data,
                timeout=120,
            )
    else:
        response = requests.post(
            f"http://jobs:{jobs_api_port}/api/job_infos",
            data=data,
            timeout=120,
        )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to create job info: {response.text}")
    time.sleep(10)
    data = {
        "job_info_name": job_name,
        "input": f'{{"images": {json.dumps(image_blobs)}}}',
    }
    response = requests.post(
        f"http://jobs:{jobs_api_port}/api/jobs", data=data, timeout=120
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to run job: {response.text}")
    while True:
        response = requests.get(
            f"http://jobs:{jobs_api_port}/api/job_status/{job_name}", timeout=120
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to get job status: {response.text}")
        status = response.json()["status"]
        if status == "not running":
            break
        if status == "error":
            raise RuntimeError("Job failed")
        time.sleep(5)
    response = requests.get(
        f"http://jobs:{jobs_api_port}/api/job_output/{job_name}", timeout=120
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to get job output: {response.text}")
    output = response.json()["output"]
    annotations = json.loads(output)

    for annotation in annotations:
        image = ImageModel.objects.get(id=annotation["image_id"])
        dataset = DatasetModel.objects.get(id=dataset_id)
        category = CategoryModel(
            name=dataset.name + "_" + image.file_name + "_" + annotation["name"],
            keypoint_edges=[],
            keypoint_labels=[],
        )
        category.save()
        dataset.categories.append(category.id)
        dataset.save()
        paperjs_object = [
            "CompoundPath",
            {"children": [["Path", {"segments": annotation["segments"]}]]},
        ]
        AnnotationModel(
            image_id=image.id,
            category_id=category.id,
            paper_object=paperjs_object,
        ).save()
    task.set_progress(100, socket=socket)


__all__ = ["segment_task"]

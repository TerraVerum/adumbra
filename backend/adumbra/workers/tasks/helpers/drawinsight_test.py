from collections import defaultdict
import json
from pathlib import Path
from tabnanny import check
import time
from adumbra.drawinsight_util.drawinsight_helpers import uuid4_to_int
from pydantic import BaseModel
import requests

# Define the Image Pydantic model
class Image(BaseModel):
    Path: str
    Width: int
    Height: int

class Annotation(BaseModel):
    ImageId: str
    ShapeId: str
    MetaData: dict

class Shape(BaseModel):
    Equation: str = "polygon"
    Filled: bool = False
    Connected: bool = True
    Thickness: dict = {"Type": "pixel", "Value": 1}
    # Ideally XYPoints can be strongly typed to only allow two values. But Python
    # doesn't yet support it: https://github.com/python/mypy/issues/8441
    XYPoints: list

class SpectralisInputJobData(BaseModel):
    Images: list

class SpectralisOutputJobData(BaseModel):
    Shapes: list
    Annotations: list

# Define the Job Pydantic model
class Job(BaseModel):
    Parameter: dict = {}
    JobInput: SpectralisInputJobData = SpectralisInputJobData(Images=[])
    JobOutput: SpectralisOutputJobData = SpectralisOutputJobData(Shapes=[], Annotations=[])
    FunctionId: str


# Server URL
BASE_URL = "http://drawinsight-wrapper:6543"
BASE_API_URL = "http://webserver:5001"


def create_function(filename: str):
    """
    Sends a POST request to create a function.

    Args:
        filename (str): Path to the function file.

    Returns:
        dict: JSON response from the server.
    """
    endpoint = f"{BASE_URL}/functions"
    payload = {"Filename": filename}

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def create_job(function_id: str, parameter: dict, job_input: dict, job_output: dict):
    """
    Sends a POST request to create a job.

    Args:
        function_id (str): ID of the function to associate with the job.
        parameter (dict): Parameters for the job.
        job_input (dict): Input data for the job.
        job_output (dict): Output data for the job.

    Returns:
        dict: JSON response from the server.
    """
    endpoint = f"{BASE_URL}/jobs"
    payload = {
        "FunctionId": function_id,
        "Parameter": parameter,
        "JobInput": job_input,
        "JobOutput": job_output,
    }

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def create_job_pipeline(job_ids: list, job_stage_mappings: dict):
    """
    Sends a POST request to create a job pipeline.

    Args:
        job_ids (list): IDs of the jobs to add to the pipeline.
        job_stage_mappings (dict): Mappings of job inputs and outputs to form pipeline.

    Returns:
        dict: JSON response from the server.
    """
    endpoint = f"{BASE_URL}/job-pipelines"
    payload = {
        "JobIds": job_ids,
        "JobStageMappings": job_stage_mappings,
    }

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def run_job_pipeline(pipeline_id: str):
    """
    Sends a POST request to run a job pipeline.

    Args:
        pipeline_id (str): Job pipeline ID to run.

    Returns:
        dict: JSON response from the server.
    """
    endpoint = f"{BASE_URL}/job-pipelines/{pipeline_id}/run"

    try:
        response = requests.post(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def get_image(image_id: str):
    """
    Sends a GET request to retrieve an image.

    Args:
        image_id (str): ID of the image to retrieve.

    Returns:
        dict: JSON response from the server.
    """
    endpoint = f"{BASE_URL}/images/{image_id}"

    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def get_job(job_id: str):
    """
    Sends a GET request to retrieve a job.

    Args:
        job_id (str): ID of the job to retrieve.

    Returns:
        dict: JSON response from the server.
    """
    endpoint = f"{BASE_URL}/jobs/{job_id}"

    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def create_annotations(image_id: str, category_name: str, polygons: list):
    """
    Sends a POST request to create annotations for an image.

    Args:
        image_id (str): ID of the image to annotate.
        category_name (str): Name of the category to annotate.
        polygons (list): List of polygons to annotate.

    Returns:
        dict: JSON response from the server.
    """
    # Step 1: Get the category ID
    endpoint = f"{BASE_API_URL}/api/annotator/drawinsight_draw"
    payload = {
        "image_id": image_id,
        "category_name": category_name,
        "polygons": polygons,
        "user": "vasanths"
    }

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


def create_image(image_id: str, path: str, dataset_id: str):
    """
    Sends a POST request to create annotations for an image.

    Args:
        image_id (str): ID of the image to annotate.
        category_name (str): Name of the category to annotate.
        polygons (list): List of polygons to annotate.

    Returns:
        dict: JSON response from the server.
    """
    # Step 1: Get the category ID
    endpoint = f"{BASE_API_URL}/api/image"
    payload = {
        "image": {
            "stream": None,
            "filename": path,
            "name": f"layer_{image_id}",
            "headers": None,
            "mimetype": "image/jpeg",
            "content_type": "image/jpeg",
            "content_length": 0,
        },
        "image_id": image_id,
        "already_uploaded": True,
        "dataset_id": dataset_id,
        "user": "vasanths"
    }

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    dataset_id = input("Enter the Dataset ID to store layer slices in: ")

    volume_image_id = input("Enter the Volume Image ID: ")
    layer_segmentation_assistant_type = input("Enter the Layer Segmentation assistant type: ")
    layer_segmentation_assistant_name = input("Enter the Layer Segmentation assistant name: ")
    # Step 1: Add a layer segmentation function
    layer_segmentation_base_path = Path("/models") / Path(layer_segmentation_assistant_type) / Path(layer_segmentation_assistant_name)
    layer_segmentation_function_filename = str(layer_segmentation_base_path / Path("layer_segmenter.py"))
    layer_segmentation_function_response = create_function(layer_segmentation_function_filename)
    print("Function Response:", layer_segmentation_function_response)
    if layer_segmentation_function_response.get("status") == "error":
        print("Error creating function:", layer_segmentation_function_response.get("message"))
        exit(1)
    layer_segmentation_function_id = layer_segmentation_function_response["function_id"]
    layer_segmentation_job_parameter = {"AssetPath": str(layer_segmentation_base_path)}
    volume = get_image(volume_image_id)["image"]
    layer_segmentation_job_input = {"Images": [volume]}
    layer_segmentation_job_output = {"Images": []}
    layer_segmentation_job_response = create_job(
        function_id=layer_segmentation_function_id,
        parameter=layer_segmentation_job_parameter,
        job_input=layer_segmentation_job_input,
        job_output=layer_segmentation_job_output,
    )
    print("Job Response:", layer_segmentation_job_response)
    if layer_segmentation_job_response.get("status") == "error":
        print("Error creating job:", layer_segmentation_job_response.get("message"))
        exit(1)

    image_annotation_assistant_type = input("Enter the Image Annotation assistant type: ")
    image_annotation_assistant_name = input("Enter the Image Annotation assistant name: ")
    # Step 1: Add a function
    # TODO: Update hardcoded function filename to a valid function file that
    # has been uploaded to a staging area accessible by the server.
    image_annotation_base_path = Path("/models") / Path(image_annotation_assistant_type) / Path(image_annotation_assistant_name)
    image_annotation_function_filename = str(image_annotation_base_path / Path("trace_segmenter.py"))
    image_annotation_function_response = create_function(image_annotation_function_filename)
    print("Function Response:", image_annotation_function_response)

    if image_annotation_function_response.get("status") == "error":
        print("Error creating function:", image_annotation_function_response.get("message"))
        exit(1)
    image_annotation_function_id = image_annotation_function_response["function_id"]

    # Step 2: Add a job associated with the function
    image_annotation_job_parameter = {"Checkpoint": str(image_annotation_base_path / Path("model.pth")), "ModelType": "vit_h"}
    image_annotation_job_input = {"Images": []}
    image_annotation_job_output = {"Shapes": [], "Annotations": []}
    image_annotation_job_response = create_job(
        function_id=image_annotation_function_id,
        parameter=image_annotation_job_parameter,
        job_input=image_annotation_job_input,
        job_output=image_annotation_job_output,
    )
    print("Job Response:", image_annotation_job_response)

    if image_annotation_job_response.get("status") == "error":
        print("Error creating job:", image_annotation_job_response.get("message"))
        exit(1)

    # Step 3: Add a job pipeline with the created job
    layer_segmentation_job_id = layer_segmentation_job_response["job_id"]
    image_annotation_job_id = image_annotation_job_response["job_id"]
    job_pipeline_response = create_job_pipeline(
        job_ids=[layer_segmentation_job_id, image_annotation_job_id],
        job_stage_mappings={0: {"Images": "Images"}},
    )

    # Step 4: Run a job pipeline with the created job pipeline
    job_pipeline_id = job_pipeline_response["pipeline_id"]
    pipeline_response = run_job_pipeline(job_pipeline_id)
    print("Pipeline Response:", pipeline_response)

    while True:
        time.sleep(5)

        # Step 5: Get the job
        image_annotation_job_response = get_job(image_annotation_job_id)
        if image_annotation_job_response.get("status") != "error":
            if json.loads(image_annotation_job_response["job"]).get("Status") != "Running":
                break

    print("Job:", image_annotation_job_response["job"])
    image_annotation_job = json.loads(image_annotation_job_response["job"])
    # Creating a map of checkpoint paths to shape IDs
    checkpoint_to_shape_ids_map = defaultdict(list)
    annotations = image_annotation_job['JobOutput'].get('Annotations', [])
    for annotation in annotations:
        shape_id = annotation.get('ShapeId')
        checkpoint_path = annotation.get('Metadata', {}).get('checkpoint_path')
        if shape_id and checkpoint_path:
            checkpoint_to_shape_ids_map[checkpoint_path].append(shape_id)


    images = image_annotation_job['JobInput'].get('Images', [])
    for image in images:
        image_id = image.get('Id')
        image_id = str(uuid4_to_int(image_id))
        image_path = image.get('Path')
        resp = create_image(image_id, image_path, dataset_id)
        print("Image Response:", resp)

    # Creating a map of checkpoint paths to shapes
    checkpoint_to_xy_points_map = defaultdict(list)
    # Iterating through shapes and creating a map of checkpoint paths to shapes
    shapes = image_annotation_job['JobOutput'].get('Shapes', [])
    for shape in shapes:
        shape_id = shape.get('Id')
        for checkpoint_path, shape_ids in checkpoint_to_shape_ids_map.items():
            if shape_id in shape_ids:
                checkpoint_to_xy_points_map[checkpoint_path].append(shape.get('XYPoints', []))

    for checkpoint_path, xy_points_list in checkpoint_to_xy_points_map.items():
        modified_xy_points_list = []
        for xy_points in xy_points_list:
            xy_points = [[xy_point[0]-image.get("Width")/2, xy_point[1]-image.get("Height")/2] for xy_point in xy_points]
            modified_xy_points_list.append(xy_points)
        checkpoint_to_xy_points_map[checkpoint_path] = modified_xy_points_list
    # Iterating through checkpoints to create annotations
    for checkpoint_path, xy_points_list in checkpoint_to_xy_points_map.items():
        for xy_points in xy_points_list:
            resp = create_annotations(image_id, checkpoint_path, [xy_points])
            print("Annotation Response:", resp)

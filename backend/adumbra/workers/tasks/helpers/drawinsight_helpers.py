import uuid


def int_to_uuid4(integer_value):
    # Mask the integer to fit within 122 random bits (UUIDv4's random space)
    masked_value = integer_value & ((1 << 122) - 1)

    # Create the UUID bytes from the integer
    uuid_bytes = masked_value.to_bytes(16, byteorder="big")

    # Ensure UUIDv4 compliance:
    # - Set the version (4 bits at index 6)
    uuid_bytes = bytearray(uuid_bytes)
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x40  # Set version to 4
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80  # Set variant to 10xx

    # Convert back to a UUID object
    return uuid.UUID(bytes=bytes(uuid_bytes))


def uuid4_to_int(uuid_value: uuid.UUID):
    uuid_bytes = uuid_value.bytes
    uuid_bytes = bytearray(uuid_bytes)
    uuid_bytes[6] = 0
    uuid_bytes[8] = 0
    uuid_bytes = bytes(uuid_bytes)
    uuid_int = int.from_bytes(uuid_bytes, byteorder="big")
    return uuid_int


def convert_polygons_to_compound_path(
    polygons, annotationId, categoryId, fill_color=[0, 0.7, 0.3], opacity=0.6
):
    """
    Convert a list of polygons to a compoundPath JSON array with annotationId and categoryId.

    Args:
        polygons (list): List of polygons, where each polygon is a list of [x, y] pairs.
        annotationId (int): ID for the annotation.
        categoryId (int): ID for the category.
        fill_color (list): RGB values for the fill color of the compound path.
        opacity (float): Opacity of the compound path.

    Returns:
        dict: A JSON-like dictionary representing the compoundPath structure.
    """
    # Convert each polygon into a child Path
    children = []
    for polygon in polygons:
        path = ["Path", {"applyMatrix": True, "segments": polygon, "closed": True}]
        children.append(path)

    # Create the compoundPath structure
    compound_path = [
        "CompoundPath",
        {
            "applyMatrix": True,
            "opacity": opacity,
            "data": {"annotationId": annotationId, "categoryId": categoryId},
            "children": children,
            "fillColor": fill_color,
            "strokeWidth": 0,
        },
    ]
    return compound_path

import os
import requests


BASE_URL = "http://drawinsight-wrapper:6543"
BASE_API_URL = "http://webserver:5001"

def spectralis_add_image(image_model):
    """
    Sends a POST request to add an image to the server.

    Args:
        path (str): Path to the image.
        width (int): Width of the image (default: -1).
        height (int): Height of the image (default: -1).

    Returns:
        dict: JSON response from the server.
    """
    endpoint = f"{BASE_URL}/images"
    payload = {
        "Id": image_model.drawinsight_id,
        "Path": image_model.path,
        "Width": image_model.width,
        "Height": image_model.height,
    }

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}


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
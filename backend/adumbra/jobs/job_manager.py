import logging
import traceback
from pathlib import Path
from typing import Literal

import docker
import docker.errors
import requests
from pydantic import BaseModel

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/adumbra_job_manager.log'),
        logging.StreamHandler()  # This will keep console output as well
    ]
)

class JobInfo(BaseModel):
    ObjectType: Literal["JobInfo"] = "JobInfo"
    Name: str
    SavePath: str
    InputSchema: dict
    Status: str


class DockerJobManager:
    def __init__(self):
        self.client = docker.from_env()
        self.running_containers = {}
        self.job_name_to_job_info: dict[str, JobInfo] = {}
        self.job_name_to_job_input: dict[str, str] = {}
        self.job_outputs = {}

    def start_job(self, job_info: JobInfo):
        """
        Build a Docker image from the folder at job_info.SavePath (containing
        a Dockerfile + a Python HTTP server on port 7654) and run a container.
        """
        build_path = Path(job_info.SavePath)
        image_tag = job_info.Name.lower()
        logging.debug(
            f"Building Docker image for job {job_info.Name} from {build_path}"
        )
        try:
            # Try to get existing image first
            existing_image = self.client.images.list(name=image_tag)
            if existing_image:
                image = existing_image[0]
                logging.debug(f"Found existing image {image_tag}")
            else:
                # Image doesn't exist, build it
                image, build_logs = self.client.images.build(
                    path=str(build_path), tag=image_tag, rm=True
                )
                logging.debug(f"Build logs: {build_logs}")
        except (docker.errors.APIError, TypeError) as e:
            logging.error(f"Failed to build/get container {job_info.Name}: {e}")
            traceback.print_exc()
            return
        try:
            # Check for existing container first
            existing_containers = self.client.containers.list(
                all=True,  # Include stopped containers
                filters={"ancestor": image.id}
            )
            if existing_containers:
                container = existing_containers[0]
                logging.debug(f"Found existing container for image {image_tag}")
            else:
                # Create new container if none exists
                container = self.client.containers.create(
                    image,
                    detach=True,
                    ports={"7654/tcp": None},  # Map container 7654 -> host random
                )
                logging.debug(f"Created new container for image {image_tag}")
        except (docker.errors.ImageNotFound, docker.errors.APIError) as e:
            logging.error(f"Failed to create container {job_info.Name}: {e}")
            traceback.print_exc()
            return
        try:
            container.start()
        except docker.errors.APIError as e:
            logging.error(f"Failed to start container {job_info.Name}: {e}")
            traceback.print_exc()
            return
        logging.debug(f"Started container {container.short_id} for job {job_info.Name}")
        self.running_containers[job_info.Name] = container
        self.job_name_to_job_info[job_info.Name] = job_info

    def send_input_to_job(self, job_info_name: str, input_str: str):
        """
        Send "input" to the job via a POST request to http://host:mapped_port/input.
        """
        container = self.running_containers.get(job_info_name)
        if not container:
            logging.error(f"No running container found for job {job_info_name}")
            return
        self.job_name_to_job_input[job_info_name] = input_str
        container.reload()
        port_data = container.attrs["NetworkSettings"]["Ports"].get("7654/tcp")
        if not port_data or not isinstance(port_data, list) or len(port_data) == 0:
            logging.error(
                f"Container for {job_info_name} does not have port 7654/tcp exposed."
            )
            return
        host_port = port_data[0]["HostPort"]
        url = f"http://localhost:{host_port}/input"
        logging.error(f"Sending POST request to {url} with data: {input_str}")
        response = requests.post(url, data=input_str.encode("utf-8"), timeout=10)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logging.error(f"Error sending input to job {job_info_name}: {e}")
            traceback.print_exc()
            return
        logging.error(
            f"Successfully posted input to {job_info_name}. Response: {response.text}"
        )

    def read_output(self, job_info_name: str):
        """
        Instead of reading container logs, we'll do a GET request to /output
        on the container's port 7654, parse the JSON we get back,
        and post events accordingly.
        """
        container = self.running_containers.get(job_info_name)
        if not container:
            logging.error(f"No running container found for job {job_info_name}")
            return None
        container.reload()
        port_data = container.attrs["NetworkSettings"]["Ports"].get("7654/tcp")
        if not port_data or not isinstance(port_data, list) or len(port_data) == 0:
            logging.error(
                f"Container for {job_info_name} does not have port 7654/tcp exposed."
            )
            return None
        host_port = port_data[0]["HostPort"]
        url = f"http://localhost:{host_port}/output"
        logging.debug(f"Requesting output from {url}")
        response = requests.get(url, timeout=10)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logging.error(f"Error fetching output from /output endpoint: {e}")
            traceback.print_exc()
            return None
        output_json = response.text
        logging.debug(f"Raw output from job {job_info_name}: {output_json}")
        self.job_outputs[job_info_name] = output_json
        return output_json

    def read_container_status(self, job_info_name: str) -> str | None:
        container = self.running_containers.get(job_info_name)
        if not container:
            logging.error(f"No container created with name {job_info_name}")
            return None
        container.reload()
        return container.attrs["State"]["Status"]  # e.g. 'running', 'exited', etc.

    def read_status(self, job_info_name: str) -> str | None:
        """
        Call the container's /status endpoint to see if handle_input is still running
        or some other job status. This no longer relies on Docker's container status.
        """
        container = self.running_containers.get(job_info_name)
        if not container:
            logging.error(f"No container found with name {job_info_name}")
            return None
        # We only need the container to still be running at Docker-level,
        # but the "actual" job status is from the /status endpoint.
        container.reload()
        port_data = container.attrs["NetworkSettings"]["Ports"].get("7654/tcp")
        if not port_data or not isinstance(port_data, list) or len(port_data) == 0:
            logging.error(
                f"Container for {job_info_name} does not have port 7654/tcp exposed."
            )
            return None
        host_port = port_data[0]["HostPort"]
        url = f"http://localhost:{host_port}/status"
        logging.debug(f"Requesting status from {url}")
        response = requests.get(url, timeout=10)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logging.error(f"Error fetching status from /status endpoint: {e}")
            traceback.print_exc()
            return None
        return response.text.strip()

    def get_job_info_by_name(self, job_info_name: str) -> JobInfo | None:
        return self.job_name_to_job_info.get(job_info_name)

    def get_all_jobs(self) -> list[str]:
        """
        Get all jobs by retrieving Docker image names on this machine.
        Returns the base image names without the ':latest' tag.
        """
        try:
            images = self.client.images.list()
            job_images = []
            for image in images:
                # Images can have multiple tags
                for tag in image.tags:
                    job_images.append(tag)
            return job_images
        except docker.errors.APIError as e:
            logging.error(f"Failed to list Docker images: {e}")
            traceback.print_exc()
            return []  # Return empty list instead of None on error

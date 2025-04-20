import json
import logging
import typing
import zipfile
from pathlib import Path

import uvicorn
from fastapi import APIRouter, FastAPI, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict

from .job_manager import DockerJobManager, JobInfo

job_manager: DockerJobManager = DockerJobManager()


class CreateJobInfoRequest(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    zip_file: UploadFile | None = None
    name: str
    input_schema: str


class RunJobRequest(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    job_info_name: str
    input: str


Model_T = typing.TypeVar("Model_T", bound=BaseModel)
AsForm = typing.Annotated[Model_T, Form(media_type="multipart/form-data")]
AsQuery = typing.Annotated[Model_T, Query()]

logger = logging.getLogger(__name__)

# TODO: Fix naming of endpoints
# Initialize FastAPI application
app = FastAPI(
    title="Jobs API",
    description="API for jobs",
    version="1.0.0",
    swagger_ui_parameters={"defaultModelRendering": "model"},
)
router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/job_infos")
async def create_and_spin_up_job_info(request: AsForm[CreateJobInfoRequest]):
    """
    Create a new job info model with the given parameters.
    """
    save_path = Path("/tmp/job_infos") / request.name
    save_path.mkdir(parents=True, exist_ok=True)
    job_zip_file = request.zip_file
    if job_zip_file is not None:
        if zipfile.is_zipfile(job_zip_file.file):
            with zipfile.ZipFile(job_zip_file.file, "r") as zip_ref:
                zip_ref.extractall(save_path)
        else:
            assert job_zip_file.filename is not None
            with open(save_path / job_zip_file.filename, "wb") as buffer:
                buffer.write(job_zip_file.file.read())
    input_schema = json.loads(request.input_schema)
    job_info = JobInfo(
        Name=request.name,
        SavePath=str(save_path),
        InputSchema=input_schema,
        Status="not running",
    )
    job_manager.start_job(job_info)
    return {"status": "success"}


@router.post("/jobs")
async def run_job(request: AsForm[RunJobRequest]):
    """
    Create a new job info model with the given parameters.
    """
    job_info = job_manager.get_job_info_by_name(request.job_info_name)
    if job_info is None:
        raise HTTPException(status_code=404, detail="Job info not found")
    job_manager.send_input_to_job(request.job_info_name, request.input)
    return {"status": "success"}


@router.get("/job_output/{job_info_name}")
async def get_job_output(job_info_name: str):
    """
    Retrieve the output of a job given its job ID.
    """
    job_output = job_manager.read_output(job_info_name)

    if job_output is None:
        raise HTTPException(status_code=404, detail="Job output not found")

    return {"job_info_name": job_info_name, "output": job_output}


@router.get("/container_status/{job_info_name}")
async def get_container_status(job_info_name: str):
    """
    Retrieve the status of a job given its job ID.
    """
    job_status = job_manager.read_container_status(job_info_name)

    if job_status is None:
        raise HTTPException(status_code=404, detail="Job output not found")

    return {"job_info_name": job_info_name, "status": job_status}


@router.get("/job_status/{job_info_name}")
async def get_job_status(job_info_name: str):
    """
    Retrieve the status of a job given its job ID.
    """
    job_status = job_manager.read_status(job_info_name)

    if job_status is None:
        raise HTTPException(status_code=404, detail="Job output not found")

    return {"job_info_name": job_info_name, "status": job_status}

@router.get("/jobs")
async def get_all_jobs():
    """
    Get all jobs by retrieving Docker image names on this machine.
    """
    jobs = job_manager.get_all_jobs()

    if jobs is None:
        raise HTTPException(status_code=500, detail="Failed to get all jobs")

    return {"jobs": jobs}


# TODO: Allow for this port to be dynamically defined
# Include the router in the FastAPI app
app.include_router(router)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

from time import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field


class ProcessJobCreate(BaseModel):
    """Model for creating a new process job."""

    title: str = Field(..., description="Title of the process job", frozen=True)
    description: str = Field(
        ..., description="Description of the process job", frozen=True
    )
    priority: int = Field(..., description="Priority of the process job", frozen=True)


class ProcessJob(ProcessJobCreate):
    """A process job is a task that is being executed in the background."""

    id: str = Field(..., description="ID of the process job", frozen=True)
    created_at: str = Field(
        default_factory=lambda: str(time()),
        description="Creation timestamp of the process job (in seconds)",
        frozen=True,
    )


job_router = APIRouter(
    prefix="/job",
    tags=["job"],
)


@job_router.post("/create")
async def create_job(job: ProcessJobCreate) -> ProcessJob:
    """
    Create a new process job.

    Returns:
        str: ID of the created process job.
    """
    # TODO: implement
    return ProcessJob(id="job_id", **job.model_dump())


@job_router.get("/get_status")
async def get_job_status(job_id: str) -> dict[str, str]:
    # TODO: implement
    return {
        "id": job_id,
        "status": "running",
    }


@job_router.get("/get_result")
async def get_job_result(job_id: str) -> dict[str, Any]:
    # TODO: implement
    return {
        "id": job_id,
        "status": "completed",
        "text": "Hello from Altron!",
        "images": [],
    }


@job_router.delete("/terminate")
async def terminate_job(job_id: str) -> dict[str, str]:
    # TODO: implement
    return {
        "id": job_id,
        "status": "terminated",
    }


router = APIRouter(
    prefix="/subprocess",
    tags=["subprocess"],
)
router.include_router(job_router)

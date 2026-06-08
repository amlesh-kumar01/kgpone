from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from celery.result import AsyncResult
from src.tasks.sample_tasks import add_numbers

router = APIRouter()

class TaskTriggerRequest(BaseModel):
    x: int
    y: int

class TaskTriggerResponse(BaseModel):
    task_id: str
    status: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: int | None = None
    error: str | None = None

@router.post("/trigger", response_model=TaskTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_task(payload: TaskTriggerRequest):
    """
    Triggers the sample 'add_numbers' celery task.
    """
    try:
        task = add_numbers.delay(payload.x, payload.y)
        return TaskTriggerResponse(task_id=task.id, status=task.status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue task: {str(e)}"
        )

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Retrieves the execution status and result of a Celery task.
    """
    try:
        res = AsyncResult(task_id)
        response = TaskStatusResponse(
            task_id=task_id,
            status=res.status
        )
        if res.ready():
            if res.successful():
                response.result = res.result
            else:
                response.error = str(res.result)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task status: {str(e)}"
        )

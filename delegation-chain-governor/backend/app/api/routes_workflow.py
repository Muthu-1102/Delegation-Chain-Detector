from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core import workflow_store
from app.schemas import WorkflowStatusResponse

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.get("/{request_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(request_id: str) -> WorkflowStatusResponse:
    workflow = workflow_store.get(request_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown request_id")

    return WorkflowStatusResponse(**workflow)

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import workflow_store
from app.db.session import get_db
from app.schemas import WorkflowStatusResponse

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.get("/{request_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(request_id: str, db: AsyncSession = Depends(get_db)) -> WorkflowStatusResponse:
    workflow = await workflow_store.get(db, request_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown request_id")

    return WorkflowStatusResponse(**workflow)
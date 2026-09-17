from fastapi import APIRouter

from app.tools.approval_tool import update_approval


router = APIRouter(
    prefix="/approvals",
    tags=["Approvals"]
)


@router.post("/{approval_id}/{decision}")
def process_approval(
    approval_id: int,
    decision: str
):
    return update_approval(
        approval_id=approval_id,
        decision=decision
    )
from fastapi import APIRouter

from app.database.database import SessionLocal
from app.database.models import ApprovalRequest


router = APIRouter(
    prefix="/approvals",
    tags=["Approvals"]
)


@router.get("/pending")
def get_pending_approvals():

    db = SessionLocal()

    try:
        approvals = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.status == "pending")
            .order_by(ApprovalRequest.id.desc())
            .all()
        )

        return [
            {
                "id": approval.id,
                "customer_id": approval.customer_id,
                "order_id": approval.order_id,
                "amount": approval.amount,
                "reason": approval.reason,
                "status": approval.status
            }
            for approval in approvals
        ]

    finally:
        db.close()
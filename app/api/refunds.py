from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.database import SessionLocal
from app.database.models import Refund
from app.control_tower.control_tower import evaluate_refund_request
from app.tools.refund_request_tool import create_canonical_refund_request


router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"]
)


class RefundRequest(BaseModel):
    customer_id: int
    order_id: int
    refund_amount: float
    reason: str


@router.post("/request")
def create_refund_request(request: RefundRequest):

    result = create_canonical_refund_request(
        customer_id=request.customer_id,
        order_id=request.order_id,
        requested_amount=request.refund_amount,
        reason=request.reason,
    )

    if not result["success"]:
        if result["error"] == "Order not found for this customer":
            raise HTTPException(
                status_code=404,
                detail=result["error"],
            )

        raise HTTPException(
            status_code=400,
            detail=result["error"],
        )

    control_tower_result = evaluate_refund_request(
        refund_request_id=result["refund_request_id"]
    )

    return control_tower_result


@router.get("/")
def get_refunds():

    db = SessionLocal()

    try:
        refunds = (
            db.query(Refund)
            .order_by(Refund.id.desc())
            .all()
        )

        return [
            {
                "id": refund.id,
                "customer_id": refund.customer_id,
                "order_id": refund.order_id,
                "amount": refund.amount,
                "status": refund.status,
                "reason": refund.reason
            }
            for refund in refunds
        ]

    finally:
        db.close()
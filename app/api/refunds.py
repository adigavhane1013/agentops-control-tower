from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.database import SessionLocal
from app.database.models import Order, Refund
from app.control_tower.control_tower import evaluate_refund_request


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

    db = SessionLocal()

    try:
        order = (
            db.query(Order)
            .filter(
                Order.id == request.order_id,
                Order.customer_id == request.customer_id
            )
            .first()
        )

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Customer or order not found"
            )

        result = evaluate_refund_request(
            customer_id=request.customer_id,
            order_id=request.order_id,
            refund_amount=request.refund_amount,
            order_amount=order.amount,
            reason=request.reason
        )

        return result

    finally:
        db.close()


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
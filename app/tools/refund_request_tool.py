from app.database.database import SessionLocal
from app.database.models import Order, RefundRequest


def create_canonical_refund_request(
    customer_id: int,
    order_id: int,
    requested_amount: float,
    reason: str,
) -> dict:
    """
    Create the authoritative RefundRequest.

    This function validates the customer/order relationship and
    persists the original requested amount. It does not evaluate
    refund policy and does not execute a refund.
    """

    if customer_id <= 0:
        return {
            "success": False,
            "error": "Invalid customer ID",
        }

    if order_id <= 0:
        return {
            "success": False,
            "error": "Invalid order ID",
        }

    if requested_amount <= 0:
        return {
            "success": False,
            "error": "Refund amount must be greater than zero",
        }

    db = SessionLocal()

    try:
        order = (
            db.query(Order)
            .filter(
                Order.id == order_id,
                Order.customer_id == customer_id,
            )
            .first()
        )

        if order is None:
            return {
                "success": False,
                "error": "Order not found for this customer",
            }

        refund_request = RefundRequest(
            customer_id=customer_id,
            order_id=order_id,
            requested_amount=requested_amount,
            reason=reason,
            status="pending",
        )

        db.add(refund_request)
        db.commit()
        db.refresh(refund_request)

        return {
            "success": True,
            "refund_request_id": refund_request.id,
            "customer_id": refund_request.customer_id,
            "order_id": refund_request.order_id,
            "requested_amount": refund_request.requested_amount,
            "reason": refund_request.reason,
            "status": refund_request.status,
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "error": str(e),
        }

    finally:
        db.close()
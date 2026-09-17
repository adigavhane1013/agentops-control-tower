from app.database.database import SessionLocal
from app.database.models import Refund


def execute_refund(
    customer_id: int,
    order_id: int,
    amount: float,
    reason: str
) -> dict:
    """Record an approved refund in the database."""

    db = SessionLocal()

    try:
        refund = Refund(
            customer_id=customer_id,
            order_id=order_id,
            amount=amount,
            status="processed",
            reason=reason
        )

        db.add(refund)
        db.commit()
        db.refresh(refund)

        return {
            "success": True,
            "refund_id": refund.id,
            "customer_id": refund.customer_id,
            "order_id": refund.order_id,
            "amount": refund.amount,
            "status": refund.status,
            "reason": refund.reason
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close()
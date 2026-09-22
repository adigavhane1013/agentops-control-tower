from app.database.database import SessionLocal
from app.database.models import Customer, Order, Refund, RefundRequest


def execute_refund(
    refund_request_id: int,
) -> dict:
    """
    Final refund execution boundary.

    Only the canonical RefundRequest ID is accepted.
    All financial and identity information is resolved from
    the database.
    """

    if refund_request_id <= 0:
        raise ValueError("Invalid refund request ID")

    db = SessionLocal()

    try:
        # --------------------------------------------------
        # 1. Load canonical refund request
        # --------------------------------------------------

        refund_request = (
            db.query(RefundRequest)
            .filter(RefundRequest.id == refund_request_id)
            .first()
        )

        if refund_request is None:
            return {
                "success": False,
                "error": "Refund request not found",
            }

        # --------------------------------------------------
        # 2. Validate canonical customer
        # --------------------------------------------------

        if refund_request.customer_id <= 0:
            raise ValueError("Invalid customer ID")

        customer = (
            db.query(Customer)
            .filter(Customer.id == refund_request.customer_id)
            .first()
        )

        if customer is None:
            return {
                "success": False,
                "error": "Customer not found",
            }

        # --------------------------------------------------
        # 3. Validate canonical order
        # --------------------------------------------------

        if refund_request.order_id <= 0:
            raise ValueError("Invalid order ID")

        order = (
            db.query(Order)
            .filter(
                Order.id == refund_request.order_id,
                Order.customer_id == refund_request.customer_id,
            )
            .first()
        )

        if order is None:
            return {
                "success": False,
                "error": "Order not found for this customer",
            }

        # --------------------------------------------------
        # 4. Validate canonical amount
        # --------------------------------------------------

        if refund_request.requested_amount <= 0:
            raise ValueError(
                "Refund amount must be greater than zero"
            )

        if refund_request.requested_amount > order.amount:
            raise ValueError(
                "Refund amount exceeds order amount"
            )

        # --------------------------------------------------
        # 5. Check for an existing refund FIRST
        # --------------------------------------------------

        existing_refund = (
            db.query(Refund)
            .filter(
                Refund.refund_request_id == refund_request_id
            )
            .first()
        )

        if existing_refund is not None:

            if refund_request.status != "processed":
                return {
                    "success": False,
                    "error": (
                        "Refund already exists but the "
                        "refund request state is inconsistent"
                    ),
                }

            return {
                "success": True,
                "refund_id": existing_refund.id,
                "refund_request_id": existing_refund.refund_request_id,
                "customer_id": existing_refund.customer_id,
                "order_id": existing_refund.order_id,
                "amount": existing_refund.amount,
                "status": existing_refund.status,
                "reason": existing_refund.reason,
                "idempotent": True,
            }

        # --------------------------------------------------
        # 6. Only approved requests can execute
        # --------------------------------------------------

        if refund_request.status != "approved":
            return {
                "success": False,
                "error": (
                    "Refund request is not approved for execution"
                ),
            }

        # --------------------------------------------------
        # 7. Create refund from canonical values
        # --------------------------------------------------

        refund = Refund(
            customer_id=refund_request.customer_id,
            order_id=refund_request.order_id,
            refund_request_id=refund_request.id,
            amount=refund_request.requested_amount,
            status="processed",
            reason=refund_request.reason,
        )

        db.add(refund)

        # --------------------------------------------------
        # 8. Mark request as processed
        # --------------------------------------------------

        refund_request.status = "processed"

        db.commit()
        db.refresh(refund)

        return {
            "success": True,
            "refund_id": refund.id,
            "refund_request_id": refund.refund_request_id,
            "customer_id": refund.customer_id,
            "order_id": refund.order_id,
            "amount": refund.amount,
            "status": refund.status,
            "reason": refund.reason,
            "idempotent": False,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
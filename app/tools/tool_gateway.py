from app.database.database import SessionLocal
from app.database.models import Customer, Order, Refund, RefundRequest
from app.tools.refund_tool import execute_refund


def execute_refund_through_gateway(refund_request_id: int) -> dict:
    """
    Central security gateway for refund execution.

    The caller provides only the canonical RefundRequest ID.
    All financial and identity values are resolved from the database.

    Execution is allowed only for an approved RefundRequest.
    A refund can only be created once for a request.
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
        # 2. Validate canonical customer ID
        # --------------------------------------------------

        if refund_request.customer_id <= 0:
            raise ValueError("Invalid customer ID")

        # --------------------------------------------------
        # 3. Validate canonical order ID
        # --------------------------------------------------

        if refund_request.order_id <= 0:
            raise ValueError("Invalid order ID")

        # --------------------------------------------------
        # 4. Validate canonical requested amount
        # --------------------------------------------------

        if refund_request.requested_amount <= 0:
            raise ValueError(
                "Refund amount must be greater than zero"
            )

        # --------------------------------------------------
        # 5. Confirm customer exists
        # --------------------------------------------------

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
        # 6. Confirm order belongs to customer
        # --------------------------------------------------

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
        # 7. Refund cannot exceed order amount
        # --------------------------------------------------

        if refund_request.requested_amount > order.amount:
            raise ValueError(
                "Refund amount exceeds order amount"
            )

        # --------------------------------------------------
        # 8. Lifecycle authorization
        # --------------------------------------------------

        if refund_request.status == "processed":
            existing_refund = (
                db.query(Refund)
                .filter(
                    Refund.refund_request_id == refund_request_id
                )
                .first()
            )

            if existing_refund is not None:
                return {
                    "success": True,
                    "refund_id": existing_refund.id,
                    "customer_id": existing_refund.customer_id,
                    "order_id": existing_refund.order_id,
                    "amount": existing_refund.amount,
                    "status": existing_refund.status,
                    "reason": existing_refund.reason,
                    "idempotent": True,
                }

            return {
                "success": False,
                "error": "Refund request is already processed",
            }

        if refund_request.status != "approved":
            return {
                "success": False,
                "error": (
                    "Refund request is not approved for execution"
                ),
            }

        # --------------------------------------------------
        # 9. Prevent duplicate execution
        # --------------------------------------------------

        existing_refund = (
            db.query(Refund)
            .filter(
                Refund.refund_request_id == refund_request_id
            )
            .first()
        )

        if existing_refund is not None:
            refund_request.status = "processed"
            db.commit()

            return {
                "success": True,
                "refund_id": existing_refund.id,
                "customer_id": existing_refund.customer_id,
                "order_id": existing_refund.order_id,
                "amount": existing_refund.amount,
                "status": existing_refund.status,
                "reason": existing_refund.reason,
                "idempotent": True,
            }

        # --------------------------------------------------
        # 10. Execute using canonical database values
        # --------------------------------------------------

        refund_result = execute_refund(
            refund_request_id=refund_request.id,
        )

        if not refund_result["success"]:
            return refund_result

        # --------------------------------------------------
        # 11. Mark canonical request as processed
        # --------------------------------------------------

        refund_request.status = "processed"
        db.commit()

        return refund_result

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
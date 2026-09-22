from app.database.database import SessionLocal
from app.database.models import ApprovalRequest, RefundRequest
from app.tools.tool_gateway import execute_refund_through_gateway


def create_approval_request(
    refund_request_id: int,
) -> dict:
    """
    Create a human-approval request for a canonical RefundRequest.

    The RefundRequest is the single source of truth for all
    refund details. ApprovalRequest only stores the request ID
    and approval lifecycle status.
    """

    if refund_request_id <= 0:
        return {
            "success": False,
            "error": "Invalid refund request ID",
        }

    db = SessionLocal()

    try:
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

        if refund_request.status != "awaiting_approval":
            return {
                "success": False,
                "error": (
                    "Refund request is not awaiting human approval"
                ),
            }

        # Prevent multiple pending approvals for the same request.
        existing_approval = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.refund_request_id == refund_request_id,
                ApprovalRequest.status == "pending",
            )
            .first()
        )

        if existing_approval is not None:
            return {
                "success": True,
                "approval_id": existing_approval.id,
                "refund_request_id": existing_approval.refund_request_id,
                "customer_id": refund_request.customer_id,
                "order_id": refund_request.order_id,
                "amount": refund_request.requested_amount,
                "reason": refund_request.reason,
                "status": existing_approval.status,
                "idempotent": True,
            }

        approval = ApprovalRequest(
            refund_request_id=refund_request.id,
            status="pending",
        )

        db.add(approval)
        db.commit()
        db.refresh(approval)

        return {
            "success": True,
            "approval_id": approval.id,
            "refund_request_id": refund_request.id,
            "customer_id": refund_request.customer_id,
            "order_id": refund_request.order_id,
            "amount": refund_request.requested_amount,
            "reason": refund_request.reason,
            "status": approval.status,
            "idempotent": False,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_approval(
    approval_id: int,
    decision: str,
) -> dict:
    """
    Approve or reject a pending approval.

    Approval changes authorization state only.
    The refund amount is always resolved from RefundRequest.
    """

    if approval_id <= 0:
        return {
            "success": False,
            "error": "Invalid approval ID",
        }

    db = SessionLocal()

    try:
        approval = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.id == approval_id)
            .first()
        )

        if approval is None:
            return {
                "success": False,
                "error": "Approval request not found",
            }

        if approval.status != "pending":
            return {
                "success": False,
                "error": (
                    f"Approval request is already "
                    f"{approval.status}"
                ),
            }

        if decision not in ["approved", "rejected"]:
            return {
                "success": False,
                "error": "Decision must be approved or rejected",
            }

        refund_request = (
            db.query(RefundRequest)
            .filter(
                RefundRequest.id == approval.refund_request_id
            )
            .first()
        )

        if refund_request is None:
            return {
                "success": False,
                "error": "Refund request not found",
            }

        if refund_request.status != "awaiting_approval":
            return {
                "success": False,
                "error": (
                    "Refund request is not awaiting human approval"
                ),
            }

        # --------------------------------------------------
        # Human rejects the refund
        # --------------------------------------------------

        if decision == "rejected":

            refund_request.status = "rejected"
            approval.status = "rejected"

            db.commit()
            db.refresh(approval)

            return {
                "success": True,
                "approval_id": approval.id,
                "refund_request_id": approval.refund_request_id,
                "status": approval.status,
                "refund_status": refund_request.status,
            }

        # --------------------------------------------------
        # Human approves the refund
        # --------------------------------------------------

        # Authorize execution.
        refund_request.status = "approved"
        db.commit()

        refund_result = execute_refund_through_gateway(
            refund_request_id=approval.refund_request_id,
        )

        if not refund_result["success"]:

            # Restore the request so the pending approval can
            # be retried rather than leaving the workflow stuck.
            db.rollback()

            db = SessionLocal()

            try:
                refund_request = (
                    db.query(RefundRequest)
                    .filter(
                        RefundRequest.id
                        == approval.refund_request_id
                    )
                    .first()
                )

                approval = (
                    db.query(ApprovalRequest)
                    .filter(
                        ApprovalRequest.id == approval_id
                    )
                    .first()
                )

                if refund_request is not None:
                    refund_request.status = "awaiting_approval"

                if approval is not None:
                    approval.status = "pending"

                db.commit()

            finally:
                db.close()

            return {
                "success": False,
                "error": "Refund execution failed",
                "details": refund_result,
            }

        # Gateway/refund tool has successfully processed the
        # canonical request.
        db = SessionLocal()

        try:
            approval = (
                db.query(ApprovalRequest)
                .filter(ApprovalRequest.id == approval_id)
                .first()
            )

            refund_request = (
                db.query(RefundRequest)
                .filter(
                    RefundRequest.id
                    == approval.refund_request_id
                )
                .first()
            )

            if approval is None or refund_request is None:
                raise RuntimeError(
                    "Approval or refund request disappeared "
                    "during execution"
                )

            approval.status = "approved"

            db.commit()
            db.refresh(approval)

            return {
                "success": True,
                "approval_id": approval.id,
                "refund_request_id": approval.refund_request_id,
                "status": approval.status,
                "refund_status": refund_request.status,
                "refund": refund_result,
            }

        finally:
            db.close()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
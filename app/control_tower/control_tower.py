from app.policy.policy_engine import evaluate_refund
from app.risk_engine.risk_engine import calculate_risk

from app.tools.tool_gateway import execute_refund_through_gateway
from app.tools.approval_tool import create_approval_request

from app.database.database import engine, Base, SessionLocal
from app.database.models import AuditLog, RefundRequest


# Create any missing database tables, including audit_logs
Base.metadata.create_all(bind=engine)


def evaluate_refund_request(
    refund_request_id: int,
) -> dict:
    """
    Evaluate a refund request using the canonical RefundRequest.

    The refund amount, customer, order, and reason are loaded from
    the database. Callers cannot supply a different refund amount.
    """

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

        customer_id = refund_request.customer_id
        order_id = refund_request.order_id
        refund_amount = refund_request.requested_amount
        reason = refund_request.reason

        # --------------------------------------------------
        # 2. Load canonical order amount
        # --------------------------------------------------

        from app.database.models import Order

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

        order_amount = order.amount

    finally:
        db.close()

    # --------------------------------------------------
    # 3. Evaluate existing refund policy
    # --------------------------------------------------

    policy_result = evaluate_refund(
        refund_amount=refund_amount,
        order_amount=order_amount,
    )

    policy_decision = policy_result["decision"]

    # --------------------------------------------------
    # 4. Calculate refund risk
    # --------------------------------------------------

    risk_result = calculate_risk(
        refund_amount=refund_amount,
        order_amount=order_amount,
    )

    risk_level = risk_result["risk_level"]

    # --------------------------------------------------
    # 5. Determine final Control Tower decision
    # --------------------------------------------------

    decision = policy_decision

    # HIGH risk always blocks the refund
    if risk_level == "HIGH":
        decision = "BLOCK"

    # MEDIUM risk requires human approval
    elif risk_level == "MEDIUM":
        if policy_decision == "ALLOW":
            decision = "HUMAN_APPROVAL"

    result = {
        "refund_request_id": refund_request_id,
        "customer_id": customer_id,
        "order_id": order_id,
        "refund_amount": refund_amount,
        "order_amount": order_amount,
        "reason": reason,
        "decision": decision,
        "policy_decision": policy_decision,
        "policy_reason": policy_result["reason"],
        "risk": risk_result,
    }

    # --------------------------------------------------
    # 6. Execute / approve / block
    # --------------------------------------------------

    if decision == "ALLOW":

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

            if refund_request.status != "pending":
                return {
                    "success": False,
                    "error": (
                        f"Refund request is already "
                        f"{refund_request.status}"
                    ),
                }

            # Authorize execution.
            refund_request.status = "approved"
            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        execution_result = execute_refund_through_gateway(
            refund_request_id=refund_request_id,
        )

        if execution_result.get("success"):

            db = SessionLocal()

            try:
                refund_request = (
                    db.query(RefundRequest)
                    .filter(RefundRequest.id == refund_request_id)
                    .first()
                )

                if refund_request is not None:
                    refund_request.status = "processed"
                    db.commit()

            except Exception:
                db.rollback()
                raise

            finally:
                db.close()

        else:
            # Execution failed, so return the request to pending.
            db = SessionLocal()

            try:
                refund_request = (
                    db.query(RefundRequest)
                    .filter(RefundRequest.id == refund_request_id)
                    .first()
                )

                if refund_request is not None:
                    refund_request.status = "pending"
                    db.commit()

            except Exception:
                db.rollback()
                raise

            finally:
                db.close()

        result["execution"] = execution_result

    elif decision == "HUMAN_APPROVAL":

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

            if refund_request.status != "pending":
                return {
                    "success": False,
                    "error": (
                        f"Refund request is already "
                        f"{refund_request.status}"
                    ),
                }

            # Mark the request as waiting for human authorization.
            refund_request.status = "awaiting_approval"
            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        approval_result = create_approval_request(
            refund_request_id=refund_request_id,
        )

        if not approval_result.get("success"):

            # Approval creation failed, so restore the request.
            db = SessionLocal()

            try:
                refund_request = (
                    db.query(RefundRequest)
                    .filter(RefundRequest.id == refund_request_id)
                    .first()
                )

                if refund_request is not None:
                    refund_request.status = "pending"
                    db.commit()

            except Exception:
                db.rollback()
                raise

            finally:
                db.close()

        result["execution"] = {
            "executed": False,
            "status": "awaiting_human_approval",
        }

        result["approval"] = approval_result

    else:

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

            if refund_request.status != "pending":
                return {
                    "success": False,
                    "error": (
                        f"Refund request is already "
                        f"{refund_request.status}"
                    ),
                }

            # Permanently block this request.
            refund_request.status = "blocked"
            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        result["execution"] = {
            "executed": False,
            "status": "blocked",
        }

    # --------------------------------------------------
    # 7. Record decision in audit log
    # --------------------------------------------------

    db = SessionLocal()

    try:
        audit_log = AuditLog(
            customer_id=customer_id,
            order_id=order_id,
            refund_amount=refund_amount,
            decision=decision,
            reason=(
                f"Policy: {policy_result['reason']} | "
                f"Risk: {risk_result['risk_level']} "
                f"(score {risk_result['risk_score']})"
            ),
        )

        db.add(audit_log)
        db.commit()

    except Exception:
        db.rollback()

    finally:
        db.close()

    return result
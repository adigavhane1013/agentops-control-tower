from app.policy.policy_engine import evaluate_refund
from app.risk_engine.risk_engine import calculate_risk

from app.tools.tool_gateway import execute_refund_through_gateway
from app.tools.approval_tool import create_approval_request

from app.database.database import engine, Base, SessionLocal
from app.database.models import AuditLog


# Create any missing database tables, including audit_logs
Base.metadata.create_all(bind=engine)


def evaluate_refund_request(
    customer_id: int,
    order_id: int,
    refund_amount: float,
    order_amount: float,
    reason: str
) -> dict:
    """
    Evaluate a refund request using both policy and risk controls.
    """

    # --------------------------------------------------
    # 1. Evaluate existing refund policy
    # --------------------------------------------------

    policy_result = evaluate_refund(
        refund_amount=refund_amount,
        order_amount=order_amount
    )

    policy_decision = policy_result["decision"]

    # --------------------------------------------------
    # 2. Calculate refund risk
    # --------------------------------------------------

    risk_result = calculate_risk(
        refund_amount=refund_amount,
        order_amount=order_amount
    )

    risk_level = risk_result["risk_level"]

    # --------------------------------------------------
    # 3. Determine final Control Tower decision
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
        "customer_id": customer_id,
        "order_id": order_id,
        "refund_amount": refund_amount,
        "order_amount": order_amount,
        "reason": reason,
        "decision": decision,
        "policy_decision": policy_decision,
        "policy_reason": policy_result["reason"],
        "risk": risk_result
    }

    # --------------------------------------------------
    # 4. Execute / approve / block
    # --------------------------------------------------

    if decision == "ALLOW":

        execution_result = execute_refund_through_gateway(
            customer_id=customer_id,
            order_id=order_id,
            amount=refund_amount,
            reason=reason
        )

        result["execution"] = execution_result

    elif decision == "HUMAN_APPROVAL":

        approval_result = create_approval_request(
            customer_id=customer_id,
            order_id=order_id,
            amount=refund_amount,
            reason=reason
        )

        result["execution"] = {
            "executed": False,
            "status": "awaiting_human_approval"
        }

        result["approval"] = approval_result

    else:

        result["execution"] = {
            "executed": False,
            "status": "blocked"
        }

    # --------------------------------------------------
    # 5. Record decision in audit log
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
            )
        )

        db.add(audit_log)
        db.commit()

    except Exception:
        db.rollback()

    finally:
        db.close()

    return result
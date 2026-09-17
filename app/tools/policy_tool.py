from app.policy.policy_engine import evaluate_refund


def check_refund_policy(
    refund_amount: float,
    order_amount: float
) -> dict:
    """Check a refund request against the deterministic refund policy."""

    result = evaluate_refund(
        refund_amount=refund_amount,
        order_amount=order_amount
    )

    return {
        "decision": result["decision"],
        "reason": result["reason"]
    }
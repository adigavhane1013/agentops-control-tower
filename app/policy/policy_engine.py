def evaluate_refund(refund_amount: float, order_amount: float) -> dict:
    """
    Deterministic refund policy engine.

    Returns:
        ALLOW
        HUMAN_APPROVAL
        BLOCK
    """

    if refund_amount > order_amount:
        return {
            "decision": "BLOCK",
            "reason": "Refund amount exceeds order amount"
        }

    if refund_amount > 20000:
        return {
            "decision": "BLOCK",
            "reason": "Refund amount exceeds ₹20,000 limit"
        }

    if refund_amount > 5000:
        return {
            "decision": "HUMAN_APPROVAL",
            "reason": "Refund requires human approval"
        }

    return {
        "decision": "ALLOW",
        "reason": "Refund meets automatic approval policy"
    }
from app.tools.refund_tool import execute_refund


def execute_refund_through_gateway(
    customer_id: int,
    order_id: int,
    amount: float,
    reason: str
) -> dict:
    """
    Central gateway for refund execution.
    """

    if amount <= 0:
        raise ValueError("Refund amount must be greater than zero")

    if customer_id <= 0:
        raise ValueError("Invalid customer ID")

    if order_id <= 0:
        raise ValueError("Invalid order ID")

    return execute_refund(
        customer_id=customer_id,
        order_id=order_id,
        amount=amount,
        reason=reason
    )
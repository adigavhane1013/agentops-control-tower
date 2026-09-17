import pytest

from app.tools.tool_gateway import execute_refund_through_gateway


def test_invalid_order_id():
    with pytest.raises(ValueError, match="Invalid order ID"):
        execute_refund_through_gateway(
            customer_id=102,
            order_id=0,
            amount=5000,
            reason="Invalid order test"
        )

def test_invalid_amount():
    with pytest.raises(ValueError, match="Refund amount must be greater than zero"):
        execute_refund_through_gateway(
            customer_id=102,
            order_id=1002,
            amount=0,
            reason="Invalid amount test"
        )


def test_invalid_customer_id():
    with pytest.raises(ValueError, match="Invalid customer ID"):
        execute_refund_through_gateway(
            customer_id=0,
            order_id=1002,
            amount=5000,
            reason="Invalid customer test"
        )
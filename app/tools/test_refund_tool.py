from app.tools.refund_tool import execute_refund


def test_execute_refund():
    result = execute_refund(
        customer_id=101,
        order_id=1001,
        amount=5000,
        reason="Wrong product"
    )

    assert result["success"] is True
    assert result["customer_id"] == 101
    assert result["order_id"] == 1001
    assert result["amount"] == 5000
    assert result["status"] == "processed"
    assert result["reason"] == "Wrong product"
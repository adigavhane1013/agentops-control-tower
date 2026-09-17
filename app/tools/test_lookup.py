from app.tools.lookup_tool import get_customer_order


def test_get_customer_order():
    result = get_customer_order(101)

    assert result["success"] is True
    assert result["customer"]["id"] == 101
    assert result["order"]["id"] == 1001
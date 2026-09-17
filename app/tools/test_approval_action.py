from app.tools.approval_tool import create_approval_request
from app.tools.approval_action import update_approval


def test_approve_refund():
    approval = create_approval_request(
        customer_id=101,
        order_id=1001,
        amount=1000,
        reason="Automated approval test"
    )

    assert approval["success"] is True

    approval_id = approval["approval_id"]

    result = update_approval(
        approval_id=approval_id,
        decision="approved"
    )

    assert result["success"] is True
    assert result["status"] == "approved"
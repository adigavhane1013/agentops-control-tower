from app.tools.policy_tool import check_refund_policy


def test_policy_allows_refund():
    result = check_refund_policy(
        refund_amount=4000,
        order_amount=5000
    )

    assert result["decision"] == "ALLOW"


def test_policy_requires_human_approval():
    result = check_refund_policy(
        refund_amount=10000,
        order_amount=15000
    )

    assert result["decision"] == "HUMAN_APPROVAL"


def test_policy_blocks_excess_refund():
    result = check_refund_policy(
        refund_amount=6000,
        order_amount=5000
    )

    assert result["decision"] == "BLOCK"
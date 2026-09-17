from app.policy.policy_engine import evaluate_refund


def test_policy_allows_refund():
    result = evaluate_refund(4000, 5000)

    assert result["decision"] == "ALLOW"
    assert result["reason"] == "Refund meets automatic approval policy"


def test_policy_requires_human_approval():
    result = evaluate_refund(10000, 15000)

    assert result["decision"] == "HUMAN_APPROVAL"
    assert result["reason"] == "Refund requires human approval"


def test_policy_blocks_high_refund():
    result = evaluate_refund(25000, 30000)

    assert result["decision"] == "BLOCK"
    assert result["reason"] == "Refund amount exceeds ₹20,000 limit"


def test_policy_blocks_refund_above_order():
    result = evaluate_refund(6000, 5000)

    assert result["decision"] == "BLOCK"
    assert result["reason"] == "Refund amount exceeds order amount"
def calculate_risk(
    refund_amount: float,
    order_amount: float
) -> dict:

    risk_score = 0
    risk_factors = []

    if refund_amount > 15000:
        risk_score += 40
        risk_factors.append("High refund amount")

    if refund_amount >= order_amount * 0.5:
        risk_score += 30
        risk_factors.append("Refund is 50% or more of order value")

    if refund_amount > 20000:
        risk_score += 30
        risk_factors.append("Refund exceeds ₹20,000")

    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors
    }
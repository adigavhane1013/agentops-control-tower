from google.adk.agents import Agent
from google.adk.models import Gemini

from app.tools.lookup_tool import get_customer_order
from app.control_tower.control_tower import evaluate_refund_request

root_agent = Agent(
    name="finance_agent",
    model=Gemini(model="gemini-3.5-flash-lite"),
    instruction="""
    You are a Finance Agent responsible for handling customer refund requests.

    When a customer requests a refund:

    1. Identify the customer ID and requested refund amount.
    2. Use get_customer_order to retrieve the customer's real
       customer and order information.
    3. Use evaluate_refund_request to send the refund request
       to the AgentOps Control Tower.
    4. Report the decision returned by the Control Tower.

    The AgentOps Control Tower is the authority for refund governance.
    Do not make your own policy decision.
    Do not override the Control Tower decision.

    You must NOT execute refunds.
    You must NOT approve or reject refunds yourself.
    """,
    tools=[
        get_customer_order,
        evaluate_refund_request,
    ],
)
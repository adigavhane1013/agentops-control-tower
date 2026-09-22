from sqlalchemy import Column, Integer, String, Float, ForeignKey, event, inspect
from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    status = Column(String, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)


class RefundRequest(Base):
    __tablename__ = "refund_requests"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    requested_amount = Column(Float, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, nullable=False)


@event.listens_for(RefundRequest, "before_update")
def prevent_refund_request_mutation(mapper, connection, target):
    """
    Prevent modification of the original refund request data.

    Only the request lifecycle status may change after creation.
    """

    state = inspect(target)

    immutable_fields = (
        "customer_id",
        "order_id",
        "requested_amount",
        "reason",
    )

    for field in immutable_fields:
        if state.attrs[field].history.has_changes():
            raise ValueError(
                f"RefundRequest field '{field}' is immutable"
            )


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    refund_request_id = Column(
        Integer,
        ForeignKey("refund_requests.id"),
        nullable=True,
    )
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    
class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True)
    refund_request_id = Column(
        Integer,
        ForeignKey("refund_requests.id"),
        nullable=False,
    )
    status = Column(String, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    refund_amount = Column(Float, nullable=False)
    decision = Column(String, nullable=False)
    reason = Column(String, nullable=True)
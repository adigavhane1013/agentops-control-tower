import importlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


_test_engine = None


def _configure_test_database():
    global _test_engine

    # Use one shared in-memory SQLite database for the entire pytest session.
    # StaticPool keeps the same connection available to all tests.
    _test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_test_engine,
    )

    database_module = importlib.import_module("app.database.database")
    models_module = importlib.import_module("app.database.models")

    Base = database_module.Base
    Customer = models_module.Customer
    Order = models_module.Order

    # Create the schema in the isolated in-memory test database.
    Base.metadata.create_all(bind=_test_engine)

    # Seed the same baseline data used by the real application.
    db = TestSessionLocal()

    try:
        db.add_all(
            [
                Customer(
                    id=101,
                    name="Rahul Sharma",
                    email="rahul@example.com",
                    status="active",
                ),
                Customer(
                    id=102,
                    name="Priya Patel",
                    email="priya@example.com",
                    status="active",
                ),
                Customer(
                    id=103,
                    name="Amit Kumar",
                    email="amit@example.com",
                    status="active",
                ),
                Order(
                    id=1001,
                    customer_id=101,
                    amount=5000,
                    status="delivered",
                ),
                Order(
                    id=1002,
                    customer_id=102,
                    amount=25000,
                    status="delivered",
                ),
                Order(
                    id=1003,
                    customer_id=103,
                    amount=3000,
                    status="delivered",
                ),
            ]
        )

        db.commit()

    finally:
        db.close()

    # Replace the application's database session/engine before
    # importing test modules that depend on them.
    database_module.SessionLocal = TestSessionLocal
    database_module.engine = _test_engine

    modules_to_patch = [
        "app.tools.refund_tool",
        "app.tools.tool_gateway",
        "app.tools.refund_request_tool",
        "app.tools.approval_tool",
        "app.tools.approval_action",
        "app.control_tower.control_tower",
        "app.database.test_database",
    ]

    for module_name in modules_to_patch:
        module = importlib.import_module(module_name)

        if hasattr(module, "SessionLocal"):
            module.SessionLocal = TestSessionLocal

        if hasattr(module, "engine"):
            module.engine = _test_engine


def pytest_configure(config):
    """
    Configure the isolated in-memory test database before pytest
    collects the test modules.
    """
    _configure_test_database()


def pytest_sessionfinish(session, exitstatus):
    """
    Dispose the in-memory test database after the pytest session.
    """
    global _test_engine

    if _test_engine is not None:
        _test_engine.dispose()
        _test_engine = None
import importlib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


_test_temp_dir = None
_test_engine = None


def _configure_test_database():
    global _test_temp_dir
    global _test_engine

    # Create a temporary directory that exists for the pytest session.
    _test_temp_dir = TemporaryDirectory(prefix="agentops_pytest_")

    test_db_path = Path(_test_temp_dir.name) / "test_agentops.db"

    _test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
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

    # Create the schema in the isolated test database.
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

    # Replace SessionLocal in the application modules before pytest
    # imports the test modules that use them.
    database_module.SessionLocal = TestSessionLocal
    database_module.engine = _test_engine

    modules_to_patch = [
        "app.tools.refund_tool",
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
    Configure the isolated test database before test collection.
    """
    _configure_test_database()


def pytest_sessionfinish(session, exitstatus):
    """
    Remove the temporary test database after pytest finishes.
    """
    global _test_temp_dir
    global _test_engine

    if _test_engine is not None:
        _test_engine.dispose()
        _test_engine = None

    if _test_temp_dir is not None:
        _test_temp_dir.cleanup()
        _test_temp_dir = None
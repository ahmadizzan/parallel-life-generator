from unittest.mock import patch

import pytest
from sqlmodel import create_engine

from plg.models.db import get_session as original_get_session, init_database_if_needed
from plg.models.models import SQLModel


@pytest.fixture(scope="function")
def setup_test_db():
    """
    Fixture to set up and tear down an in-memory SQLite database for tests.
    It also patches the get_session function to use the test database.
    """
    # In a real CI environment, the home directory might not exist.
    # This ensures the .plg directory is created.
    init_database_if_needed()

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with original_get_session(engine) as session:
            yield session

    # Patch get_session in all the places it's used by the CLI commands
    with patch("plg.cli.get_session", new=get_test_session), patch(
        "plg.models.db.get_session", new=get_test_session
    ), patch("plg.tools.tree.get_session", new=get_test_session):
        yield

    SQLModel.metadata.drop_all(engine)

from sqlmodel import Session, select

from plg.models.db import get_session


def test_get_session_context_works():
    """
    Verify that the get_session context manager yields a valid and
    usable session.
    """
    with get_session() as session:
        # Assert that we have a valid session inside the context
        assert isinstance(session, Session)

        # Assert that the session is active by executing a simple query
        result = session.exec(select(1)).one()
        assert result == 1

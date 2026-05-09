import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Adjust sys.path so we can import modules from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def mock_db():
    """
    Auto-mock database functions globally for tests to prevent
    the background `poll_loop` or endpoint handlers from attempting
    to connect to a live postgres database during tests.
    """
    with patch("main.fetch_recent_incidents") as mock_fetch, \
         patch("main.fetch_incident_by_id") as mock_by_id, \
         patch("main.fetch_stats") as mock_stats:
        
        mock_fetch.return_value = []
        mock_by_id.return_value = None
        mock_stats.return_value = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
        
        yield {"fetch": mock_fetch, "by_id": mock_by_id, "stats": mock_stats}

@pytest.fixture
def client(mock_db):
    """
    Spin up the TestClient. This also runs the FastAPI lifespan events,
    which starts the asyncio `poll_loop()`. Since `mock_db` is auto-used,
    it intercepts `fetch_recent_incidents` perfectly before lifespan starts!
    """
    from main import app
    with TestClient(app) as c:
        yield c

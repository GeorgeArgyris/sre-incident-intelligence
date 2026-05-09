import sys
import os
import json
import pytest
from unittest.mock import patch

os.environ["GROQ_API_KEY"] = "fake-test-key"
os.environ["CONFLUENT_BOOTSTRAP_SERVERS"] = "fake-broker"
os.environ["CONFLUENT_API_KEY"] = "fake-key"
os.environ["CONFLUENT_API_SECRET"] = "fake-secret"
os.environ["DATABASE_URL"] = "postgresql://fake"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Completely mock confluent_kafka globally so worker.py global assignments don't trigger real network I/O
from unittest.mock import MagicMock
sys.modules['confluent_kafka'] = MagicMock()

# Import targeted function explicitly
from worker import send_to_dlq

@patch("worker.dlq_producer.produce")
@patch("worker.dlq_producer.poll")
def test_send_to_dlq(mock_poll, mock_produce):
    send_to_dlq("faulty_str_payload", "Groq timeout exception")
    
    # Ensure produced topics accurately isolate to dead-letter-queue securely 
    mock_produce.assert_called_once_with(
        topic="dead-letter-queue",
        value=json.dumps({"raw": "faulty_str_payload", "reason": "Groq timeout exception"}),
    )
    mock_poll.assert_called_once_with(0)

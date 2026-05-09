import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

# Set required environment variables before imports so top-level clients don't crash
os.environ["GROQ_API_KEY"] = "fake-test-key"

# Inject parent directory to path strictly for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enricher import enrich_incident
from models import EnrichedIncident

@patch("enricher.client.chat.completions.create")
def test_enrich_incident_severity_mapping(mock_create):
    # Setup mock LLM response payload safely bypassing physical groq keys
    fake_llm_response = {
        "incident_id": "test-1",
        "service": "billing",
        "severity": "CRITICAL",  # should be translated implicitly
        "error_type": "ConnectionTimeout",
        "root_cause": "The billing database query timed out.",
        "recommended_actions": ["Restart DB", "Check indices"],
        "estimated_impact": "High failure rate for checkouts",
        "resolution_time_minutes": 15
    }
    
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(fake_llm_response)
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_create.return_value = mock_response

    # Feed it a "p1" payload exactly simulating what's seen natively
    raw_incident = {
        "incident_id": "test-1",
        "service": "billing",
        "severity": "p1",
        "error_type": "ConnectionTimeout"
    }
    
    result = enrich_incident(raw_incident)
    
    assert isinstance(result, EnrichedIncident)
    assert result.severity == "CRITICAL"
    assert result.root_cause == "The billing database query timed out."
    assert "Check indices" in result.recommended_actions
    
    # Assert LLM parameters
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]
    assert call_args["model"] == "llama-3.1-8b-instant"
    assert raw_incident["incident_id"] in call_args["messages"][0]["content"]

@patch("enricher.client.chat.completions.create")
def test_enrich_incident_json_parse_error(mock_create):
    # Setup hallucinated malformed LLM response breaking json rules natively
    mock_choice = MagicMock()
    mock_choice.message.content = "This is definitely not valid json"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_create.return_value = mock_response

    raw_incident = {
        "incident_id": "test-2",
        "service": "auth",
        "severity": "p4",
        "error_type": "MinorWarning"
    }

    # Ensuring it aggressively fails upstream so it catches DLQ block correctly
    with pytest.raises(json.JSONDecodeError):
        enrich_incident(raw_incident)

import sys
import os

# Inject parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from incident_factory import generate_incident

def test_generate_incident_schema():
    """
    Verifies that the synthetic Faker producer reliably generates
    payloads matching the strict fields expected downstream by the worker module.
    """
    incident = generate_incident()
    
    assert isinstance(incident, dict)
    
    expected_keys = ["incident_id", "service", "severity", "error_type"]
    for key in expected_keys:
        assert key in incident, f"Missing {key} in generated incident payload"
        
    assert isinstance(incident["incident_id"], str)
    assert len(incident["incident_id"]) > 0
    assert incident["severity"] in ["P1", "P2", "P3", "P4"]

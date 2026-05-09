import json

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "ts" in response.json()

def test_list_incidents_empty(client, mock_db):
    mock_db["fetch"].return_value = []
    response = client.get("/incidents")
    assert response.status_code == 200
    data = response.json()
    assert data["incidents"] == []

def test_list_incidents_with_data_and_pagination(client, mock_db):
    # Mock some data and test parameter passing
    mock_db["fetch"].return_value = [
        {"incident_id": "i-123", "service": "web-backend", "severity": "CRITICAL"}
    ]
    response = client.get("/incidents?limit=5&offset=10&severity=CRITICAL")
    assert response.status_code == 200
    
    # Check that our mock backend was called with the exact parameters given in the URL!
    mock_db["fetch"].assert_called_with(limit=5, offset=10, severity="CRITICAL")
    
    data = response.json()
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["incident_id"] == "i-123"

def test_get_incident_not_found(client, mock_db):
    mock_db["by_id"].return_value = None
    response = client.get("/incidents/nonexistent_id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"

def test_get_incident_success(client, mock_db):
    mock_db["by_id"].return_value = {"incident_id": "i-999", "service": "database"}
    response = client.get("/incidents/i-999")
    assert response.status_code == 200
    assert response.json()["incident_id"] == "i-999"

def test_get_stats(client, mock_db):
    mock_db["stats"].return_value = {"total": 50, "critical": 12, "high": 5, "medium": 0, "low": 0}
    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json()["critical"] == 12

def test_websocket_incidents_connection(client, mock_db):
    # Mock initial data pushed upon WEBSOCKET CONNECT
    mock_db["fetch"].return_value = [
        {"incident_id": "ws-1", "service": "cache", "severity": "HIGH"}
    ]
    
    with client.websocket_connect("/ws/incidents") as websocket:
        # Client receives history immediately
        data = websocket.receive_json()
        assert data["incident_id"] == "ws-1"
        assert data["severity"] == "HIGH"

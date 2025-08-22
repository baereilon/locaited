"""Test API endpoints for result display functionality."""

import pytest
from fastapi.testclient import TestClient
from locaited.api import app

client = TestClient(app)


def test_discover_test_endpoint_returns_mock_data():
    """Test that the mock endpoint returns properly structured data quickly."""
    # Prepare request data
    request_data = {
        "query": "fashion events",
        "location": "NYC",
        "interest_areas": ["fashion", "technology"],
        "days_ahead": 7,
        "use_cache": True
    }
    
    # Make request
    response = client.post("/workflow/discover-test", json=request_data)
    
    # Check response status
    assert response.status_code == 200
    
    # Parse response
    data = response.json()
    
    # Check response structure
    assert "events" in data
    assert "total_cost" in data
    assert "cache_hits" in data
    assert "status" in data
    assert "message" in data
    
    # Check status is success
    assert data["status"] == "success"
    
    # Check events are returned
    assert len(data["events"]) > 0
    
    # Check event structure
    for event in data["events"]:
        assert "title" in event
        assert "location" in event
        assert "time" in event
        assert "url" in event
        assert "access_req" in event
        assert "summary" in event
        assert "score" in event
        assert "rationale" in event
        
        # Check score is valid
        assert 0 <= event["score"] <= 100


def test_discover_test_endpoint_returns_quickly():
    """Test that the mock endpoint returns within reasonable time."""
    import time
    
    request_data = {
        "query": "test query",
        "location": "NYC",
        "interest_areas": ["test"],
        "days_ahead": 7,
        "use_cache": True
    }
    
    start_time = time.time()
    response = client.post("/workflow/discover-test", json=request_data)
    end_time = time.time()
    
    # Should return in less than 1 second
    assert (end_time - start_time) < 1.0
    assert response.status_code == 200


def test_discover_test_endpoint_handles_empty_interests():
    """Test that the endpoint handles empty interest areas."""
    request_data = {
        "query": "events",
        "location": "NYC",
        "interest_areas": [],
        "days_ahead": 14,
        "use_cache": False
    }
    
    response = client.post("/workflow/discover-test", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert len(data["events"]) > 0


def test_workflow_response_model_validation():
    """Test that the response matches the WorkflowResponse model."""
    request_data = {
        "query": "test",
        "location": "NYC",
        "interest_areas": ["test"],
        "days_ahead": 7,
        "use_cache": True
    }
    
    response = client.post("/workflow/discover-test", json=request_data)
    data = response.json()
    
    # Validate all required fields are present and correct type
    assert isinstance(data["events"], list)
    assert isinstance(data["total_cost"], (int, float))
    assert isinstance(data["cache_hits"], int)
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)
    
    # Validate events have correct structure
    if data["events"]:
        event = data["events"][0]
        assert isinstance(event["title"], str)
        assert isinstance(event["location"], str)
        assert event["time"] is None or isinstance(event["time"], str)
        assert isinstance(event["url"], str)
        assert isinstance(event["access_req"], str)
        assert isinstance(event["summary"], str)
        assert isinstance(event["score"], (int, float))
        assert event["rationale"] is None or isinstance(event["rationale"], str)
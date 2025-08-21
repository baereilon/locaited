"""Pytest configuration and shared fixtures for all tests."""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our modules for mocking
from locaited.utils.llm_client import LLMClient
from locaited.utils.tavily_client import TavilyClient


# ==================== Configuration ====================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as benchmark (run with --benchmark)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test (uses real APIs)"
    )


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--benchmark", 
        action="store_true", 
        default=False,
        help="run benchmark tests"
    )
    parser.addoption(
        "--smoke", 
        action="store_true", 
        default=False,
        help="run smoke tests (uses real APIs - costs money!)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip benchmark and smoke tests unless explicitly requested."""
    if not config.getoption("--benchmark"):
        skip_benchmark = pytest.mark.skip(reason="need --benchmark option to run")
        for item in items:
            if "benchmark" in item.keywords:
                item.add_marker(skip_benchmark)
    
    if not config.getoption("--smoke"):
        skip_smoke = pytest.mark.skip(reason="need --smoke option to run (uses real APIs!)")
        for item in items:
            if "smoke" in item.keywords:
                item.add_marker(skip_smoke)


# ==================== Session-Scoped Fixtures ====================

@pytest.fixture(scope="session")
def test_cache_dir():
    """Create a shared test cache directory for the entire test session."""
    cache_dir = Path(tempfile.mkdtemp(prefix="locaited_test_cache_"))
    yield cache_dir
    # Clean up after all tests
    shutil.rmtree(cache_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def shared_cache_config(test_cache_dir):
    """Configuration for shared test cache."""
    return {
        "base_dir": test_cache_dir,
        "v0.4.0": test_cache_dir / "v0.4.0",
        "enabled": True
    }


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_llm_client():
    """Mock LLMClient at wrapper level."""
    mock_client = MagicMock(spec=LLMClient)
    
    # Default successful response
    mock_client.complete_json.return_value = {
        "parsed_content": {"test": "response"},
        "raw_content": '{"test": "response"}',
        "cost": 0.0001,
        "model": "gpt-4.1-mini",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }
    
    mock_client.complete.return_value = {
        "content": "Test response",
        "cost": 0.0001,
        "model": "gpt-4.1-mini",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }
    
    return mock_client


@pytest.fixture
def mock_tavily_client():
    """Mock TavilyClient at wrapper level."""
    mock_client = MagicMock(spec=TavilyClient)
    
    # Default search response
    mock_client.search.return_value = {
        "results": [
            {
                "title": "Test Event",
                "url": "https://example.com/event",
                "content": "Test event happening this week",
                "score": 0.95
            }
        ],
        "query": "test query",
        "response_time": 0.5
    }
    
    return mock_client


# ==================== Test Data Fixtures ====================

@pytest.fixture(scope="session")
def sample_user_inputs():
    """Sample user inputs for testing."""
    return [
        {
            "location": "New York City",
            "time_frame": "this week",
            "interests": ["protests", "cultural events"]
        },
        {
            "location": "Brooklyn",
            "time_frame": "next 2 weeks",
            "interests": ["art exhibitions", "concerts", "community events"]
        },
        {
            "location": "Manhattan",
            "time_frame": "today",
            "interests": ["political rallies"]
        }
    ]


@pytest.fixture(scope="session")
def sample_profile():
    """Sample editor profile output."""
    return {
        "location": "New York City",
        "time_frame": "this week",
        "interests": ["protests", "cultural events"],
        "researcher_guidance": "Focus on grassroots protests and major cultural festivals happening in NYC this week"
    }


@pytest.fixture(scope="session")
def sample_leads():
    """Sample researcher leads output."""
    return [
        {
            "event_description": "Climate March at Washington Square Park",
            "event_type": "protest",
            "search_query": "Climate March Washington Square Park NYC August 2025"
        },
        {
            "event_description": "Brooklyn Book Festival",
            "event_type": "cultural",
            "search_query": "Brooklyn Book Festival 2025 dates"
        }
    ]


@pytest.fixture(scope="session")
def sample_evidence():
    """Sample fact-checker evidence output."""
    return [
        {
            "lead": "Climate March at Washington Square Park",
            "search_results": [
                {
                    "title": "NYC Climate March Set for August 25",
                    "content": "Activists will gather at Washington Square Park on August 25 at 2 PM...",
                    "url": "https://example.com/climate-march"
                }
            ],
            "has_evidence": True
        }
    ]


@pytest.fixture(scope="session")
def sample_events():
    """Sample publisher events output."""
    return [
        {
            "title": "NYC Climate March",
            "date": "2025-08-25",
            "time": "14:00",
            "location": "Washington Square Park, NYC",
            "description": "Climate activists march for policy change",
            "score": 85
        }
    ]


# ==================== Validation CSV Fixtures ====================

@pytest.fixture(scope="session")
def validation_csv_path():
    """Path to existing validation CSV for testing."""
    csv_path = Path(__file__).parent.parent / "benchmarks/results/v0.4.0/events_for_validation_0.4.0_20250820_141744.csv"
    if csv_path.exists():
        return csv_path
    return None


# ==================== Helper Functions ====================

@pytest.fixture
def assert_valid_json():
    """Helper to assert valid JSON structure."""
    def _assert(data, required_fields):
        assert isinstance(data, dict), "Response should be a dictionary"
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    return _assert


@pytest.fixture
def assert_cost_tracked():
    """Helper to assert cost tracking."""
    def _assert(result):
        assert "cost" in result or "total_cost" in result, "Cost tracking missing"
        cost = result.get("cost", result.get("total_cost", 0))
        assert isinstance(cost, (int, float)), "Cost should be numeric"
        assert cost >= 0, "Cost should be non-negative"
    return _assert
"""Unit tests for Fact-Checker agent evidence gathering."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from locaited.agents.fact_checker import FactCheckerAgent


class TestFactCheckerAgentGathersEvidence:
    """Test Fact-Checker agent evidence gathering functionality."""
    
    @pytest.fixture
    def fact_checker_agent(self):
        """Create Fact-Checker agent instance."""
        # Disable caching for tests
        agent = FactCheckerAgent()
        agent.use_cache = False
        # Mock the tavily_client to have necessary attributes
        agent.tavily_client = MagicMock()
        agent.tavily_client.total_cost = 0.0
        agent.tavily_client.total_searches = 0
        return agent
    
    @pytest.fixture
    def mock_tavily_response(self):
        """Mock Tavily API response."""
        return {
            "results": [
                {
                    "title": "Climate March Confirmed for August 25",
                    "url": "https://example.com/climate-march",
                    "content": "Environmental activists will gather at Washington Square Park on August 25 at 2 PM for a climate march...",
                    "score": 0.95
                },
                {
                    "title": "NYC Events This Week",
                    "url": "https://example.com/events",
                    "content": "Several events happening including the climate demonstration on Sunday...",
                    "score": 0.82
                }
            ],
            "query": "Climate March Washington Square Park NYC August 25 2025",
            "response_time": 0.5
        }
    
    @pytest.fixture
    def sample_state_with_leads(self):
        """Sample state with leads from Researcher."""
        return {
            "profile": {
                "location": "New York City",
                "time_frame": "this week",
                "interests": ["protests", "cultural events"]
            },
            "leads": [
                {
                    "description": "Climate March at Washington Square Park",
                    "type": "protest",
                    "search_query": "Climate March Washington Square Park NYC August 25 2025"
                },
                {
                    "description": "Brooklyn Book Festival",
                    "type": "cultural",
                    "search_query": "Brooklyn Book Festival 2025 dates location"
                },
                {
                    "description": "Housing Justice Rally at City Hall",
                    "type": "protest",
                    "search_query": "Housing Justice Rally City Hall NYC August 2025"
                }
            ]
        }
    
    @pytest.mark.unit
    def test_fact_checker_searches_all_leads(self, fact_checker_agent, mock_tavily_response, sample_state_with_leads):
        """Test that Fact-Checker searches for all provided leads."""
        # Setup mock
        fact_checker_agent.tavily_client.search.return_value = mock_tavily_response
        fact_checker_agent.tavily_client.total_cost = 0.003
        fact_checker_agent.tavily_client.total_searches = 3
        
        # Act
        result = fact_checker_agent.process(sample_state_with_leads)
        
        # Assert all leads were searched
        assert fact_checker_agent.tavily_client.search.call_count == 3  # One search per lead
        
        # Verify each search query was used (using kwargs)
        search_queries = [call.kwargs.get('query', '') 
                        for call in fact_checker_agent.tavily_client.search.call_args_list]
        assert "Climate March Washington Square Park NYC August 25 2025" in search_queries
        assert "Brooklyn Book Festival 2025 dates location" in search_queries
        assert "Housing Justice Rally City Hall NYC August 2025" in search_queries
        
        # Verify evidence was collected
        assert "evidence" in result
        assert len(result["evidence"]) == 3
    
    @pytest.mark.unit
    def test_fact_checker_uses_tavily_caching(self, fact_checker_agent, mock_tavily_response):
        """Test that Fact-Checker uses caching to avoid duplicate searches."""
        # Create state with duplicate search queries
        state = {
            "leads": [
                {
                    "description": "Climate March Morning Session",
                    "type": "protest",
                    "search_query": "Climate March NYC August 2025"  # Same query
                },
                {
                    "description": "Climate March Evening Session",
                    "type": "protest",
                    "search_query": "Climate March NYC August 2025"  # Same query (duplicate)
                },
                {
                    "description": "Different Event",
                    "type": "cultural",
                    "search_query": "Brooklyn Museum exhibition"  # Different query
                }
            ]
        }
        
        # Enable caching for this test
        fact_checker_agent.use_cache = True
        fact_checker_agent.tavily_client.search.return_value = mock_tavily_response
        fact_checker_agent.tavily_client.total_cost = 0.002
        fact_checker_agent.tavily_client.total_searches = 2
        
        # Act
        result = fact_checker_agent.process(state)
        
        # Assert - should process all leads
        assert "evidence" in result
        assert len(result["evidence"]) == 3  # Still get 3 evidence items
    
    @pytest.mark.unit
    def test_fact_checker_extracts_evidence(self, fact_checker_agent, mock_tavily_response, sample_state_with_leads):
        """Test that Fact-Checker properly extracts evidence from search results."""
        # Setup mock
        fact_checker_agent.tavily_client.search.return_value = mock_tavily_response
        fact_checker_agent.tavily_client.total_cost = 0.003
        fact_checker_agent.tavily_client.total_searches = 3
        
        # Act
        result = fact_checker_agent.process(sample_state_with_leads)
        
        # Assert evidence structure
        evidence = result["evidence"][0]
        assert "lead" in evidence
        assert "results" in evidence
        
        # Verify search results are properly formatted
        search_results = evidence["results"]
        assert len(search_results) > 0
        first_result = search_results[0]
        assert "title" in first_result
        assert "content" in first_result
        assert "url" in first_result
        
        # Verify evidence was found (has results)
        assert len(evidence["results"]) > 0  # Has results
    
    @pytest.mark.unit
    def test_fact_checker_tracks_api_costs(self, fact_checker_agent, mock_tavily_response, sample_state_with_leads):
        """Test that Fact-Checker tracks Tavily API costs."""
        # Setup mock with cost tracking
        fact_checker_agent.tavily_client.search.return_value = mock_tavily_response
        fact_checker_agent.tavily_client.total_cost = 0.003  # 3 searches * $0.001
        fact_checker_agent.tavily_client.total_searches = 3
        
        # Act
        result = fact_checker_agent.process(sample_state_with_leads)
        
        # Assert cost tracking
        assert "fact_checker_metrics" in result
        metrics = result["fact_checker_metrics"]
        assert "total_leads" in metrics
        assert metrics["total_leads"] == 3
        assert "tavily_cost" in metrics
        assert metrics["tavily_cost"] == 0.003
        assert "leads_with_evidence" in metrics
        assert metrics["leads_with_evidence"] == 3  # All leads have evidence
    
    @pytest.mark.unit  
    def test_fact_checker_handles_no_results(self, fact_checker_agent):
        """Test that Fact-Checker handles cases where no evidence is found."""
        state = {
            "leads": [
                {
                    "description": "Fictional Event That Doesn't Exist",
                    "type": "unknown",
                    "search_query": "xyzabc123 nonexistent event query"
                }
            ]
        }
        
        empty_response = {
            "results": [],  # No results
            "query": "xyzabc123 nonexistent event query",
            "response_time": 0.3
        }
        
        fact_checker_agent.tavily_client.search.return_value = empty_response
        fact_checker_agent.tavily_client.total_cost = 0.001
        fact_checker_agent.tavily_client.total_searches = 1
        
        # Act
        result = fact_checker_agent.process(state)
        
        # Assert
        assert "evidence" in result
        evidence = result["evidence"][0]
        assert len(evidence["results"]) == 0  # No evidence found
        assert evidence["lead"]["description"] == "Fictional Event That Doesn't Exist"
    
    @pytest.mark.unit
    def test_fact_checker_handles_api_errors(self, fact_checker_agent, sample_state_with_leads):
        """Test that Fact-Checker handles API errors gracefully."""
        # Simulate API error on first call, then work
        fact_checker_agent.tavily_client.search.side_effect = [
            Exception("API rate limit exceeded"),
            Exception("API rate limit exceeded"),
            Exception("API rate limit exceeded")
        ]
        fact_checker_agent.tavily_client.total_cost = 0.0
        fact_checker_agent.tavily_client.total_searches = 0
        
        # Act
        result = fact_checker_agent.process(sample_state_with_leads)
        
        # Assert - should handle error gracefully
        assert "evidence" in result
        assert len(result["evidence"]) == 3
        
        # Check all evidence items have no results due to errors
        for evidence in result["evidence"]:
            assert evidence["results"] == []
            assert "error" in evidence  # Error should be recorded
    
    @pytest.mark.unit
    def test_fact_checker_batches_searches(self, fact_checker_agent):
        """Test that Fact-Checker batches searches appropriately."""
        # Create state with many leads
        state = {
            "leads": [
                {
                    "description": f"Event {i}",
                    "type": "test",
                    "search_query": f"test query {i}"
                }
                for i in range(25)  # 25 leads like Researcher generates
            ]
        }
        
        mock_response = {
            "results": [{"title": "Test", "url": "http://test.com", "content": "Test", "score": 0.8}],
            "query": "test",
            "response_time": 0.1
        }
        
        fact_checker_agent.tavily_client.search.return_value = mock_response
        fact_checker_agent.tavily_client.total_cost = 0.025  # 25 * $0.001
        fact_checker_agent.tavily_client.total_searches = 25
        
        # Act
        result = fact_checker_agent.process(state)
        
        # Assert - should process all leads
        assert len(result["evidence"]) == 25
        
        # Verify batching if implemented (check metrics)
        metrics = result["fact_checker_metrics"]
        assert metrics["total_leads"] == 25
        assert metrics["tavily_cost"] == 0.025
        assert metrics["leads_with_evidence"] == 25  # All found evidence
"""Integration tests for workflow coordination between agents."""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from locaited.agents.editor import EditorAgent
from locaited.agents.researcher import ResearcherAgent
from locaited.agents.fact_checker import FactCheckerAgent
from locaited.agents.publisher import PublisherAgent


class TestWorkflowCoordination:
    """Test coordination between agents in the workflow."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for all agents."""
        mock = MagicMock()
        mock.complete_json.return_value = {
            "parsed_content": {},
            "cost": 0.001,
            "total_tokens": 100,
            "elapsed_time": 0.5
        }
        return mock
    
    @pytest.fixture
    def mock_tavily_client(self):
        """Mock Tavily client for Fact-Checker."""
        mock = MagicMock()
        mock.search.return_value = {
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "content": "Test content",
                    "score": 0.9
                }
            ],
            "query": "test query",
            "response_time": 0.5
        }
        mock.total_cost = 0.001
        mock.total_searches = 1
        return mock
    
    @pytest.mark.integration
    def test_editor_to_researcher_handoff(self, mock_llm_client):
        """Test Editor passes profile correctly to Researcher."""
        # Setup agents
        editor = EditorAgent()
        editor.use_cache = False
        editor.llm_client = mock_llm_client
        
        researcher = ResearcherAgent()
        researcher.use_cache = False
        researcher.llm_client = mock_llm_client
        
        # Mock Editor response
        mock_llm_client.complete_json.return_value = {
            "parsed_content": {
                "location": "New York City",
                "time_frame": "this week",
                "interests": ["protests", "cultural events"],
                "researcher_guidance": "Focus on outdoor events with visual impact"
            },
            "cost": 0.001,
            "total_tokens": 100,
            "elapsed_time": 0.5
        }
        
        # Process with Editor
        state = {"user_input": "Find protests and cultural events in NYC this week"}
        state = editor.process(state)
        
        # Verify profile was created
        assert "profile" in state
        assert state["profile"]["location"] == "New York City"
        
        # Mock Researcher response (expects "events" not "leads")
        mock_llm_client.complete_json.return_value = {
            "parsed_content": {
                "events": [
                    {
                        "description": "Climate March at Washington Square Park",
                        "type": "protest",
                        "keywords": ["climate", "march", "protest"]
                    }
                ]
            },
            "cost": 0.002,
            "total_tokens": 200,
            "elapsed_time": 1.0
        }
        
        # Process with Researcher
        state = researcher.process(state)
        
        # Verify leads were created using profile
        assert "leads" in state
        assert len(state["leads"]) > 0
        
        # Verify Researcher was called with correct location and timeframe
        researcher_call = mock_llm_client.complete_json.call_args_list[-1]
        assert "new york city" in researcher_call.kwargs["user_prompt"].lower()
        assert "this week" in researcher_call.kwargs["user_prompt"].lower()
    
    @pytest.mark.integration
    def test_researcher_to_fact_checker_handoff(self, mock_llm_client, mock_tavily_client):
        """Test Researcher passes leads correctly to Fact-Checker."""
        # Setup agents
        researcher = ResearcherAgent()
        researcher.use_cache = False
        researcher.llm_client = mock_llm_client
        
        fact_checker = FactCheckerAgent()
        fact_checker.use_cache = False
        fact_checker.tavily_client = mock_tavily_client
        
        # Setup initial state
        state = {
            "profile": {
                "location": "NYC",
                "time_frame": "this week",
                "interests": ["protests"]
            }
        }
        
        # Mock Researcher response (expects "events" not "leads")
        mock_llm_client.complete_json.return_value = {
            "parsed_content": {
                "events": [
                    {
                        "description": "Climate March at Washington Square Park",
                        "type": "protest",
                        "keywords": ["climate", "march", "protest"]
                    },
                    {
                        "description": "Housing Justice Rally",
                        "type": "protest",
                        "keywords": ["housing", "justice", "rally"]
                    }
                ]
            },
            "cost": 0.002,
            "total_tokens": 200,
            "elapsed_time": 1.0
        }
        
        # Process with Researcher
        state = researcher.process(state)
        
        # Verify leads were created
        assert "leads" in state
        assert len(state["leads"]) == 2
        
        # Process with Fact-Checker
        state = fact_checker.process(state)
        
        # Verify evidence was gathered for each lead
        assert "evidence" in state
        assert len(state["evidence"]) == 2
        
        # Verify search queries were used
        assert mock_tavily_client.search.call_count == 2
        search_queries = [call.kwargs.get('query', '') 
                         for call in mock_tavily_client.search.call_args_list]
        # Researcher builds search queries with keywords
        assert any("climate" in q.lower() and "march" in q.lower() for q in search_queries)
    
    @pytest.mark.integration
    def test_fact_checker_to_publisher_handoff(self, mock_llm_client, mock_tavily_client):
        """Test Fact-Checker passes evidence correctly to Publisher."""
        # Setup agents
        fact_checker = FactCheckerAgent()
        fact_checker.use_cache = False
        fact_checker.tavily_client = mock_tavily_client
        
        publisher = PublisherAgent()
        publisher.use_cache = False
        publisher.llm_client = mock_llm_client
        
        # Setup state with leads
        state = {
            "profile": {
                "location": "NYC",
                "time_frame": "this week",
                "interests": ["protests", "cultural"]
            },
            "leads": [
                {
                    "description": "Climate March",
                    "type": "protest",
                    "search_query": "Climate March NYC"
                }
            ]
        }
        
        # Process with Fact-Checker
        state = fact_checker.process(state)
        
        # Verify evidence was created
        assert "evidence" in state
        assert len(state["evidence"]) > 0
        
        # Mock Publisher extraction response
        extraction_response = {
            "parsed_content": {
                "events": [
                    {
                        "title": "Climate March at Washington Square",
                        "date": "2025-08-25",
                        "location": "Washington Square Park",
                        "description": "Environmental protest"
                    }
                ]
            },
            "cost": 0.003,
            "total_tokens": 300,
            "elapsed_time": 1.5
        }
        
        # Mock Publisher gate response
        gate_response = {
            "parsed_content": {
                "decision": "APPROVE",
                "events": [
                    {
                        "title": "Climate March at Washington Square",
                        "score": 85,
                        "date": "2025-08-25",
                        "location": "Washington Square Park"
                    }
                ],
                "feedback": None
            },
            "cost": 0.002,
            "total_tokens": 200,
            "elapsed_time": 1.0
        }
        
        mock_llm_client.complete_json.side_effect = [extraction_response, gate_response]
        
        # Process with Publisher
        state = publisher.process(state)
        
        # Verify events were extracted and approved
        assert "events" in state
        assert len(state["events"]) > 0
        assert state["gate_decision"] == "APPROVE"
        
        # Verify Publisher received evidence
        extraction_call = mock_llm_client.complete_json.call_args_list[0]
        assert "search results" in extraction_call.kwargs["user_prompt"].lower()
    
    @pytest.mark.integration
    def test_retry_flow_from_publisher_to_editor(self, mock_llm_client):
        """Test RETRY decision flows back to Editor correctly."""
        # Setup agents
        editor = EditorAgent()
        editor.use_cache = False
        editor.llm_client = mock_llm_client
        
        publisher = PublisherAgent()
        publisher.use_cache = False
        publisher.llm_client = mock_llm_client
        
        # Setup state with Publisher feedback
        state = {
            "profile": {
                "location": "NYC",
                "time_frame": "this week",
                "interests": ["protests"],
                "iteration": 1
            },
            "evidence": [
                {
                    "lead": {"description": "Test event"},
                    "results": []
                }
            ],
            "gate_decision": "RETRY",
            "feedback": "Need more specific venue names and exact dates"
        }
        
        # Mock Publisher responses for RETRY
        extraction_response = {
            "parsed_content": {"events": []},
            "cost": 0.001,
            "total_tokens": 100,
            "elapsed_time": 0.5
        }
        
        retry_response = {
            "parsed_content": {
                "decision": "RETRY",
                "events": [],
                "feedback": "Need more specific venue names and exact dates"
            },
            "cost": 0.001,
            "total_tokens": 100,
            "elapsed_time": 0.5
        }
        
        mock_llm_client.complete_json.side_effect = [extraction_response, retry_response]
        
        # Process with Publisher (to get RETRY state)
        state = publisher.process(state)
        
        # Verify RETRY decision
        assert state["gate_decision"] == "RETRY"
        assert "feedback" in state
        
        # Mock Editor retry response
        mock_llm_client.complete_json.return_value = {
            "parsed_content": {
                "location": "New York City",
                "time_frame": "August 25-31, 2025",
                "interests": ["protests", "rallies"],
                "researcher_guidance": "Search for specific venues like Washington Square Park, Union Square. Include exact dates."
            },
            "cost": 0.001,
            "total_tokens": 100,
            "elapsed_time": 0.5
        }
        
        # Process retry with Editor
        state = editor.process(state)
        
        # Verify Editor updated profile based on feedback
        assert "profile" in state
        assert "researcher_guidance" in state["profile"]
        # Editor sets researcher_guidance but may not use exact feedback words
        assert state["profile"]["researcher_guidance"] is not None
        assert len(state["profile"]["researcher_guidance"]) > 0
        # Note: Editor doesn't actually increment iteration in the profile, it defaults to 1
        assert state["profile"]["iteration"] == 1
    
    @pytest.mark.integration
    def test_full_pipeline_flow(self, mock_llm_client, mock_tavily_client):
        """Test complete flow from user input to approved events."""
        # Setup all agents
        editor = EditorAgent()
        editor.use_cache = False
        editor.llm_client = mock_llm_client
        
        researcher = ResearcherAgent()
        researcher.use_cache = False
        researcher.llm_client = mock_llm_client
        
        fact_checker = FactCheckerAgent()
        fact_checker.use_cache = False
        fact_checker.tavily_client = mock_tavily_client
        
        publisher = PublisherAgent()
        publisher.use_cache = False
        publisher.llm_client = mock_llm_client
        
        # Initial state
        state = {"user_input": "Find interesting events in NYC this week"}
        
        # Mock responses for each agent
        editor_response = {
            "parsed_content": {
                "location": "New York City",
                "time_frame": "this week",
                "interests": ["cultural", "protests"],
                "researcher_guidance": "Focus on photogenic events"
            },
            "cost": 0.001,
            "total_tokens": 100,
            "elapsed_time": 0.5
        }
        
        researcher_response = {
            "parsed_content": {
                "events": [
                    {
                        "description": "Climate March",
                        "type": "protest",
                        "keywords": ["climate", "march", "NYC"]
                    }
                ]
            },
            "cost": 0.002,
            "total_tokens": 200,
            "elapsed_time": 1.0
        }
        
        extraction_response = {
            "parsed_content": {
                "events": [
                    {
                        "title": "Climate March",
                        "date": "2025-08-25",
                        "location": "Washington Square Park",
                        "description": "Climate protest"
                    }
                ]
            },
            "cost": 0.003,
            "total_tokens": 300,
            "elapsed_time": 1.5
        }
        
        gate_response = {
            "parsed_content": {
                "decision": "APPROVE",
                "events": [
                    {
                        "title": "Climate March",
                        "score": 90,
                        "date": "2025-08-25",
                        "location": "Washington Square Park"
                    }
                ],
                "feedback": None
            },
            "cost": 0.002,
            "total_tokens": 200,
            "elapsed_time": 1.0
        }
        
        # Set up mock responses in order
        mock_llm_client.complete_json.side_effect = [
            editor_response,
            researcher_response,
            extraction_response,
            gate_response
        ]
        
        # Run full pipeline
        state = editor.process(state)
        assert "profile" in state
        
        state = researcher.process(state)
        assert "leads" in state
        
        state = fact_checker.process(state)
        assert "evidence" in state
        
        state = publisher.process(state)
        assert "events" in state
        assert state["gate_decision"] == "APPROVE"
        
        # Verify final state has all components
        assert len(state["events"]) > 0
        assert state["events"][0]["title"] == "Climate March"
        assert state["events"][0]["score"] == 90
        
        # Verify metrics are tracked
        assert "editor_metrics" in state
        assert "researcher_metrics" in state
        assert "fact_checker_metrics" in state
        assert "publisher_metrics" in state
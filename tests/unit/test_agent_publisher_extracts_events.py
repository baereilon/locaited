"""Unit tests for Publisher agent event extraction and gate decisions."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from locaited.agents.publisher import PublisherAgent


class TestPublisherAgentExtractsEvents:
    """Test Publisher agent event extraction and gate decision functionality."""
    
    @pytest.fixture
    def publisher_agent(self):
        """Create Publisher agent instance."""
        # Disable caching for tests
        agent = PublisherAgent()
        agent.use_cache = False
        return agent
    
    @pytest.fixture
    def mock_extraction_response(self):
        """Mock LLM response for event extraction."""
        return {
            "parsed_content": {
                "events": [
                    {
                        "title": "Climate March at Washington Square Park",
                        "date": "2025-08-25",
                        "time": "14:00",
                        "location": "Washington Square Park, NYC",
                        "description": "Environmental activists march for climate action",
                        "access_info": "Open to public",
                        "contact_info": "climatenyc@example.com",
                        "equipment_notes": "Wide angle lens recommended for crowd shots"
                    },
                    {
                        "title": "Brooklyn Book Festival",
                        "date": "2025-08-24",
                        "time": "10:00",
                        "location": "Brooklyn Borough Hall",
                        "description": "Annual celebration of literature",
                        "access_info": "Free admission",
                        "contact_info": "info@brooklynbookfest.org",
                        "equipment_notes": "Natural light, portraits of authors"
                    }
                ] * 8  # 16 events to test limit
            },
            "cost": 0.003,
            "total_tokens": 2000,
            "elapsed_time": 2.5
        }
    
    @pytest.fixture
    def mock_gate_response_approve(self):
        """Mock LLM response for gate decision - APPROVE."""
        return {
            "parsed_content": {
                "decision": "APPROVE",
                "events": [
                    {
                        "title": "Climate March at Washington Square Park", 
                        "score": 95,
                        "date": "2025-08-25",
                        "time": "14:00",
                        "location": "Washington Square Park, NYC"
                    },
                    {
                        "title": "Brooklyn Book Festival", 
                        "score": 85,
                        "date": "2025-08-24",
                        "time": "10:00",
                        "location": "Brooklyn Borough Hall"
                    }
                ] * 5,  # 10 scored events
                "feedback": None
            },
            "cost": 0.002,
            "total_tokens": 500,
            "elapsed_time": 1.0
        }
    
    @pytest.fixture
    def mock_gate_response_retry(self):
        """Mock LLM response for gate decision - RETRY."""
        return {
            "parsed_content": {
                "decision": "RETRY",
                "events": [],
                "feedback": "Need more specific venue names and exact dates. Focus on confirmed events, not rumors."
            },
            "cost": 0.002,
            "total_tokens": 500,
            "elapsed_time": 1.0
        }
    
    @pytest.fixture
    def sample_state_with_evidence(self):
        """Sample state with evidence from Fact-Checker."""
        return {
            "profile": {
                "location": "New York City",
                "time_frame": "this week",
                "interests": ["protests", "cultural events"]
            },
            "evidence": [
                {
                    "lead": {
                        "description": "Climate March at Washington Square Park",
                        "type": "protest"
                    },
                    "results": [
                        {
                            "title": "Climate March Confirmed",
                            "content": "Environmental activists will gather at Washington Square Park on August 25 at 2 PM...",
                            "url": "https://example.com/climate-march"
                        }
                    ]
                },
                {
                    "lead": {
                        "description": "Brooklyn Book Festival",
                        "type": "cultural"
                    },
                    "results": [
                        {
                            "title": "Brooklyn Book Festival This Weekend",
                            "content": "The annual Brooklyn Book Festival returns August 24 starting at 10 AM...",
                            "url": "https://example.com/book-fest"
                        }
                    ]
                }
            ]
        }
    
    @pytest.mark.unit
    def test_publisher_extracts_events_from_evidence(self, publisher_agent, mock_extraction_response, 
                                                     mock_gate_response_approve, sample_state_with_evidence):
        """Test that Publisher extracts concrete events from evidence."""
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            # Setup mock to return extraction then gate response
            mock_llm.complete_json.side_effect = [mock_extraction_response, mock_gate_response_approve]
            
            # Act
            result = publisher_agent.process(sample_state_with_evidence)
            
            # Assert events were extracted
            assert "events" in result
            assert len(result["events"]) > 0
            
            # Verify LLM was called twice (extraction + gate)
            assert mock_llm.complete_json.call_count == 2
            
            # Check first call was for extraction
            first_call = mock_llm.complete_json.call_args_list[0]
            assert "extract" in first_call.kwargs["system_prompt"].lower()
            # Publisher uses "search results" not "evidence" in prompt
            assert "search results" in first_call.kwargs["user_prompt"].lower()
    
    @pytest.mark.unit
    def test_publisher_deduplicates_similar_events(self, publisher_agent, sample_state_with_evidence):
        """Test that Publisher deduplicates similar events."""
        # Create response with duplicate events
        duplicate_response = {
            "parsed_content": {
                "events": [
                    {
                        "title": "Climate March at Washington Square",
                        "date": "2025-08-25",
                        "time": "14:00",
                        "location": "Washington Square Park",
                        "description": "Climate protest"
                    },
                    {
                        "title": "Climate March Washington Square Park",  # Similar title
                        "date": "2025-08-25",  # Same date
                        "time": "14:00",  # Same time
                        "location": "Washington Square Park NYC",  # Similar location
                        "description": "Environmental march"
                    },
                    {
                        "title": "Brooklyn Book Festival",  # Different event
                        "date": "2025-08-24",
                        "time": "10:00",
                        "location": "Brooklyn",
                        "description": "Book festival"
                    }
                ]
            },
            "cost": 0.003,
            "total_tokens": 1000,
            "elapsed_time": 1.5
        }
        
        gate_response = {
            "parsed_content": {
                "decision": "APPROVE",
                "events": [
                    {"title": "Climate March at Washington Square", "score": 90, "date": "2025-08-25", "time": "14:00", "location": "Washington Square Park"},
                    {"title": "Brooklyn Book Festival", "score": 85, "date": "2025-08-24", "time": "10:00", "location": "Brooklyn"}
                ],
                "feedback": None
            },
            "cost": 0.002,
            "total_tokens": 500,
            "elapsed_time": 1.0
        }
        
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.side_effect = [duplicate_response, gate_response]
            
            # Act
            result = publisher_agent.process(sample_state_with_evidence)
            
            # Assert - should have deduplicated (2 unique events, not 3)
            assert len(result["events"]) == 2
            event_titles = [e["title"] for e in result["events"]]
            assert "Brooklyn Book Festival" in event_titles
    
    @pytest.mark.unit
    def test_publisher_scores_events(self, publisher_agent, mock_extraction_response, 
                                    mock_gate_response_approve, sample_state_with_evidence):
        """Test that Publisher scores events 0-100."""
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.side_effect = [mock_extraction_response, mock_gate_response_approve]
            
            # Act
            result = publisher_agent.process(sample_state_with_evidence)
            
            # Assert all events have scores
            for event in result["events"]:
                assert "score" in event
                assert isinstance(event["score"], (int, float))
                assert 0 <= event["score"] <= 100
    
    @pytest.mark.unit
    def test_publisher_makes_gate_decision(self, publisher_agent, mock_extraction_response, 
                                          sample_state_with_evidence):
        """Test that Publisher makes APPROVE/RETRY gate decisions."""
        # Test APPROVE
        approve_response = {
            "parsed_content": {
                "decision": "APPROVE",
                "events": [{"title": f"Event {i}", "score": 80+i, "date": "2025-08-20", "time": "10:00", "location": f"Location {i}"} for i in range(10)],
                "feedback": None
            },
            "cost": 0.002,
            "total_tokens": 500,
            "elapsed_time": 1.0
        }
        
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.side_effect = [mock_extraction_response, approve_response]
            
            # Act
            result = publisher_agent.process(sample_state_with_evidence)
            
            # Assert
            assert result["gate_decision"] == "APPROVE"
            # Publisher doesn't set feedback field when APPROVE
            assert "feedback" not in result or result.get("feedback") is None
            
        # Test RETRY
        retry_response = {
            "parsed_content": {
                "decision": "RETRY",
                "events": [{"title": "Event 1", "score": 40}],
                "feedback": "Need more specific searches with exact dates"
            },
            "cost": 0.002,
            "total_tokens": 500,
            "elapsed_time": 1.0
        }
        
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.side_effect = [mock_extraction_response, retry_response]
            
            # Act
            result = publisher_agent.process(sample_state_with_evidence)
            
            # Assert
            assert result["gate_decision"] == "RETRY"
            assert result["feedback"] == "Need more specific searches with exact dates"
    
    @pytest.mark.unit
    def test_publisher_limits_to_15_events(self, publisher_agent, sample_state_with_evidence):
        """Test that Publisher limits output to max 15 events."""
        # Create response with 20+ events
        many_events_response = {
            "parsed_content": {
                "events": [
                    {
                        "title": f"Event {i}",
                        "date": f"2025-08-{20+i}",
                        "time": f"{10+i}:00",
                        "location": f"Location {i}",
                        "description": f"Description {i}"
                    }
                    for i in range(20)  # 20 events
                ]
            },
            "cost": 0.004,
            "total_tokens": 3000,
            "elapsed_time": 3.0
        }
        
        gate_response = {
            "parsed_content": {
                "decision": "APPROVE",
                "events": [{"title": f"Event {i}", "score": 70+i, "date": "2025-08-20", "time": "10:00", "location": f"Location {i}"} for i in range(15)],
                "feedback": None
            },
            "cost": 0.002,
            "total_tokens": 500,
            "elapsed_time": 1.0
        }
        
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.side_effect = [many_events_response, gate_response]
            
            # Act
            result = publisher_agent.process(sample_state_with_evidence)
            
            # Assert - Publisher limits to 10 events in gate decision, not 15
            assert len(result["events"]) <= 10
            assert len(result["events"]) == 10  # Should be exactly 10 (gate decision limit)
    
    @pytest.mark.unit
    def test_publisher_provides_retry_feedback(self, publisher_agent, mock_extraction_response,
                                              mock_gate_response_retry, sample_state_with_evidence):
        """Test that Publisher provides actionable feedback on RETRY."""
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.side_effect = [mock_extraction_response, mock_gate_response_retry]
            
            # Act
            result = publisher_agent.process(sample_state_with_evidence)
            
            # Assert
            assert result["gate_decision"] == "RETRY"
            assert result["feedback"] is not None
            assert "specific" in result["feedback"].lower()
            assert len(result["feedback"]) > 10  # Meaningful feedback
            
            # Verify feedback was generated in gate decision call
            gate_call = mock_llm.complete_json.call_args_list[1]
            assert "feedback" in gate_call.kwargs["user_prompt"].lower()
    
    @pytest.mark.unit
    def test_publisher_tracks_llm_costs(self, publisher_agent, mock_extraction_response,
                                       mock_gate_response_approve, sample_state_with_evidence):
        """Test that Publisher tracks costs for both LLM calls."""
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.side_effect = [mock_extraction_response, mock_gate_response_approve]
            
            # Act
            result = publisher_agent.process(sample_state_with_evidence)
            
            # Assert cost tracking
            assert "publisher_metrics" in result
            metrics = result["publisher_metrics"]
            
            # Should track llm_cost (combined cost)
            assert "llm_cost" in metrics
            # Publisher makes 2 LLM calls: extraction (0.003) + gate (0.002)
            assert metrics["llm_cost"] == 0.005  # Sum of both
    
    @pytest.mark.unit
    def test_publisher_handles_no_evidence(self, publisher_agent):
        """Test that Publisher handles cases with no evidence."""
        state = {
            "profile": {
                "location": "NYC",
                "time_frame": "this week",
                "interests": ["events"]
            },
            "evidence": []  # No evidence
        }
        
        # Should still try to extract but find nothing
        empty_extraction = {
            "parsed_content": {
                "events": []
            },
            "cost": 0.001,
            "total_tokens": 100,
            "elapsed_time": 0.5
        }
        
        retry_response = {
            "parsed_content": {
                "decision": "RETRY",
                "events": [],
                "feedback": "No evidence provided, need to search for events"
            },
            "cost": 0.001,
            "total_tokens": 100,
            "elapsed_time": 0.5
        }
        
        with patch.object(publisher_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.side_effect = [empty_extraction, retry_response]
            
            # Act
            result = publisher_agent.process(state)
            
            # Assert
            assert result["gate_decision"] == "RETRY"
            assert len(result["events"]) == 0
            assert "no evidence" in result["feedback"].lower()
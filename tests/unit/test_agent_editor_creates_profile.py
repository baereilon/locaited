"""Unit tests for Editor agent profile creation."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from locaited.agents.editor import EditorAgent


class TestEditorAgentCreatesProfile:
    """Test Editor agent profile creation functionality."""
    
    @pytest.fixture
    def editor_agent(self):
        """Create Editor agent instance."""
        return EditorAgent()
    
    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for profile creation."""
        return {
            "parsed_content": {
                "location": "New York City",
                "time_frame": "this week",
                "interests": ["protests", "cultural events"],
                "iteration": 1,
                "focus_event_types": ["protests", "festivals"],
                "avoid_event_types": [],
                "key_organizations": ["BLM", "Climate Action"],
                "researcher_guidance": "Focus on grassroots protests and major cultural festivals",
                "search_themes": ["social justice", "arts"]
            },
            "cost": 0.001
        }
    
    @pytest.mark.unit
    def test_editor_creates_profile_from_user_input(self, editor_agent, mock_llm_response):
        """Test that Editor creates a profile from user input."""
        # Arrange
        state = {
            "user_input": {
                "location": "NYC",
                "time_frame": "this week",
                "interests": ["protests", "cultural events"]
            }
        }
        
        # Mock the LLM client
        with patch.object(editor_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.return_value = mock_llm_response
            
            # Act
            result = editor_agent.process(state)
            
            # Assert
            assert "profile" in result
            profile = result["profile"]
            assert profile["location"] == "New York City"
            assert profile["time_frame"] == "this week"
            assert "protests" in profile["interests"]
            assert "researcher_guidance" in profile
            assert "editor_metrics" in result
            # Editor tracks cumulative cost, not just this call
            assert "llm_cost" in result["editor_metrics"]
            
            # Verify LLM was called with correct prompts
            mock_llm.complete_json.assert_called_once()
            call_args = mock_llm.complete_json.call_args
            assert "photojournalist" in call_args[1]["system_prompt"].lower()
            assert "profile" in call_args[1]["user_prompt"].lower()
    
    @pytest.mark.unit
    def test_editor_handles_retry_with_feedback(self, editor_agent, mock_llm_response):
        """Test that Editor handles retry with Publisher feedback."""
        # Arrange
        state = {
            "user_input": {
                "location": "Brooklyn",
                "time_frame": "next week",
                "interests": ["art exhibitions"]
            },
            "profile": {
                "iteration": 1
            },
            "gate_decision": "RETRY",
            "feedback": "Need more specific venue suggestions"
        }
        
        # Update mock response for retry
        retry_response = dict(mock_llm_response)
        retry_response["parsed_content"] = dict(mock_llm_response["parsed_content"])
        retry_response["parsed_content"]["iteration"] = 2
        retry_response["parsed_content"]["researcher_guidance"] = (
            "Focus on specific galleries like Brooklyn Museum, BRIC Arts"
        )
        
        with patch.object(editor_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.return_value = retry_response
            
            # Act
            result = editor_agent.process(state)
            
            # Assert
            assert result["profile"]["iteration"] == 2
            assert "Brooklyn Museum" in result["profile"]["researcher_guidance"]
            
            # Verify feedback was included in prompt
            call_args = mock_llm.complete_json.call_args
            assert "venue suggestions" in call_args[1]["user_prompt"]
    
    @pytest.mark.unit
    def test_editor_formats_context_correctly(self, editor_agent):
        """Test that Editor formats context correctly for LLM."""
        # Arrange
        state = {
            "user_input": {
                "location": "Manhattan",
                "time_frame": "today",
                "interests": ["concerts", "museums"]
            },
            "profile": {
                "iteration": 2
            },
            "gate_decision": "RETRY",
            "feedback": "Too many past events"
        }
        
        # Act
        context = editor_agent._format_context_for_llm(state)
        
        # Assert
        assert "Manhattan" in context
        assert "today" in context
        assert "concerts" in context
        assert "museums" in context
        assert "iteration 3" in context.lower()  # iteration + 1
        assert "Too many past events" in context
    
    @pytest.mark.unit
    def test_editor_handles_string_input(self, editor_agent, mock_llm_response):
        """Test that Editor handles plain string user input."""
        # Arrange
        state = {
            "user_input": "Find me interesting protests in NYC this week"
        }
        
        with patch.object(editor_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.return_value = mock_llm_response
            
            # Act
            result = editor_agent.process(state)
            
            # Assert
            assert "profile" in result
            assert result["profile"]["location"] == "New York City"
            
            # Verify string was passed to LLM
            call_args = mock_llm.complete_json.call_args
            assert "interesting protests" in call_args[1]["user_prompt"]
    
    @pytest.mark.unit
    def test_editor_tracks_costs(self, editor_agent):
        """Test that Editor tracks LLM costs correctly."""
        # Arrange
        state = {
            "user_input": {
                "location": "NYC",
                "time_frame": "this week",
                "interests": ["events"]
            }
        }
        
        mock_response = {
            "parsed_content": {
                "location": "NYC",
                "time_frame": "this week",
                "interests": ["events"],
                "researcher_guidance": "Find events"
            },
            "cost": 0.00234
        }
        
        with patch.object(editor_agent, 'llm_client') as mock_llm:
            mock_llm.complete_json.return_value = mock_response
            
            # Act
            result = editor_agent.process(state)
            
            # Assert
            assert "editor_metrics" in result
            assert "llm_cost" in result["editor_metrics"]
            # Verify total cost was updated
            assert editor_agent.total_cost == 0.00234
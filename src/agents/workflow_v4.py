"""Workflow v0.4.0 - LangGraph orchestration with retry logic."""

import logging
from typing import Dict, Any, TypedDict, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from src.agents.editor_v4 import EditorV4
from src.agents.researcher_v4 import ResearcherV4
from src.agents.fact_checker_v4 import FactCheckerV4
from src.agents.publisher_v4 import PublisherV4

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict, total=False):
    """State schema for v0.4.0 workflow."""
    # User input
    user_input: Dict[str, Any]
    
    # Editor outputs
    profile: Dict[str, Any]
    location: str
    time_frame: str
    should_retry: bool
    editor_metrics: Dict[str, Any]
    
    # Researcher outputs
    leads: List[Dict[str, Any]]
    researcher_metrics: Dict[str, Any]
    
    # Fact-Checker outputs
    evidence: List[Dict[str, Any]]
    fact_checker_metrics: Dict[str, Any]
    
    # Publisher outputs
    events: List[Dict[str, Any]]
    gate_decision: str  # APPROVE, RETRY, ERROR
    feedback: Optional[str]
    publisher_metrics: Dict[str, Any]
    
    # Workflow tracking
    workflow_start_time: str
    workflow_end_time: Optional[str]
    total_iterations: int
    workflow_metrics: Dict[str, Any]  # Combined metrics


class WorkflowV4:
    """Orchestrates the v0.4.0 agent workflow with retry logic."""
    
    def __init__(self, use_cache: bool = True):
        """Initialize workflow with agents.
        
        Args:
            use_cache: Whether agents should use caching
        """
        logger.info("Initializing Workflow v0.4.0...")
        
        # Initialize agents
        self.editor = EditorV4()
        self.researcher = ResearcherV4(use_cache=use_cache)
        self.fact_checker = FactCheckerV4(use_cache=use_cache)
        self.publisher = PublisherV4(use_cache=use_cache)
        
        # Create workflow
        self.workflow = self._create_workflow()
        
        logger.info("Workflow v0.4.0 initialized")
    
    def _create_workflow(self) -> CompiledStateGraph:
        """Create LangGraph workflow with retry logic.
        
        Returns:
            Compiled workflow graph
        """
        # Create state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (each agent's process method)
        workflow.add_node("editor", self.editor.process)
        workflow.add_node("researcher", self.researcher.process)
        workflow.add_node("fact_checker", self.fact_checker.process)
        workflow.add_node("publisher", self.publisher.process)
        
        # Add linear edges
        workflow.add_edge("editor", "researcher")
        workflow.add_edge("researcher", "fact_checker")
        workflow.add_edge("fact_checker", "publisher")
        
        # Add conditional edge after publisher
        workflow.add_conditional_edges(
            "publisher",
            self._route_publisher_decision,
            {
                "editor": "editor",
                END: END
            }
        )
        
        # Set entry point
        workflow.set_entry_point("editor")
        
        # Compile and return
        return workflow.compile()
    
    def _route_publisher_decision(self, state: WorkflowState) -> str:
        """Route based on Publisher's gate decision.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name or END
        """
        gate_decision = state.get("gate_decision", "ERROR")
        should_retry = state.get("should_retry", True)
        
        # Log decision
        logger.info(f"Routing decision: gate={gate_decision}, should_retry={should_retry}")
        
        # Route based on decision and retry flag
        if gate_decision == "RETRY" and should_retry:
            iteration = state.get("profile", {}).get("iteration", 0)
            logger.info(f"Retrying workflow (iteration {iteration + 1})")
            return "editor"
        else:
            if gate_decision == "APPROVE":
                logger.info("Workflow approved - ending with events")
            elif gate_decision == "RETRY" and not should_retry:
                logger.info("Max retries reached - ending")
            else:
                logger.warning(f"Workflow ending with status: {gate_decision}")
            return END
    
    def run_workflow(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with user input.
        
        Args:
            user_input: Dict with location, time_frame, interests
            
        Returns:
            Final state with events or error information
        """
        try:
            # Initialize state
            initial_state = WorkflowState(
                user_input=user_input,
                workflow_start_time=datetime.now().isoformat(),
                total_iterations=0
            )
            
            logger.info(f"Starting workflow for: {user_input}")
            
            # Run workflow (handles retries internally)
            final_state = self.workflow.invoke(initial_state)
            
            # Add completion time
            final_state["workflow_end_time"] = datetime.now().isoformat()
            
            # Collect and add workflow metrics
            final_state["workflow_metrics"] = self._collect_workflow_metrics(final_state)
            
            # Log results
            if final_state.get("gate_decision") == "APPROVE":
                events = final_state.get("events", [])
                logger.info(f"Workflow completed successfully with {len(events)} events")
                logger.info(f"Total cost: ${final_state['workflow_metrics']['total_cost']:.4f}")
            else:
                logger.warning(f"Workflow ended without approval: {final_state.get('gate_decision')}")
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "error": str(e),
                "events": [],
                "gate_decision": "ERROR",
                "workflow_end_time": datetime.now().isoformat()
            }
    
    def _collect_workflow_metrics(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics from state and agents.
        
        Args:
            state: Final workflow state
            
        Returns:
            Combined metrics
        """
        # Calculate total cost
        total_cost = 0
        if state.get("editor_metrics", {}).get("llm_cost"):
            total_cost += state["editor_metrics"]["llm_cost"]
        if state.get("researcher_metrics", {}).get("llm_cost"):
            total_cost += state["researcher_metrics"]["llm_cost"]
        if state.get("fact_checker_metrics", {}).get("tavily_cost"):
            total_cost += state["fact_checker_metrics"]["tavily_cost"]
        if state.get("publisher_metrics", {}).get("llm_cost"):
            total_cost += state["publisher_metrics"]["llm_cost"]
        
        # Calculate duration
        start_time = datetime.fromisoformat(state["workflow_start_time"])
        end_time = datetime.fromisoformat(state["workflow_end_time"])
        duration = (end_time - start_time).total_seconds()
        
        return {
            "total_cost": total_cost,
            "total_duration_seconds": duration,
            "iterations": state.get("profile", {}).get("iteration", 1),
            "leads_generated": len(state.get("leads", [])),
            "evidence_found": state.get("fact_checker_metrics", {}).get("total_results", 0),
            "events_extracted": len(state.get("events", [])),
            "final_decision": state.get("gate_decision", "ERROR")
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from all agents.
        
        Returns:
            Combined metrics from all agents
        """
        return {
            "editor": self.editor.get_metrics(),
            "researcher": self.researcher.get_metrics(),
            "fact_checker": self.fact_checker.get_metrics(),
            "publisher": self.publisher.get_metrics()
        }
    
    def reset_metrics(self):
        """Reset metrics for all agents."""
        self.editor.reset_metrics()
        self.researcher.reset_metrics()
        self.fact_checker.reset_metrics()
        self.publisher.reset_metrics()
        logger.info("All agent metrics reset")
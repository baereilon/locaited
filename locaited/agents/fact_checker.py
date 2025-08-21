"""Fact-Checker Agent - Tavily evidence gatherer."""

import logging
from typing import Dict, Any, List
from datetime import datetime
import time

from locaited.agents.base_agent import CachedAgent
from locaited.utils.tavily_client import get_tavily_client

logger = logging.getLogger(__name__)


class FactCheckerAgent(CachedAgent):
    """Fact-Checker that searches for evidence using Tavily."""
    
    def __init__(self, use_cache: bool = True):
        """Initialize Fact-Checker v0.4.0.
        
        Args:
            use_cache: Whether to use caching
        """
        super().__init__(name="fact_checker", use_cache=use_cache)
        self.tavily_client = get_tavily_client(use_cache=use_cache)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Search for evidence of event leads.
        
        Args:
            state: Workflow state with leads from Researcher
            
        Returns:
            Updated state with evidence
        """
        try:
            # Extract leads
            leads = state.get("leads", [])
            if not leads:
                logger.warning("No leads to fact-check")
                state["evidence"] = []
                state["fact_checker_metrics"] = {"error": "No leads provided"}
                return state
            
            # Check cache
            cache_key = self._generate_cache_key(leads)
            cached_result = self.get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Using cached evidence")
                state["evidence"] = cached_result["evidence"]
                state["fact_checker_metrics"] = cached_result["metrics"]
                return state
            
            # Search for evidence
            logger.info(f"Searching for evidence on {len(leads)} leads...")
            evidence = self._batch_search_leads(leads)
            
            # Track metrics
            metrics = {
                "total_leads": len(leads),
                "leads_with_evidence": len([e for e in evidence if e["results"]]),
                "total_results": sum(len(e["results"]) for e in evidence),
                "tavily_cost": self.tavily_client.total_cost,
                "search_time": self.tavily_client.total_time,
                "errors": len([e for e in evidence if "error" in e])
            }
            
            # Update cost tracking
            self.total_cost += self.tavily_client.total_cost
            
            # Save to cache
            result = {"evidence": evidence, "metrics": metrics}
            self.save_to_cache(cache_key, result)
            
            # Update state
            state["evidence"] = evidence
            state["fact_checker_metrics"] = metrics
            
            logger.info(
                f"Found evidence for {metrics['leads_with_evidence']}/{len(leads)} leads, "
                f"total results: {metrics['total_results']}, "
                f"cost: ${metrics['tavily_cost']:.4f}"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error gathering evidence: {e}")
            self.errors.append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "state": state
            })
            
            # Return empty evidence on error
            state["evidence"] = []
            state["fact_checker_metrics"] = {"error": str(e)}
            return state
    
    def _batch_search_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search for evidence on multiple leads.
        
        Args:
            leads: List of event leads
            
        Returns:
            List of evidence results
        """
        evidence = []
        
        for i, lead in enumerate(leads):
            logger.info(f"Searching evidence {i+1}/{len(leads)}: {lead['description'][:50]}...")
            
            try:
                # Search using the prepared query
                search_results = self._search_for_evidence(lead)
                
                evidence.append({
                    "lead": lead,
                    "results": search_results.get("results", []),
                    "answer": search_results.get("answer"),
                    "search_time": search_results.get("search_time", 0)
                })
                
                # Small delay to avoid rate limiting
                if i < len(leads) - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Failed to search for lead {i+1}: {e}")
                evidence.append({
                    "lead": lead,
                    "results": [],
                    "error": str(e)
                })
        
        return evidence
    
    def _search_for_evidence(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Search Tavily for evidence of a specific lead.
        
        Args:
            lead: Event lead with search_query
            
        Returns:
            Search results from Tavily
        """
        # Use the pre-built search query from Researcher
        query = lead.get("search_query", lead["description"])
        
        # Search with appropriate parameters for event evidence
        return self.tavily_client.search(
            query=query,
            search_depth="advanced",  # Use advanced for better event details
            max_results=10,  # Get multiple sources
            include_answer=True,  # Get AI summary
            include_raw_content=False  # Don't need raw HTML
        )
    
    def _generate_cache_key(self, leads: List[Dict[str, Any]]) -> str:
        """Generate cache key from leads.
        
        Args:
            leads: List of leads
            
        Returns:
            Cache key string
        """
        # Create a stable key from lead descriptions
        lead_strings = [lead.get("description", "") for lead in leads[:5]]  # First 5 for key
        return "_".join(lead_strings)[:100]  # Limit length
    
    def validate_output(self, state: Dict[str, Any]) -> bool:
        """Validate fact-checker output.
        
        Args:
            state: State with evidence
            
        Returns:
            True if valid
        """
        if "evidence" not in state:
            logger.error("No evidence in state")
            return False
        
        evidence = state["evidence"]
        if not evidence:
            logger.warning("No evidence gathered")
            return True  # Empty is valid but not ideal
        
        # Check evidence structure
        for item in evidence:
            if "lead" not in item:
                logger.error(f"Evidence missing lead: {item}")
                return False
            if "results" not in item and "error" not in item:
                logger.error(f"Evidence missing results or error: {item}")
                return False
        
        logger.info(f"Validated {len(evidence)} evidence items")
        return True
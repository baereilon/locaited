"""
LLM-based implementation of the Event Verifier.

Uses GPT-3.5 to classify events based on specificity and temporality.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from locaited.agents.verifier import VerifierInterface, EventVerification
from locaited.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class VerifierLLM(VerifierInterface):
    """LLM-based verifier using GPT-3.5 for classification."""
    
    def __init__(self):
        """Initialize LLM verifier with GPT-3.5 for cost efficiency."""
        self.llm_client = get_llm_client(model="gpt-3.5-turbo", temperature=0)
        logger.info("Initialized LLM-based verifier with GPT-3.5")
    
    def verify_event(self, event: Dict[str, Any]) -> EventVerification:
        """
        Verify a single event using LLM.
        
        Args:
            event: Event dictionary with at least 'description'
            
        Returns:
            EventVerification object with classification results
        """
        verification = EventVerification(event)
        
        try:
            # Build prompt for classification
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(event)
            
            # Get LLM classification
            response = self.llm_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=200,
                schema=self._get_response_schema()
            )
            
            # Parse response
            result = response["parsed_content"]
            
            # Update verification object
            verification.is_specific = result["is_specific"]
            verification.has_date = result["specificity_details"]["has_date"]
            verification.has_location = result["specificity_details"]["has_location"]
            verification.has_time = result["specificity_details"].get("has_time", False)
            verification.temporality = result["temporality"]
            verification.confidence = result["confidence"] / 100.0  # Convert to 0-1
            
            # Determine if we should keep (must be BOTH specific AND future)
            verification.should_keep = (
                verification.is_specific and 
                verification.temporality == "FUTURE"
            )
            
            logger.debug(f"LLM verified: {event.get('description', '')[:50]}... "
                        f"Specific: {verification.is_specific}, "
                        f"Temporal: {verification.temporality}")
            
        except Exception as e:
            logger.error(f"LLM verification failed for event: {e}")
            # Default to unclear/false on error
            verification.temporality = "UNCLEAR"
            verification.is_specific = False
            verification.should_keep = False
        
        return verification
    
    def verify_batch(self, events: List[Dict[str, Any]]) -> List[EventVerification]:
        """
        Verify a batch of events.
        
        For LLM implementation, we process in small batches to optimize API calls.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of EventVerification objects
        """
        verifications = []
        batch_size = 5  # Process 5 at a time for efficiency
        
        for i in range(0, len(events), batch_size):
            batch = events[i:i+batch_size]
            
            if len(batch) == 1:
                # Single event, use single verification
                verifications.append(self.verify_event(batch[0]))
            else:
                # Multiple events, use batch prompt
                batch_verifications = self._verify_batch_together(batch)
                verifications.extend(batch_verifications)
        
        return verifications
    
    def _verify_batch_together(self, events: List[Dict[str, Any]]) -> List[EventVerification]:
        """
        Verify multiple events in a single LLM call for efficiency.
        
        Args:
            events: List of events (max 5)
            
        Returns:
            List of EventVerification objects
        """
        verifications = []
        
        try:
            # Build batch prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_batch_user_prompt(events)
            
            # Get LLM classification for all events
            response = self.llm_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1000,
                schema=self._get_batch_response_schema()
            )
            
            # Parse response for each event
            results = response["parsed_content"]["verifications"]
            
            for i, event in enumerate(events):
                verification = EventVerification(event)
                
                if i < len(results):
                    result = results[i]
                    
                    verification.is_specific = result["is_specific"]
                    verification.has_date = result["specificity_details"]["has_date"]
                    verification.has_location = result["specificity_details"]["has_location"]
                    verification.has_time = result["specificity_details"].get("has_time", False)
                    verification.temporality = result["temporality"]
                    verification.confidence = result["confidence"] / 100.0
                    
                    verification.should_keep = (
                        verification.is_specific and 
                        verification.temporality == "FUTURE"
                    )
                else:
                    # Fallback if response is incomplete
                    verification.temporality = "UNCLEAR"
                    verification.is_specific = False
                    verification.should_keep = False
                
                verifications.append(verification)
            
            logger.debug(f"Batch verified {len(verifications)} events via LLM")
            
        except Exception as e:
            logger.error(f"Batch LLM verification failed: {e}")
            # Return unclear/false for all on error
            for event in events:
                verification = EventVerification(event)
                verification.temporality = "UNCLEAR"
                verification.is_specific = False
                verification.should_keep = False
                verifications.append(verification)
        
        return verifications
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for event classification."""
        today = datetime.now().strftime("%B %d, %Y")
        
        return f"""You are an event validator for photojournalists in New York City.
Your job is to classify events based on two criteria:

1. SPECIFICITY: Does the event have a concrete date AND location?
   - SPECIFIC: Has both a date (like "August 24" or "next Tuesday") AND a location (venue, address, or area)
   - NOT SPECIFIC: Missing date OR location OR both

2. TEMPORALITY: When is the event happening relative to today ({today})?
   - FUTURE: Happening after today
   - PAST: Already happened before today
   - ONGOING: Happening now or throughout a period including today
   - UNCLEAR: Cannot determine when it happens

IMPORTANT RULES:
- An event needs BOTH date AND location to be specific (time is nice but not required)
- "Fashion Week" without specific shows/dates is NOT specific
- "Protests this week" without specific day/location is NOT specific
- "Climate March at Union Square on August 24" IS specific
- Be strict about specificity - when in doubt, mark as not specific"""
    
    def _build_user_prompt(self, event: Dict[str, Any]) -> str:
        """Build the user prompt for a single event."""
        description = event.get("description", "")
        
        return f"""Classify this event:

Event: {description}

Determine:
1. Is it SPECIFIC (has date AND location)?
2. When is it happening (FUTURE/PAST/ONGOING/UNCLEAR)?

Provide your classification with confidence 0-100."""
    
    def _build_batch_user_prompt(self, events: List[Dict[str, Any]]) -> str:
        """Build the user prompt for multiple events."""
        events_text = "\n".join([
            f"{i+1}. {event.get('description', '')}"
            for i, event in enumerate(events)
        ])
        
        return f"""Classify these {len(events)} events:

{events_text}

For each event, determine:
1. Is it SPECIFIC (has date AND location)?
2. When is it happening (FUTURE/PAST/ONGOING/UNCLEAR)?

Provide classifications with confidence 0-100 for each."""
    
    def _get_response_schema(self) -> Dict[str, Any]:
        """Get JSON schema for single event response."""
        return {
            "type": "object",
            "required": ["is_specific", "specificity_details", "temporality", "confidence"],
            "properties": {
                "is_specific": {
                    "type": "boolean",
                    "description": "True if event has both date AND location"
                },
                "specificity_details": {
                    "type": "object",
                    "required": ["has_date", "has_location"],
                    "properties": {
                        "has_date": {
                            "type": "boolean",
                            "description": "True if specific date mentioned"
                        },
                        "has_location": {
                            "type": "boolean",
                            "description": "True if specific location/venue mentioned"
                        },
                        "has_time": {
                            "type": "boolean",
                            "description": "True if specific time mentioned (bonus)"
                        }
                    }
                },
                "temporality": {
                    "type": "string",
                    "enum": ["FUTURE", "PAST", "ONGOING", "UNCLEAR"],
                    "description": "When the event occurs relative to today"
                },
                "confidence": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Confidence in classification (0-100)"
                }
            }
        }
    
    def _get_batch_response_schema(self) -> Dict[str, Any]:
        """Get JSON schema for batch response."""
        return {
            "type": "object",
            "required": ["verifications"],
            "properties": {
                "verifications": {
                    "type": "array",
                    "items": self._get_response_schema()
                }
            }
        }
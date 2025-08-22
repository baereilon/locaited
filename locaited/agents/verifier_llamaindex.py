"""
LlamaIndex-based implementation of the Event Verifier.

Uses pattern matching and embeddings to classify events without LLM calls.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding

from locaited.agents.verifier import VerifierInterface, EventVerification

logger = logging.getLogger(__name__)


class VerifierLlamaIndex(VerifierInterface):
    """LlamaIndex-based verifier using pattern matching and embeddings."""
    
    def __init__(self):
        """Initialize LlamaIndex verifier with pattern indices."""
        logger.info("Initializing LlamaIndex-based verifier")
        
        # Configure LlamaIndex settings for efficiency
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
        Settings.chunk_size = 256
        
        # Build pattern indices
        self._build_specificity_index()
        self._build_temporality_index()
        
        # Compile regex patterns for extraction
        self._compile_patterns()
        
        logger.info("LlamaIndex verifier initialized with pattern indices")
    
    def _build_specificity_index(self):
        """Build index for specificity pattern matching."""
        specific_patterns = [
            # Specific events with date and location
            "Met Gala at Metropolitan Museum on May 5",
            "Climate March at Washington Square Park on August 24",
            "Fashion show at Spring Studios on September 10 at 3pm",
            "Mayor's press conference at City Hall on Monday",
            "Protest at Union Square this Tuesday at noon",
            "Art opening at MoMA on Friday evening",
            "Concert at Madison Square Garden on December 15",
            "Yankees game at Yankee Stadium tonight",
            "Festival in Central Park this weekend",
            "Book launch at Barnes & Noble Union Square on Thursday",
            
            # Specific - has both date and location indicators
            "SPECIFIC: Event has exact date like August 24 and venue like Madison Square Garden",
            "SPECIFIC: Event mentions specific day and specific location",
            "SPECIFIC: Includes when (date/day) and where (venue/address)",
        ]
        
        generic_patterns = [
            # Generic events lacking specificity
            "Fashion Week events",
            "Protests this week",
            "Cultural events in Manhattan",
            "Art exhibitions this month",
            "Upcoming concerts",
            "Political rallies",
            "Summer festivals",
            "Museum events",
            "Community gatherings",
            "Parades in NYC",
            
            # Generic - missing key details
            "GENERIC: Event lacks specific date or specific venue",
            "GENERIC: Only mentions general timeframe like 'this month'",
            "GENERIC: Only mentions general area like 'downtown'",
            "GENERIC: Vague event without concrete details",
        ]
        
        # Create documents
        specific_docs = [Document(text=f"SPECIFIC: {text}") for text in specific_patterns]
        generic_docs = [Document(text=f"GENERIC: {text}") for text in generic_patterns]
        
        # Build combined index
        all_docs = specific_docs + generic_docs
        self.specificity_index = VectorStoreIndex.from_documents(all_docs)
    
    def _build_temporality_index(self):
        """Build index for temporal pattern matching."""
        future_patterns = [
            # Future indicators
            "happening on August 24",
            "scheduled for next Tuesday",
            "will be held on September 10",
            "taking place this Friday",
            "coming up this weekend",
            "set for Monday",
            "planned for next month",
            "upcoming event on",
            "tickets available for",
            "RSVP for event on",
            
            # Future tense
            "FUTURE: Uses future tense like 'will be', 'happening on', 'scheduled for'",
            "FUTURE: Mentions specific future date",
            "FUTURE: Registration or tickets available",
        ]
        
        past_patterns = [
            # Past indicators
            "happened yesterday",
            "was held last week",
            "took place on Monday",
            "occurred earlier today",
            "already happened",
            "was attended by",
            "drew crowds of",
            "resulted in",
            "ended with",
            "concluded yesterday",
            
            # Past tense
            "PAST: Uses past tense like 'was', 'happened', 'took place'",
            "PAST: Already occurred before today",
            "PAST: Historical event that already happened",
        ]
        
        ongoing_patterns = [
            # Ongoing indicators
            "happening now",
            "currently underway",
            "all week long",
            "throughout the month",
            "continuing through",
            "runs until",
            "open through",
            "daily events",
            "every Tuesday",
            "recurring weekly",
            
            # Ongoing
            "ONGOING: Happening over a period including today",
            "ONGOING: Continuous or recurring event",
            "ONGOING: Multiple days or sessions",
        ]
        
        # Create documents
        future_docs = [Document(text=f"FUTURE: {text}") for text in future_patterns]
        past_docs = [Document(text=f"PAST: {text}") for text in past_patterns]
        ongoing_docs = [Document(text=f"ONGOING: {text}") for text in ongoing_patterns]
        
        # Build combined index
        all_docs = future_docs + past_docs + ongoing_docs
        self.temporality_index = VectorStoreIndex.from_documents(all_docs)
    
    def _compile_patterns(self):
        """Compile regex patterns for date and location extraction."""
        # Date patterns
        self.date_patterns = [
            # Month Day format
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\b',
            # Day of week
            r'\b(this|next)?\s*(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            # Relative dates
            r'\b(today|tomorrow|tonight|this weekend|next week)\b',
            # Numeric dates
            r'\b\d{1,2}/\d{1,2}(/\d{2,4})?\b',
        ]
        
        # Location patterns - NYC specific venues
        self.location_patterns = [
            # Major venues
            r'\b(Madison Square Garden|Barclays Center|Lincoln Center|Radio City)\b',
            r'\b(Metropolitan Museum|MoMA|Guggenheim|Whitney Museum)\b',
            r'\b(Central Park|Bryant Park|Washington Square|Union Square|Times Square)\b',
            r'\b(City Hall|Brooklyn Bridge|High Line|Chelsea Market)\b',
            # Generic venue indicators
            r'\bat\s+[A-Z][A-Za-z\s]+(Hall|Center|Museum|Park|Gallery|Theater|Stadium)\b',
            r'\bin\s+(Manhattan|Brooklyn|Queens|Bronx|Staten Island|Harlem|Chelsea|SoHo)\b',
        ]
        
        # Time patterns (bonus)
        self.time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(am|pm|AM|PM)?\b',
            r'\b(morning|afternoon|evening|night)\b',
            r'\b(noon|midnight)\b',
        ]
    
    def verify_event(self, event: Dict[str, Any]) -> EventVerification:
        """
        Verify a single event using pattern matching.
        
        Args:
            event: Event dictionary with at least 'description'
            
        Returns:
            EventVerification object with classification results
        """
        verification = EventVerification(event)
        description = event.get("description", "")
        
        # Extract date, location, time
        verification.has_date = self._has_date(description)
        verification.has_location = self._has_location(description)
        verification.has_time = self._has_time(description)
        
        # Determine specificity (needs both date AND location)
        verification.is_specific = verification.has_date and verification.has_location
        
        # Determine temporality using index
        verification.temporality = self._classify_temporality(description)
        
        # Calculate confidence based on pattern matching strength
        verification.confidence = self._calculate_confidence(
            verification.has_date,
            verification.has_location,
            verification.temporality
        )
        
        # Should keep if specific AND future
        verification.should_keep = (
            verification.is_specific and 
            verification.temporality == "FUTURE"
        )
        
        logger.debug(f"LlamaIndex verified: {description[:50]}... "
                    f"Specific: {verification.is_specific}, "
                    f"Temporal: {verification.temporality}")
        
        return verification
    
    def verify_batch(self, events: List[Dict[str, Any]]) -> List[EventVerification]:
        """
        Verify a batch of events.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of EventVerification objects
        """
        return [self.verify_event(event) for event in events]
    
    def _has_date(self, description: str) -> bool:
        """Check if description contains a date."""
        for pattern in self.date_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return True
        return False
    
    def _has_location(self, description: str) -> bool:
        """Check if description contains a location."""
        for pattern in self.location_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return True
        return False
    
    def _has_time(self, description: str) -> bool:
        """Check if description contains a time (bonus)."""
        for pattern in self.time_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return True
        return False
    
    def _classify_temporality(self, description: str) -> str:
        """
        Classify temporal nature of event using index similarity.
        
        Args:
            description: Event description
            
        Returns:
            FUTURE, PAST, ONGOING, or UNCLEAR
        """
        try:
            # Query the temporality index
            query_engine = self.temporality_index.as_query_engine(
                similarity_top_k=3,
                response_mode="no_text"  # We just want the nodes, not a response
            )
            
            response = query_engine.query(description)
            
            if not response.source_nodes:
                return "UNCLEAR"
            
            # Analyze top matches
            future_score = 0
            past_score = 0
            ongoing_score = 0
            
            for node in response.source_nodes:
                text = node.text.upper()
                score = node.score if hasattr(node, 'score') else 0.5
                
                if "FUTURE:" in text:
                    future_score += score
                elif "PAST:" in text:
                    past_score += score
                elif "ONGOING:" in text:
                    ongoing_score += score
            
            # Also check for explicit temporal indicators
            desc_lower = description.lower()
            
            # Strong future indicators
            if any(word in desc_lower for word in ["will be", "scheduled for", "upcoming", "next"]):
                future_score += 0.5
            
            # Strong past indicators
            if any(word in desc_lower for word in ["was", "happened", "took place", "occurred"]):
                past_score += 0.5
            
            # Strong ongoing indicators
            if any(word in desc_lower for word in ["happening now", "currently", "all week", "through"]):
                ongoing_score += 0.5
            
            # Determine classification
            if future_score > max(past_score, ongoing_score) and future_score > 0.3:
                return "FUTURE"
            elif past_score > max(future_score, ongoing_score) and past_score > 0.3:
                return "PAST"
            elif ongoing_score > max(future_score, past_score) and ongoing_score > 0.3:
                return "ONGOING"
            else:
                return "UNCLEAR"
                
        except Exception as e:
            logger.error(f"Temporality classification failed: {e}")
            return "UNCLEAR"
    
    def _calculate_confidence(self, has_date: bool, has_location: bool, temporality: str) -> float:
        """
        Calculate confidence score based on extraction results.
        
        Args:
            has_date: Whether date was found
            has_location: Whether location was found
            temporality: Temporal classification
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        if has_date:
            confidence += 0.2
        if has_location:
            confidence += 0.2
        if temporality != "UNCLEAR":
            confidence += 0.1
        
        return min(confidence, 1.0)
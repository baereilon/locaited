"""Database module for LocAIted."""

from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import hashlib
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.sql import func

from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    credentials_permits = Column(JSON)  # Store as JSON
    primary_location = Column(String(50), default="NYC")
    secondary_locations = Column(JSON)  # List of secondary cities
    interest_areas = Column(JSON)  # List of interest categories
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    recommendations = relationship("Recommendation", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    date = Column(DateTime)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String(255))
    summary = Column(Text)
    access_req = Column(String(100))  # open/press/permit
    organizer = Column(String(255))
    url = Column(String(500))
    source_urls = Column(JSON)  # List of source URLs
    dedupe_fingerprint = Column(String(64), unique=True)  # SHA256 hash
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recommendations = relationship("Recommendation", back_populates="event")
    
    @staticmethod
    def generate_fingerprint(title: str, start_time: datetime, organizer: str) -> str:
        """Generate deduplication fingerprint."""
        data = f"{title}|{start_time}|{organizer}".lower()
        return hashlib.sha256(data.encode()).hexdigest()

class Recommendation(Base):
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    confidence = Column(Float)  # 0.0 to 1.0
    reasoning = Column(Text)  # Why recommended (≤350 chars)
    query = Column(Text)  # Original query that generated this
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    event = relationship("Event", back_populates="recommendations")
    feedback = relationship("Feedback", back_populates="recommendation", uselist=False)

class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    recommendation_id = Column(Integer, ForeignKey('recommendations.id'))
    thumbs = Column(String(10))  # 'up' or 'down'
    attended = Column(Boolean)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    recommendation = relationship("Recommendation", back_populates="feedback")

# Additional tracking tables (simplified for MVP)
class QueryCache(Base):
    """Simple cache for queries."""
    __tablename__ = 'query_cache'
    
    id = Column(Integer, primary_key=True)
    cache_key = Column(String(64), unique=True)  # Hash of query params
    query = Column(Text)
    filters = Column(JSON)
    result_event_ids = Column(JSON)  # List of event IDs
    total_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_cache_key(query: str, filters: dict, model: str = "gpt-3.5-turbo") -> str:
        """Generate cache key from query parameters."""
        data = json.dumps({"query": query, "filters": filters, "model": model}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

# Database setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DATABASE_URL}")

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def create_user(db: Session, name: str, email: str, **kwargs) -> User:
    """Create a new user."""
    user = User(name=name, email=email, **kwargs)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_or_create_event(db: Session, event_data: dict) -> Event:
    """Get existing event or create new one."""
    # Generate fingerprint
    fingerprint = Event.generate_fingerprint(
        event_data.get('title', ''),
        event_data.get('start_time', datetime.now()),
        event_data.get('organizer', '')
    )
    
    # Check if exists
    existing = db.query(Event).filter_by(dedupe_fingerprint=fingerprint).first()
    if existing:
        # Update if new data
        for key, value in event_data.items():
            if hasattr(existing, key) and value is not None:
                setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        db.commit()
        return existing
    
    # Create new
    event_data['dedupe_fingerprint'] = fingerprint
    event = Event(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def create_recommendation(db: Session, user_id: int, event_id: int, 
                         confidence: float, reasoning: str, query: str) -> Recommendation:
    """Create a recommendation."""
    rec = Recommendation(
        user_id=user_id,
        event_id=event_id,
        confidence=confidence,
        reasoning=reasoning[:350],  # Enforce limit
        query=query
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def add_feedback(db: Session, user_id: int, recommendation_id: int, 
                thumbs: str, attended: bool = None, notes: str = None) -> Feedback:
    """Add user feedback."""
    feedback = Feedback(
        user_id=user_id,
        recommendation_id=recommendation_id,
        thumbs=thumbs,
        attended=attended,
        notes=notes
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback

def check_cache(db: Session, query: str, filters: dict, model: str = "gpt-3.5-turbo") -> Optional[List[int]]:
    """Check if query results are cached."""
    cache_key = QueryCache.generate_cache_key(query, filters, model)
    cached = db.query(QueryCache).filter_by(cache_key=cache_key).first()
    if cached:
        return cached.result_event_ids
    return None

def save_to_cache(db: Session, query: str, filters: dict, event_ids: List[int], 
                 cost: float, model: str = "gpt-3.5-turbo"):
    """Save query results to cache."""
    cache_key = QueryCache.generate_cache_key(query, filters, model)
    cache_entry = QueryCache(
        cache_key=cache_key,
        query=query,
        filters=filters,
        result_event_ids=event_ids,
        total_cost=cost
    )
    db.add(cache_entry)
    db.commit()

# Test function
def test_database():
    """Test database operations."""
    init_db()
    db = next(get_db())
    
    # Create test user
    user = create_user(
        db, 
        name="Test User",
        email="test@example.com",
        primary_location="NYC",
        interest_areas=["protests", "cultural", "political"]
    )
    print(f"Created user: {user.name}")
    
    # Create test event
    event_data = {
        'title': "Test Event",
        'start_time': datetime.now(),
        'location': "NYC",
        'organizer': "Test Org",
        'summary': "Test event description"
    }
    event = get_or_create_event(db, event_data)
    print(f"Created event: {event.title}")
    
    # Create recommendation
    rec = create_recommendation(
        db,
        user_id=user.id,
        event_id=event.id,
        confidence=0.85,
        reasoning="Matches your interest in cultural events in NYC",
        query="cultural events NYC"
    )
    print(f"Created recommendation with confidence: {rec.confidence}")
    
    db.close()
    print("Database test complete!")

if __name__ == "__main__":
    test_database()
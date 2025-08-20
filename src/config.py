"""Configuration module for LocAIted v0.4.0.

Centralized configuration for all components.
"""

import os
from pathlib import Path

# Project Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEST_DATA_PATH = PROJECT_ROOT / "test data" / "Liri Interesting events.csv"
CACHE_DIR = PROJECT_ROOT / "cache" / "v0.4.0"
BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks" / "results" / "v0.4.0"

# API Keys (loaded from environment)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI Configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_TEMPERATURE = 1.0  # gpt-4.1-mini only supports 1.0
OPENAI_MAX_TOKENS_DEFAULT = 2000
OPENAI_MAX_TOKENS_EXTRACT = 2500  # For Publisher extraction
OPENAI_MAX_TOKENS_DECISION = 1500  # For gate decisions

# Cost Management
MAX_COST_PER_QUERY = float(os.getenv("MAX_COST_PER_QUERY", "0.10"))
COST_PER_1K_TOKENS_INPUT = 0.00015   # $0.15 per 1M input tokens
COST_PER_1K_TOKENS_OUTPUT = 0.0006   # $0.60 per 1M output tokens

# Tavily Configuration
TAVILY_SEARCH_DEPTH = "basic"  # basic or advanced
TAVILY_MAX_RESULTS = 10  # Results per search
TAVILY_MAX_SEARCHES = 25  # Maximum searches per workflow run
TAVILY_COST_PER_SEARCH = 0.001  # $0.001 per search

# Workflow Configuration
MAX_RETRY_ITERATIONS = 3
MIN_EVENTS_FOR_APPROVAL = 5
MAX_EVENTS_TO_RETURN = 15  # Publisher output limit
TOP_EVENTS_FOR_GATE = 10  # Number of top events to show in gate decision

# Agent Configuration
RESEARCHER_LEADS_COUNT = 25
FACT_CHECKER_BATCH_SIZE = 25  # Process all leads
PUBLISHER_DEDUP_THRESHOLD = 0.8  # Similarity threshold for deduplication

# Cache Configuration
CACHE_ENABLED = True
CACHE_TTL_SECONDS = 3600  # 1 hour
CACHE_MAX_SIZE_MB = 100  # Maximum cache size

# Query Defaults
DEFAULT_LOCATION = "New York City"
DEFAULT_TIME_FRAME = "next 2 weeks"
DEFAULT_INTERESTS = ["protests", "cultural events", "political events"]

# Validation Configuration
VALIDATION_QUERY = {
    "location": DEFAULT_LOCATION,
    "time_frame": DEFAULT_TIME_FRAME,
    "interests": ["protests", "cultural events", "political events", "parades", "art exhibitions"]
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Database (for future use)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///locaited.db")

# Validate required configuration
def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    if not TAVILY_API_KEY:
        errors.append("TAVILY_API_KEY not found in environment variables")
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not found in environment variables")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))

# Validate on import
try:
    validate_config()
except ValueError:
    # Allow import to succeed for documentation purposes
    # but actual usage will fail
    pass
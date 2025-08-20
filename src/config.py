"""Configuration module for LocAIted."""

import os
from pathlib import Path

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///locaited.db")

# Cost Management
MAX_COST_PER_QUERY = float(os.getenv("MAX_COST_PER_QUERY", "0.10"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEST_DATA_PATH = PROJECT_ROOT / "test data" / "Liri Interesting events.csv"

# Query Defaults
DEFAULT_CITY = "NYC"
DEFAULT_DATE_RANGE_DAYS = 14
DEFAULT_MAX_RESULTS = 20

# Tavily Settings
TAVILY_SEARCH_DEPTH = "basic"  # basic or advanced
TAVILY_MAX_RESULTS = 15
TAVILY_EXTRACT_MAX_URLS = 8  # To stay within budget

# Cache Settings
CACHE_ENABLED = True
CACHE_TTL_SECONDS = 3600  # 1 hour

# Validate required keys
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in environment variables")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
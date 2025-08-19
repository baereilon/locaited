"""Main entry point for testing LocAIted system."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import *

def main():
    print("LocAIted - Multi-Agent Event Discovery System")
    print("=" * 50)
    print(f"Configuration loaded:")
    print(f"  - Database: {DATABASE_URL}")
    print(f"  - OpenAI Model: {OPENAI_MODEL}")
    print(f"  - Max Cost per Query: ${MAX_COST_PER_QUERY}")
    print(f"  - Test Data Path: {TEST_DATA_PATH}")
    print(f"  - Tavily API Key: {'✓' if TAVILY_API_KEY else '✗'}")
    print(f"  - OpenAI API Key: {'✓' if OPENAI_API_KEY else '✗'}")
    print()
    
    # Placeholder for agent testing
    print("Ready to implement agents...")

if __name__ == "__main__":
    main()
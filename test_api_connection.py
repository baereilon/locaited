"""Test API connections and environment setup for LocAIted.

This script verifies:
1. Environment variables are loaded correctly
2. OpenAI API connection works
3. Basic LLM functionality
"""

import os
import logging
from src.utils.llm_client import get_llm_client

logging.basicConfig(level=logging.INFO)

def test_environment():
    """Check environment variables."""
    print("=" * 60)
    print("ENVIRONMENT CHECK")
    print("=" * 60)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')
    model = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
    
    print(f"OPENAI_API_KEY: {'✓ Configured' if openai_key else '✗ Missing'}")
    print(f"TAVILY_API_KEY: {'✓ Configured' if tavily_key else '✗ Missing'}")
    print(f"OPENAI_MODEL: {model}")
    
    return bool(openai_key and tavily_key)

def test_llm_connection():
    """Test OpenAI API connection."""
    print("\n" + "=" * 60)
    print("LLM CONNECTION TEST")
    print("=" * 60)
    
    try:
        client = get_llm_client()
        response = client.complete(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello, World!' in JSON format with a 'message' field.",
            max_tokens=50,
            temperature=1.0
        )
        print(f"Response: {response['content']}")
        print(f"Cost: ${response['cost']:.6f}")
        print(f"Model: {response['model']}")
        print("✓ LLM connection successful")
        return True
    except Exception as e:
        print(f"✗ LLM connection failed: {e}")
        return False

def main():
    """Run all connection tests."""
    print("LOCAITED API CONNECTION TEST")
    print("=" * 60)
    
    env_ok = test_environment()
    llm_ok = test_llm_connection() if env_ok else False
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Environment: {'✓ Pass' if env_ok else '✗ Fail'}")
    print(f"LLM Connection: {'✓ Pass' if llm_ok else '✗ Fail'}")
    
    if env_ok and llm_ok:
        print("\n✓ All tests passed - ready to run LocAIted")
        return 0
    else:
        print("\n✗ Some tests failed - check configuration")
        return 1

if __name__ == "__main__":
    exit(main())
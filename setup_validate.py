"""Validation script for LocAIted setup."""

import sys
import os

def validate_setup():
    """Validate the LocAIted installation."""
    errors = []
    warnings = []
    
    # 1. Test imports
    print("Testing imports...")
    try:
        from src.agents.workflow_v4 import WorkflowV4
        from src.utils.llm_client import get_llm_client
        from src.utils.tavily_client import TavilyClient
        print("✅ All imports successful")
    except ImportError as e:
        errors.append(f"Import failed: {e}")
        print(f"❌ Import failed: {e}")
    
    # 2. Check API keys (without loading them into environment)
    print("\nChecking API keys...")
    if os.path.exists('.env.secret'):
        with open('.env.secret', 'r') as f:
            content = f.read()
            
        # Check for OpenAI key
        if 'OPENAI_API_KEY=' in content:
            lines = [l for l in content.split('\n') if l.startswith('OPENAI_API_KEY=')]
            if lines and lines[0].split('=', 1)[1].strip():
                print("✅ OPENAI_API_KEY configured")
            else:
                warnings.append("OPENAI_API_KEY is empty in .env.secret")
                print("⚠️  OPENAI_API_KEY is empty")
        else:
            warnings.append("OPENAI_API_KEY not found in .env.secret")
            print("⚠️  OPENAI_API_KEY not found")
        
        # Check for Tavily key
        if 'TAVILY_API_KEY=' in content:
            lines = [l for l in content.split('\n') if l.startswith('TAVILY_API_KEY=')]
            if lines and lines[0].split('=', 1)[1].strip():
                print("✅ TAVILY_API_KEY configured")
            else:
                warnings.append("TAVILY_API_KEY is empty in .env.secret")
                print("⚠️  TAVILY_API_KEY is empty")
        else:
            warnings.append("TAVILY_API_KEY not found in .env.secret")
            print("⚠️  TAVILY_API_KEY not found")
    else:
        warnings.append(".env.secret file not found")
        print("⚠️  .env.secret file not found")
    
    # 3. Check cache directory
    print("\nChecking cache directory...")
    if os.path.exists('cache/v0.4.0'):
        print("✅ Cache directory exists")
    else:
        warnings.append("Cache directory not found")
        print("⚠️  Cache directory not found")
    
    # 4. Summary
    print("\n" + "="*40)
    if errors:
        print("❌ Setup validation FAILED")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    elif warnings:
        print("⚠️  Setup complete with warnings:")
        for warning in warnings:
            print(f"   - {warning}")
        if any("API_KEY" in w for w in warnings):
            print("\n   Add your API keys to .env.secret to use LocAIted")
    else:
        print("✅ Setup validation PASSED")
    
    return len(errors) == 0

if __name__ == "__main__":
    validate_setup()
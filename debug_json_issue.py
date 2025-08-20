"""Debug script to identify JSON parsing issue with gpt-5-mini."""

import os
import logging
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_api():
    """Test OpenAI API directly."""
    print("\n=== Testing Direct OpenAI API ===")
    client = OpenAI()
    
    try:
        response = client.chat.completions.create(
            model='gpt-5-mini',
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant. Respond with JSON.'},
                {'role': 'user', 'content': 'Give me a JSON object with a greeting field'}
            ],
            response_format={'type': 'json_object'},
            max_completion_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"Response content: {content}")
        print(f"Content type: {type(content)}")
        print(f"Content length: {len(content) if content else 0}")
        
        if content:
            import json
            parsed = json.loads(content)
            print(f"Parsed JSON: {parsed}")
        else:
            print("ERROR: Empty response from API")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_llm_client():
    """Test our LLM client wrapper."""
    print("\n=== Testing LLM Client ===")
    from src.utils.llm_client import get_llm_client
    
    client = get_llm_client(model="gpt-5-mini", temperature=1.0)
    
    try:
        response = client.complete_json(
            system_prompt="You are a helpful assistant",
            user_prompt="Give me a JSON object with a test field",
            max_tokens=100
        )
        print(f"Success! Parsed content: {response['parsed_content']}")
    except Exception as e:
        print(f"Error: {e}")

def test_editor():
    """Test Editor agent."""
    print("\n=== Testing Editor Agent ===")
    from src.agents.editor_v4 import EditorV4
    
    editor = EditorV4()
    state = {
        'user_input': {
            'location': 'NYC',
            'time_frame': 'this week',
            'interests': ['protests']
        }
    }
    
    try:
        result = editor.process(state)
        print(f"Success! Profile: {result.get('profile')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Debugging JSON issue with gpt-5-mini")
    print("=" * 50)
    
    # Check model is set correctly
    print(f"OPENAI_MODEL from env: {os.getenv('OPENAI_MODEL')}")
    
    # Run tests
    test_direct_api()
    test_llm_client()
    test_editor()
"""LLM Client wrapper for GPT-4.1-mini with cost tracking and error handling."""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import time

from openai import OpenAI
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with GPT-4.1-mini API."""
    
    # Cost per 1K tokens (as of 2025)
    MODEL_COSTS = {
        "gpt-4.1-mini": {
            "input": 0.00015,   # $0.15 per 1M input tokens
            "output": 0.0006    # $0.60 per 1M output tokens
        }
    }
    
    def __init__(self, model: str = "gpt-4.1-mini", temperature: float = 0.7):
        """Initialize LLM client.
        
        Args:
            model: Model name (default: gpt-4.1-mini)
            temperature: Temperature for generation (0-1)
        """
        self.model = model
        self.temperature = temperature
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        
        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0
        
        # Error tracking
        self.errors = []
        
        logger.info(f"LLMClient initialized with model: {model}")
    
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """Send completion request to LLM.
        
        Args:
            system_prompt: System message setting context
            user_prompt: User message with the request
            max_tokens: Maximum tokens in response
            temperature: Override default temperature
            response_format: JSON schema for structured output
            retry_count: Number of retries on failure
            
        Returns:
            Dictionary with response, tokens, and cost info
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        temp = temperature if temperature is not None else self.temperature
        
        # Build request parameters
        params = {
            "model": self.model,
            "messages": messages
        }
        
        # Only add temperature if not default (1.0)
        if temp != 1.0:
            params["temperature"] = temp
        
        if max_tokens:
            params["max_completion_tokens"] = max_tokens
            
        if response_format:
            params["response_format"] = response_format
        
        # Retry logic
        last_error = None
        for attempt in range(retry_count):
            try:
                start_time = time.time()
                
                # Make API call
                response: ChatCompletion = self.client.chat.completions.create(**params)
                
                elapsed = time.time() - start_time
                
                # Extract response data
                content = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                
                # Calculate cost
                cost = self._calculate_cost(input_tokens, output_tokens)
                
                # Update tracking
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                self.total_cost += cost
                self.request_count += 1
                
                logger.info(
                    f"LLM completion: {total_tokens} tokens, "
                    f"${cost:.6f} cost, {elapsed:.2f}s"
                )
                
                return {
                    "content": content,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "elapsed_time": elapsed,
                    "model": self.model
                }
                
            except Exception as e:
                last_error = e
                self.errors.append({
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "attempt": attempt + 1
                })
                
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"LLM request failed (attempt {attempt + 1}/{retry_count}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"LLM request failed after {retry_count} attempts: {e}")
        
        # All retries failed
        raise Exception(f"LLM request failed after {retry_count} attempts: {last_error}")
    
    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get JSON response from LLM.
        
        Args:
            system_prompt: System message
            user_prompt: User message
            schema: Optional JSON schema for validation
            **kwargs: Additional arguments for complete()
            
        Returns:
            Parsed JSON response
        """
        # Add JSON instruction to prompts
        system_prompt = f"{system_prompt}\n\nYou must respond with valid JSON."
        
        # Set response format if schema provided
        if schema:
            kwargs["response_format"] = {"type": "json_object"}
        
        result = self.complete(system_prompt, user_prompt, **kwargs)
        
        try:
            # Strip markdown code blocks if present
            content = result["content"].strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            elif content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()
            
            # Parse JSON response
            json_content = json.loads(content)
            
            # Validate against schema if provided
            if schema:
                # Basic validation (could use jsonschema library for full validation)
                required_keys = schema.get("required", [])
                for key in required_keys:
                    if key not in json_content:
                        raise ValueError(f"Missing required key: {key}")
            
            result["parsed_content"] = json_content
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw content: {result['content']}")
            raise ValueError(f"LLM did not return valid JSON: {e}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Total cost in dollars
        """
        if self.model not in self.MODEL_COSTS:
            logger.warning(f"Unknown model {self.model}, using gpt-4.1-mini costs")
            costs = self.MODEL_COSTS["gpt-4.1-mini"]
        else:
            costs = self.MODEL_COSTS[self.model]
        
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "model": self.model,
            "request_count": self.request_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": self.total_cost,
            "avg_cost_per_request": (
                self.total_cost / self.request_count 
                if self.request_count > 0 else 0
            ),
            "error_count": len(self.errors),
            "recent_errors": self.errors[-5:] if self.errors else []
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0
        self.errors = []
        logger.info("LLMClient metrics reset")
    
    def batch_complete(
        self,
        requests: List[Dict[str, str]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Process multiple completion requests.
        
        Args:
            requests: List of dicts with 'system' and 'user' prompts
            **kwargs: Additional arguments for complete()
            
        Returns:
            List of responses
        """
        results = []
        
        for i, request in enumerate(requests):
            logger.info(f"Processing batch request {i+1}/{len(requests)}")
            
            try:
                result = self.complete(
                    system_prompt=request.get("system", ""),
                    user_prompt=request["user"],
                    **kwargs
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch request {i+1} failed: {e}")
                results.append({
                    "error": str(e),
                    "content": None,
                    "cost": 0
                })
        
        return results
    
    def __str__(self) -> str:
        """String representation."""
        return (f"LLMClient(model={self.model}, "
                f"requests={self.request_count}, "
                f"cost=${self.total_cost:.4f})")
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"LLMClient(model={self.model}, "
                f"temperature={self.temperature}, "
                f"requests={self.request_count}, "
                f"tokens={self.total_input_tokens + self.total_output_tokens}, "
                f"cost=${self.total_cost:.4f})")


# Singleton instance for shared use
_default_client = None

def get_llm_client(model: str = "gpt-4.1-mini", temperature: float = 0.7) -> LLMClient:
    """Get or create default LLM client.
    
    Args:
        model: Model name
        temperature: Temperature setting
        
    Returns:
        LLMClient instance
    """
    global _default_client
    
    if _default_client is None:
        _default_client = LLMClient(model=model, temperature=temperature)
    
    return _default_client
"""Base agent class with shared functionality for all agents."""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the LocAIted system."""
    
    def __init__(self, name: str, use_cache: bool = True):
        """Initialize base agent.
        
        Args:
            name: Agent name for logging and identification
            use_cache: Whether to use caching for API calls
        """
        self.name = name
        self.use_cache = use_cache
        self.logger = logging.getLogger(f"locaited.{name}")
        
        # Cost tracking
        self.last_cost = 0.0
        self.total_cost = 0.0
        
        # Performance tracking
        self.last_execution_time = 0.0
        self.execution_count = 0
        
        # Error tracking
        self.errors: List[str] = []
        
        self.logger.info(f"{self.name} agent initialized")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method that each agent must implement.
        
        Args:
            input_data: Input data specific to each agent
            
        Returns:
            Output data specific to each agent
        """
        pass
    
    def log_info(self, message: str):
        """Log info message with agent name prefix."""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str, error: Optional[Exception] = None):
        """Log error message and track it.
        
        Args:
            message: Error message
            error: Optional exception object
        """
        error_msg = f"[{self.name}] ERROR: {message}"
        if error:
            error_msg += f" - {str(error)}"
        
        self.logger.error(error_msg)
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "error": str(error) if error else None
        })
    
    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(f"[{self.name}] WARNING: {message}")
    
    def track_cost(self, cost: float, operation: str = ""):
        """Track API costs.
        
        Args:
            cost: Cost in dollars
            operation: Optional description of the operation
        """
        self.last_cost = cost
        self.total_cost += cost
        
        if operation:
            self.log_info(f"Cost for {operation}: ${cost:.6f}")
        else:
            self.log_info(f"Operation cost: ${cost:.6f}")
    
    def track_execution_time(self, start_time: datetime):
        """Track execution time for performance monitoring.
        
        Args:
            start_time: When the operation started
        """
        elapsed = (datetime.now() - start_time).total_seconds()
        self.last_execution_time = elapsed
        self.execution_count += 1
        
        self.log_info(f"Execution time: {elapsed:.2f}s")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "agent": self.name,
            "total_cost": self.total_cost,
            "last_cost": self.last_cost,
            "execution_count": self.execution_count,
            "last_execution_time": self.last_execution_time,
            "avg_execution_time": (
                self.last_execution_time / self.execution_count 
                if self.execution_count > 0 else 0
            ),
            "error_count": len(self.errors),
            "errors": self.errors[-5:] if self.errors else []  # Last 5 errors
        }
    
    def reset_metrics(self):
        """Reset all metrics for fresh run."""
        self.last_cost = 0.0
        self.total_cost = 0.0
        self.last_execution_time = 0.0
        self.execution_count = 0
        self.errors = []
        
        self.log_info("Metrics reset")
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that input has required fields.
        
        Args:
            input_data: Input dictionary to validate
            required_fields: List of required field names
            
        Returns:
            True if valid, False otherwise
        """
        missing_fields = []
        for field in required_fields:
            if field not in input_data or input_data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            self.log_error(f"Missing required fields: {missing_fields}")
            return False
        
        return True
    
    def save_debug_output(self, data: Any, filename_prefix: str):
        """Save debug output for inspection.
        
        Args:
            data: Data to save
            filename_prefix: Prefix for the filename
        """
        from locaited.config import PROJECT_ROOT
        
        debug_dir = PROJECT_ROOT / "debug" / self.name.lower()
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = debug_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.log_info(f"Debug output saved to: {filepath.name}")
        except Exception as e:
            self.log_error(f"Failed to save debug output: {e}")
    
    def __str__(self) -> str:
        """String representation of agent."""
        return f"{self.name}Agent(cost=${self.total_cost:.4f}, executions={self.execution_count})"
    
    def __repr__(self) -> str:
        """Detailed representation of agent."""
        return (f"{self.name}Agent("
                f"total_cost=${self.total_cost:.4f}, "
                f"executions={self.execution_count}, "
                f"errors={len(self.errors)})")


class CachedAgent(BaseAgent):
    """Base agent with caching support."""
    
    def __init__(self, name: str, use_cache: bool = True, cache_ttl: int = 3600):
        """Initialize cached agent.
        
        Args:
            name: Agent name
            use_cache: Whether to use caching
            cache_ttl: Cache time-to-live in seconds
        """
        super().__init__(name, use_cache)
        self.cache_ttl = cache_ttl
        
        if self.use_cache:
            self._init_cache()
    
    def _init_cache(self):
        """Initialize cache directory for this agent."""
        from locaited.config import PROJECT_ROOT
        
        self.cache_dir = PROJECT_ROOT / "cache" / "v0.4.0" / self.name.lower()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create index file if it doesn't exist
        self.cache_index_file = self.cache_dir / "index.json"
        if not self.cache_index_file.exists():
            with open(self.cache_index_file, 'w') as f:
                json.dump({}, f)
    
    def get_cache_key(self, **kwargs) -> str:
        """Generate cache key from parameters.
        
        Args:
            **kwargs: Parameters to hash
            
        Returns:
            Cache key string
        """
        import hashlib
        
        # Sort keys for consistent hashing
        sorted_items = sorted(kwargs.items())
        key_string = json.dumps(sorted_items, sort_keys=True, default=str)
        
        # Create hash
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if available and not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        if not self.use_cache:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            age = (datetime.now() - cached_time).total_seconds()
            
            if age > self.cache_ttl:
                self.log_info(f"Cache expired for key {cache_key[:8]}...")
                return None
            
            self.log_info(f"Cache hit for key {cache_key[:8]}... (age: {age:.0f}s)")
            return cache_data['data']
            
        except Exception as e:
            self.log_error(f"Error reading cache: {e}")
            return None
    
    def save_to_cache(self, cache_key: str, data: Any):
        """Save data to cache.
        
        Args:
            cache_key: Cache key
            data: Data to cache
        """
        if not self.use_cache:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            # Update index
            self._update_cache_index(cache_key, data)
            
            self.log_info(f"Saved to cache: {cache_key[:8]}...")
            
        except Exception as e:
            self.log_error(f"Error saving to cache: {e}")
    
    def _update_cache_index(self, cache_key: str, data: Any):
        """Update cache index for quick lookups.
        
        Args:
            cache_key: Cache key
            data: Cached data (for metadata extraction)
        """
        try:
            with open(self.cache_index_file, 'r') as f:
                index = json.load(f)
            
            # Add metadata about this cache entry
            index[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'type': type(data).__name__,
                'size': len(json.dumps(data, default=str))
            }
            
            with open(self.cache_index_file, 'w') as f:
                json.dump(index, f, indent=2)
                
        except Exception as e:
            self.log_error(f"Error updating cache index: {e}")
    
    def clear_cache(self):
        """Clear all cache for this agent."""
        if not self.use_cache:
            return
        
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self._init_cache()
            self.log_info("Cache cleared")
        except Exception as e:
            self.log_error(f"Error clearing cache: {e}")
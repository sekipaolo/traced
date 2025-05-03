"""Thread-local storage for trace context."""

import threading
from typing import Optional


class TraceContext:
    """
    Thread-local storage for trace context.
    
    This class provides a way to maintain trace context across method
    calls without passing it explicitly.
    """
    
    # Thread-local storage
    _local = threading.local()
    
    @classmethod
    def get_current_trace_id(cls) -> Optional[str]:
        """
        Get the current trace ID if it exists.
        
        Returns:
            Current trace ID or None if not set
        """
        if not hasattr(cls._local, "trace_id"):
            return None
        return cls._local.trace_id
    
    @classmethod
    def set_current_trace_id(cls, trace_id: str) -> None:
        """
        Set the current trace ID.
        
        Args:
            trace_id: Trace ID to set
        """
        cls._local.trace_id = trace_id
    
    @classmethod
    def get_current_parent_id(cls) -> Optional[str]:
        """
        Get the current parent execution ID if it exists.
        
        Returns:
            Current parent ID or None if not set
        """
        if not hasattr(cls._local, "parent_id"):
            return None
        return cls._local.parent_id
    
    @classmethod
    def set_current_parent_id(cls, parent_id: str) -> None:
        """
        Set the current parent execution ID.
        
        Args:
            parent_id: Parent ID to set
        """
        cls._local.parent_id = parent_id
    
    @classmethod
    def clear(cls) -> None:
        """Clear the current context."""
        if hasattr(cls._local, "trace_id"):
            delattr(cls._local, "trace_id")
        if hasattr(cls._local, "parent_id"):
            delattr(cls._local, "parent_id")
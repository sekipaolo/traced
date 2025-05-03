"""Base traced class and configuration utilities."""

import uuid
import time
import functools
import logging
import inspect
from typing import Dict, Any, Optional, Callable, List, Type

from traced.core.context import TraceContext
from traced.core.events import TraceEvent, Artifact

# Set up logging
logger = logging.getLogger("traced.core")

# Global storage instance and factory function
_trace_storage = None


def _get_trace_storage():
    """
    Get the configured trace storage backend.
    
    Raises:
        RuntimeError: If no storage backend is configured
    """
    global _trace_storage
    if _trace_storage is None:
        # Lazy import to avoid circular dependencies
        from traced.storage.memory import InMemoryTraceStorage
        _trace_storage = InMemoryTraceStorage()
        logger.info("No storage configured, using in-memory storage")
    return _trace_storage

def configure_tracing(storage_type: str = "memory", **kwargs) -> None:
    """
    Configure the global tracing storage.
    
    This function must be called before using any tracing functionality,
    otherwise an in-memory storage backend will be used by default.
    
    Args:
        storage_type: Type of storage to use ("memory", "mongodb", "sql", "sqlite")
        **kwargs: Additional configuration for the storage backend
        
    Raises:
        ValueError: If the storage type is unknown
        ImportError: If the required dependencies are not installed
    """
    global _trace_storage
    
    if storage_type == "memory":
        from traced.storage.memory import InMemoryTraceStorage
        _trace_storage = InMemoryTraceStorage()
    elif storage_type == "mongodb":
        from traced.storage.mongodb import MongoDBTraceStorage
        _trace_storage = MongoDBTraceStorage(**kwargs)
    elif storage_type == "sqlite":
        from traced.storage.sqlite import SQLiteTraceStorage
        _trace_storage = SQLiteTraceStorage(**kwargs)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
    
    logger.info(f"Configured tracing with storage type: {storage_type}")

class Traced:
    """
    Base class that provides tracing capabilities.
    
    Simply inherit from this class and all public methods will be
    automatically traced!
    
    Class attributes:
        TRACED_EXCLUDE: List of method names to exclude from tracing
        TRACED_RECORD_PARAMS: Whether to record method parameters
        TRACED_RECORD_RESULTS: Whether to record method results
    """
    
    # Class-level configuration
    TRACED_EXCLUDE: List[str] = []  # Methods to exclude from tracing
    TRACED_RECORD_PARAMS: bool = True  # Whether to record method parameters
    TRACED_RECORD_RESULTS: bool = True  # Whether to record method results
    
    def __init__(
        self,
        name: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ):
        """
        Initialize the traced object.
        
        Args:
            name: Name for this traced object (defaults to class name)
            trace_id: ID for the trace (generated if not provided)
            parent_id: ID of the parent execution (None for root)
        """
        # Use class name if no name provided
        self.name = name or self.__class__.__name__
        
        # Get current context or create new
        current_trace_id = TraceContext.get_current_trace_id()
        current_parent_id = TraceContext.get_current_parent_id()
        
        # Set trace context
        self.trace_id = trace_id or current_trace_id or self._generate_id()
        
        # If parent_id is provided, use it
        # Otherwise, if we're continuing an existing trace, the current execution becomes the parent
        if parent_id is not None:
            self.parent_id = parent_id
        elif current_trace_id is not None and current_parent_id is not None:
            self.parent_id = current_parent_id
        else:
            self.parent_id = None
            
        # Generate unique execution ID
        self.execution_id = self._generate_id()
        
        # Log initialization
        logger.debug(
            f"Initialized {self.name} with trace_id={self.trace_id}, "
            f"execution_id={self.execution_id}, parent_id={self.parent_id}"
        )
        
        # Wrap public methods with tracing
        self._wrap_methods()
    
    def _generate_id(self) -> str:
        """
        Generate a unique ID.
        
        Returns:
            Unique ID string
        """
        return str(uuid.uuid4())
    
    def _wrap_methods(self) -> None:
        """Automatically wrap public methods with tracing."""
        # Look at all attributes of the class
        for attr_name in dir(self.__class__):
            # Skip private methods and excluded methods
            if attr_name.startswith('_') or attr_name in self.TRACED_EXCLUDE:
                continue
            
            attr = getattr(self.__class__, attr_name)
            
            # Only wrap callable methods that haven't been wrapped yet
            if (inspect.isfunction(attr) or inspect.ismethod(attr)) and not hasattr(attr, '_traced'):
                # Check if the method is explicitly marked as not to be traced
                if hasattr(attr, '_not_traced'):
                    logger.debug(f"Skipping method {attr_name} marked as not_traced")
                    continue
                
                # Get the original method
                original_method = attr
                
                # Create a wrapped method
                @functools.wraps(original_method)
                def traced_method(self, *args, **kwargs):
                    # Update trace context for this execution
                    previous_trace_id = TraceContext.get_current_trace_id()
                    previous_parent_id = TraceContext.get_current_parent_id()
                    
                    TraceContext.set_current_trace_id(self.trace_id)
                    TraceContext.set_current_parent_id(self.execution_id)
                    
                    try:
                        # Start tracing the method
                        if self.TRACED_RECORD_PARAMS:
                            self._start_trace(original_method.__name__, args, kwargs)
                        else:
                            self._start_trace(original_method.__name__)
                        
                        # Execute the original method
                        result = original_method(self, *args, **kwargs)
                        
                        # End trace successfully
                        if self.TRACED_RECORD_RESULTS:
                            self._end_trace(original_method.__name__, result=result)
                        else:
                            self._end_trace(original_method.__name__)
                        
                        return result
                    except Exception as e:
                        # End trace with error
                        self._end_trace(original_method.__name__, error=e)
                        raise
                    finally:
                        # Restore previous context
                        if previous_trace_id:
                            TraceContext.set_current_trace_id(previous_trace_id)
                        if previous_parent_id:
                            TraceContext.set_current_parent_id(previous_parent_id)
                
                # Mark as traced
                traced_method._traced = True
                
                # Replace the original method
                setattr(self.__class__, attr_name, traced_method)
                logger.debug(f"Wrapped method {attr_name} for tracing")
    
    def _start_trace(
        self,
        method_name: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None
    ) -> None:
        """
        Start tracing a method execution.
        
        Args:
            method_name: Name of the method
            args: Method arguments
            kwargs: Method keyword arguments
        """
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Prepare event data
        data = {}
        if args is not None:
            data["args"] = args
        if kwargs is not None:
            data["kwargs"] = kwargs
        
        # Create trace event
        event = TraceEvent(
            trace_id=self.trace_id,
            execution_id=self.execution_id,
            parent_id=self.parent_id,
            agent_name=self.name,
            method_name=method_name,
            event_type="start",
            timestamp=time.time(),
            data=data
        )
        
        # Save trace event
        storage.save_trace_event(event)
    
    def _end_trace(
        self,
        method_name: str,
        result: Any = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        End tracing a method execution.
        
        Args:
            method_name: Name of the method
            result: Method result
            error: Exception if any
        """
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Prepare event data
        data = {}
        if result is not None:
            data["result"] = result
        if error is not None:
            data["error"] = str(error)
            data["error_type"] = type(error).__name__
        
        # Create trace event
        event = TraceEvent(
            trace_id=self.trace_id,
            execution_id=self.execution_id,
            parent_id=self.parent_id,
            agent_name=self.name,
            method_name=method_name,
            event_type="end",
            timestamp=time.time(),
            data=data
        )
        
        # Save trace event
        storage.save_trace_event(event)
    
    def save_artifact(self, name: str, content: Any, artifact_type: str = "data") -> str:
        """
        Save an artifact associated with this execution.
        
        Args:
            name: Name of the artifact
            content: Content of the artifact
            artifact_type: Type of artifact
            
        Returns:
            ID of the artifact
        """
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Create artifact
        artifact = Artifact(
            trace_id=self.trace_id,
            execution_id=self.execution_id,
            name=name,
            content=content,
            artifact_type=artifact_type
        )
        
        # Save artifact
        artifact_id = storage.save_artifact(artifact)
        
        return artifact_id
    
    def trace_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Record a custom trace event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Create trace event
        event = TraceEvent(
            trace_id=self.trace_id,
            execution_id=self.execution_id,
            parent_id=self.parent_id,
            agent_name=self.name,
            method_name="custom",
            event_type=event_type,
            timestamp=time.time(),
            data=data
        )
        
        # Save trace event
        storage.save_trace_event(event)
    
    @classmethod
    def get_trace(cls, trace_id: str) -> Dict[str, Any]:
        """
        Get all events and artifacts for a trace.
        
        Args:
            trace_id: ID of the trace
            
        Returns:
            Dictionary with events and artifacts
        """
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Get trace data
        return storage.get_trace(trace_id)
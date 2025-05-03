"""Span utilities for traced package."""

import uuid
import time
import logging
from typing import Dict, Any, Optional

from traced.core.context import TraceContext
from traced.core.events import TraceEvent, Artifact
from traced.core.base import _get_trace_storage

# Set up logging
logger = logging.getLogger("traced.utils")


class TracedSpan:
    """
    Context manager for trace spans.
    
    This class provides a way to create trace spans that can be used
    in a with statement to trace a block of code.
    """
    
    def __init__(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a trace span.
        
        Args:
            name: Name for this span
            trace_id: ID for the trace (generated if not provided)
            parent_id: ID of the parent execution (None for root)
            attributes: Additional attributes for the span
        """
        # Get current context
        current_trace_id = TraceContext.get_current_trace_id()
        current_parent_id = TraceContext.get_current_parent_id()
        
        # Set trace context
        self.trace_id = trace_id or current_trace_id or str(uuid.uuid4())
        self.parent_id = parent_id or current_parent_id
        self.execution_id = str(uuid.uuid4())
        self.name = name
        self.attributes = attributes or {}
        
        # Store previous context
        self.previous_trace_id = current_trace_id
        self.previous_parent_id = current_parent_id
    
    def __enter__(self) -> 'TracedSpan':
        """
        Enter the span context.
        
        Returns:
            Self for method chaining
        """
        # Update trace context
        TraceContext.set_current_trace_id(self.trace_id)
        TraceContext.set_current_parent_id(self.execution_id)
        
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Record start
        start_data = {"attributes": self.attributes}
        
        start_event = TraceEvent(
            trace_id=self.trace_id,
            execution_id=self.execution_id,
            parent_id=self.parent_id,
            agent_name=self.name,
            method_name="span",
            event_type="start",
            timestamp=time.time(),
            data=start_data
        )
        storage.save_trace_event(start_event)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the span context.
        
        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Record end
        end_data = {}
        if exc_type is not None:
            end_data["error"] = str(exc_val)
            end_data["error_type"] = exc_type.__name__
        
        end_event = TraceEvent(
            trace_id=self.trace_id,
            execution_id=self.execution_id,
            parent_id=self.parent_id,
            agent_name=self.name,
            method_name="span",
            event_type="end",
            timestamp=time.time(),
            data=end_data
        )
        storage.save_trace_event(end_event)
        
        # Restore previous context
        if self.previous_trace_id:
            TraceContext.set_current_trace_id(self.previous_trace_id)
        if self.previous_parent_id:
            TraceContext.set_current_parent_id(self.previous_parent_id)
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an event to this span.
        
        Args:
            name: Name of the event
            attributes: Additional attributes for the event
        """
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Record event
        event_data = {"event_name": name}
        if attributes:
            event_data["attributes"] = attributes
        
        event = TraceEvent(
            trace_id=self.trace_id,
            execution_id=self.execution_id,
            parent_id=self.parent_id,
            agent_name=self.name,
            method_name="event",
            event_type=name,
            timestamp=time.time(),
            data=event_data
        )
        storage.save_trace_event(event)
    
    def save_artifact(self, name: str, content: Any, artifact_type: str = "data") -> str:
        """
        Save an artifact associated with this span.
        
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


def span(
    name: str,
    trace_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
) -> TracedSpan:
    """
    Create a trace span context manager.
    
    This function is a convenience wrapper around TracedSpan.
    
    Args:
        name: Name for this span
        trace_id: ID for the trace (generated if not provided)
        parent_id: ID of the parent execution (None for root)
        attributes: Additional attributes for the span
        
    Returns:
        TracedSpan context manager
    """
    return TracedSpan(
        name=name,
        trace_id=trace_id,
        parent_id=parent_id,
        attributes=attributes
    )
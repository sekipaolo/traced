"""Base storage interface for traced package."""

from typing import Dict, Any

from traced.core.events import TraceEvent, Artifact


class BaseTraceStorage:
    """
    Base class for trace storage backends.
    
    This class defines the interface that all storage backends must implement.
    """
    
    def save_trace_event(self, event: TraceEvent) -> str:
        """
        Save a trace event.
        
        Args:
            event: The trace event to save
            
        Returns:
            ID of the saved event
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement save_trace_event")
    
    def save_artifact(self, artifact: Artifact) -> str:
        """
        Save an artifact.
        
        Args:
            artifact: The artifact to save
            
        Returns:
            ID of the saved artifact
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement save_artifact")
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Get all events and artifacts for a trace.
        
        Args:
            trace_id: ID of the trace
            
        Returns:
            Dictionary with events and artifacts
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement get_trace")
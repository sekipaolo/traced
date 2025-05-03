"""In-memory storage backend for traced package."""

import uuid
from typing import Dict, Any

from traced.storage.base import BaseTraceStorage
from traced.core.events import TraceEvent, Artifact


class InMemoryTraceStorage(BaseTraceStorage):
    """
    Simple in-memory implementation of trace storage.
    
    This storage backend keeps all trace data in memory,
    which is useful for testing or simple applications.
    Note that data is lost when the process exits.
    """
    
    def __init__(self):
        """Initialize in-memory storage."""
        self.events = {}
        self.artifacts = {}
    
    def save_trace_event(self, event: TraceEvent) -> str:
        """
        Save a trace event to memory.
        
        Args:
            event: The trace event to save
            
        Returns:
            ID of the saved event
        """
        event_id = str(uuid.uuid4())
        self.events[event_id] = event
        return event_id
    
    def save_artifact(self, artifact: Artifact) -> str:
        """
        Save an artifact to memory.
        
        Args:
            artifact: The artifact to save
            
        Returns:
            ID of the saved artifact
        """
        self.artifacts[artifact.id] = artifact
        return artifact.id
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Get all events and artifacts for a trace.
        
        Args:
            trace_id: ID of the trace
            
        Returns:
            Dictionary with events and artifacts
        """
        # Filter events by trace_id
        trace_events = [
            event.to_dict() 
            for event in self.events.values() 
            if event.trace_id == trace_id
        ]
        
        # Filter artifacts by trace_id
        trace_artifacts = [
            artifact.to_dict() 
            for artifact in self.artifacts.values() 
            if artifact.trace_id == trace_id
        ]
        
        return {
            "trace_id": trace_id,
            "events": trace_events,
            "artifacts": trace_artifacts
        }
"""Event and artifact classes for traced package."""

import time
import uuid
from typing import Dict, Any, Optional


class TraceEvent:
    """
    Represents a trace event.
    
    Events are recorded during the execution of traced methods,
    providing a timeline of what happened during a trace.
    """
    
    def __init__(
        self,
        trace_id: str,
        execution_id: str,
        parent_id: Optional[str],
        agent_name: str,
        method_name: str,
        event_type: str,
        timestamp: float,
        data: Dict[str, Any]
    ):
        """
        Initialize a trace event.
        
        Args:
            trace_id: ID of the trace this event belongs to
            execution_id: ID of the execution this event belongs to
            parent_id: ID of the parent execution (None for root)
            agent_name: Name of the agent that generated this event
            method_name: Name of the method that generated this event
            event_type: Type of event (e.g., "start", "end", "error")
            timestamp: Time when the event occurred
            data: Additional data for the event
        """
        self.trace_id = trace_id
        self.execution_id = execution_id
        self.parent_id = parent_id
        self.agent_name = agent_name
        self.method_name = method_name
        self.event_type = event_type
        self.timestamp = timestamp
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "trace_id": self.trace_id,
            "execution_id": self.execution_id,
            "parent_id": self.parent_id,
            "agent_name": self.agent_name,
            "method_name": self.method_name,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "data": self.data
        }


class Artifact:
    """
    Represents a trace artifact.
    
    Artifacts are data objects associated with a trace, such as
    inputs, outputs, or intermediate results.
    """
    
    def __init__(
        self,
        trace_id: str,
        execution_id: str,
        name: str,
        content: Any,
        artifact_type: str
    ):
        """
        Initialize a trace artifact.
        
        Args:
            trace_id: ID of the trace this artifact belongs to
            execution_id: ID of the execution this artifact belongs to
            name: Name of the artifact
            content: Content of the artifact
            artifact_type: Type of artifact (e.g., "data", "text", "json")
        """
        self.id = str(uuid.uuid4())
        self.trace_id = trace_id
        self.execution_id = execution_id
        self.name = name
        self.content = content
        self.artifact_type = artifact_type
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the artifact
        """
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "execution_id": self.execution_id,
            "name": self.name,
            "content": self.content,
            "artifact_type": self.artifact_type,
            "timestamp": self.timestamp
        }
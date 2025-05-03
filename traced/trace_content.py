"""
Traced: A simple but powerful tracing library for Python applications

This package provides an easy way to add tracing to any Python class
with minimal code changes - just inherit from Traced!
"""

import time
import uuid
import inspect
import functools
import threading
import logging
from typing import Dict, Any, Optional, List, Union, Callable


# Set up logging
logger = logging.getLogger("traced")


class TraceContext:
    """Thread-local storage for trace context"""
    
    _local = threading.local()
    
    @classmethod
    def get_current_trace_id(cls) -> Optional[str]:
        """Get the current trace ID if it exists"""
        if not hasattr(cls._local, "trace_id"):
            return None
        return cls._local.trace_id
    
    @classmethod
    def set_current_trace_id(cls, trace_id: str) -> None:
        """Set the current trace ID"""
        cls._local.trace_id = trace_id
    
    @classmethod
    def get_current_parent_id(cls) -> Optional[str]:
        """Get the current parent execution ID if it exists"""
        if not hasattr(cls._local, "parent_id"):
            return None
        return cls._local.parent_id
    
    @classmethod
    def set_current_parent_id(cls, parent_id: str) -> None:
        """Set the current parent execution ID"""
        cls._local.parent_id = parent_id
    
    @classmethod
    def clear(cls) -> None:
        """Clear the current context"""
        if hasattr(cls._local, "trace_id"):
            delattr(cls._local, "trace_id")
        if hasattr(cls._local, "parent_id"):
            delattr(cls._local, "parent_id")


class TraceEvent:
    """Represents a trace event"""
    
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
        self.trace_id = trace_id
        self.execution_id = execution_id
        self.parent_id = parent_id
        self.agent_name = agent_name
        self.method_name = method_name
        self.event_type = event_type
        self.timestamp = timestamp
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
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
    """Represents a trace artifact"""
    
    def __init__(
        self,
        trace_id: str,
        execution_id: str,
        name: str,
        content: Any,
        artifact_type: str
    ):
        self.id = str(uuid.uuid4())
        self.trace_id = trace_id
        self.execution_id = execution_id
        self.name = name
        self.content = content
        self.artifact_type = artifact_type
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "execution_id": self.execution_id,
            "name": self.name,
            "content": self.content,
            "artifact_type": self.artifact_type,
            "timestamp": self.timestamp
        }


class BaseTraceStorage:
    """Base class for trace storage backends"""
    
    def save_trace_event(self, event: TraceEvent) -> str:
        """
        Save a trace event
        
        Args:
            event: The trace event to save
            
        Returns:
            ID of the saved event
        """
        raise NotImplementedError("Subclasses must implement save_trace_event")
    
    def save_artifact(self, artifact: Artifact) -> str:
        """
        Save an artifact
        
        Args:
            artifact: The artifact to save
            
        Returns:
            ID of the saved artifact
        """
        raise NotImplementedError("Subclasses must implement save_artifact")
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Get all events and artifacts for a trace
        
        Args:
            trace_id: ID of the trace
            
        Returns:
            Dictionary with events and artifacts
        """
        raise NotImplementedError("Subclasses must implement get_trace")


class InMemoryTraceStorage(BaseTraceStorage):
    """Simple in-memory implementation of trace storage"""
    
    def __init__(self):
        self.events = {}
        self.artifacts = {}
    
    def save_trace_event(self, event: TraceEvent) -> str:
        """Save a trace event to memory"""
        event_id = str(uuid.uuid4())
        self.events[event_id] = event
        return event_id
    
    def save_artifact(self, artifact: Artifact) -> str:
        """Save an artifact to memory"""
        self.artifacts[artifact.id] = artifact
        return artifact.id
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """Get all events and artifacts for a trace"""
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


class MongoDBTraceStorage(BaseTraceStorage):
    """MongoDB implementation of trace storage"""
    
    def __init__(
        self, 
        uri: str = "mongodb://localhost:27017/",
        database: str = "traced",
        events_collection: str = "trace_events",
        artifacts_collection: str = "trace_artifacts"
    ):
        try:
            from pymongo import MongoClient
            self.client = MongoClient(uri)
            self.db = self.client[database]
            self.events = self.db[events_collection]
            self.artifacts = self.db[artifacts_collection]
            
            # Create indexes
            self.events.create_index("trace_id")
            self.events.create_index("execution_id")
            self.artifacts.create_index("trace_id")
            self.artifacts.create_index("execution_id")
            
            logger.info(f"Connected to MongoDB at {uri}, database {database}")
        except ImportError:
            logger.error("pymongo is required for MongoDBTraceStorage")
            raise ImportError("pymongo is required for MongoDBTraceStorage. Install with 'pip install pymongo'")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def save_trace_event(self, event: TraceEvent) -> str:
        """Save a trace event to MongoDB"""
        event_dict = event.to_dict()
        result = self.events.insert_one(event_dict)
        return str(result.inserted_id)
    
    def save_artifact(self, artifact: Artifact) -> str:
        """Save an artifact to MongoDB"""
        artifact_dict = artifact.to_dict()
        result = self.artifacts.insert_one(artifact_dict)
        return str(result.inserted_id)
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """Get all events and artifacts for a trace from MongoDB"""
        # Query events
        events = list(self.events.find({"trace_id": trace_id}))
        
        # Query artifacts
        artifacts = list(self.artifacts.find({"trace_id": trace_id}))
        
        # Clean up MongoDB _id fields
        for item in events + artifacts:
            if "_id" in item:
                item["id"] = str(item["_id"])
                del item["_id"]
        
        return {
            "trace_id": trace_id,
            "events": events,
            "artifacts": artifacts
        }


class SQLTraceStorage(BaseTraceStorage):
    """SQL database implementation of trace storage"""
    
    def __init__(
        self,
        connection_string: str,
        events_table: str = "trace_events",
        artifacts_table: str = "trace_artifacts"
    ):
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, MetaData, Table, Column
            from sqlalchemy import String, Float, JSON
            
            self.engine = create_engine(connection_string)
            self.metadata = MetaData()
            
            # Define tables if they don't exist
            self.events_table = Table(
                events_table, 
                self.metadata,
                Column("id", String, primary_key=True),
                Column("trace_id", String, index=True),
                Column("execution_id", String, index=True),
                Column("parent_id", String),
                Column("agent_name", String),
                Column("method_name", String),
                Column("event_type", String),
                Column("timestamp", Float),
                Column("data", JSON)
            )
            
            self.artifacts_table = Table(
                artifacts_table,
                self.metadata,
                Column("id", String, primary_key=True),
                Column("trace_id", String, index=True),
                Column("execution_id", String, index=True),
                Column("name", String),
                Column("content", JSON),
                Column("artifact_type", String),
                Column("timestamp", Float)
            )
            
            # Create tables
            self.metadata.create_all(self.engine)
            
            logger.info(f"Connected to SQL database with {connection_string}")
        except ImportError:
            logger.error("sqlalchemy is required for SQLTraceStorage")
            raise ImportError("sqlalchemy is required for SQLTraceStorage. Install with 'pip install sqlalchemy'")
        except Exception as e:
            logger.error(f"Failed to connect to SQL database: {e}")
            raise
    
    def save_trace_event(self, event: TraceEvent) -> str:
        """Save a trace event to SQL database"""
        event_id = str(uuid.uuid4())
        event_dict = event.to_dict()
        event_dict["id"] = event_id
        
        with self.engine.connect() as conn:
            conn.execute(self.events_table.insert().values(**event_dict))
            conn.commit()
        
        return event_id
    
    def save_artifact(self, artifact: Artifact) -> str:
        """Save an artifact to SQL database"""
        artifact_dict = artifact.to_dict()
        
        with self.engine.connect() as conn:
            conn.execute(self.artifacts_table.insert().values(**artifact_dict))
            conn.commit()
        
        return artifact.id
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """Get all events and artifacts for a trace from SQL database"""
        events = []
        artifacts = []
        
        with self.engine.connect() as conn:
            # Query events
            result = conn.execute(
                self.events_table.select().where(self.events_table.c.trace_id == trace_id)
            )
            for row in result:
                events.append(dict(row))
            
            # Query artifacts
            result = conn.execute(
                self.artifacts_table.select().where(self.artifacts_table.c.trace_id == trace_id)
            )
            for row in result:
                artifacts.append(dict(row))
        
        return {
            "trace_id": trace_id,
            "events": events,
            "artifacts": artifacts
        }


# Global storage instance
_trace_storage = InMemoryTraceStorage()

def _get_trace_storage() -> BaseTraceStorage:
    """Get the configured trace storage backend"""
    global _trace_storage
    return _trace_storage


def configure_tracing(storage_type: str = "memory", **kwargs) -> None:
    """
    Configure the global tracing storage
    
    Args:
        storage_type: Type of storage to use ("memory", "mongodb", "sql")
        **kwargs: Additional configuration for the storage backend
    
    Raises:
        ValueError: If the storage type is unknown
    """
    global _trace_storage
    
    if storage_type == "memory":
        _trace_storage = InMemoryTraceStorage()
    elif storage_type == "mongodb":
        _trace_storage = MongoDBTraceStorage(**kwargs)
    elif storage_type == "sql":
        _trace_storage = SQLTraceStorage(**kwargs)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
    
    logger.info(f"Configured tracing with storage type: {storage_type}")


class Traced:
    """
    Base class that provides tracing capabilities
    
    Simply inherit from this class and all public methods will be
    automatically traced!
    """
    
    # Class-level configuration
    TRACED_EXCLUDE = []  # Methods to exclude from tracing
    TRACED_RECORD_PARAMS = True  # Whether to record method parameters
    TRACED_RECORD_RESULTS = True  # Whether to record method results
    
    def __init__(
        self,
        name: Optional[str] = None,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ):
        """
        Initialize the traced object
        
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
        """Generate a unique ID"""
        return str(uuid.uuid4())
    
    def _wrap_methods(self) -> None:
        """Automatically wrap public methods with tracing"""
        # Find all public methods
        for attr_name in dir(self):
            # Skip private methods and excluded methods
            if attr_name.startswith('_') or attr_name in self.TRACED_EXCLUDE:
                continue
            
            attr = getattr(self, attr_name)
            
            # Only wrap callable methods that haven't been wrapped yet
            if callable(attr) and not hasattr(attr, '_traced'):
                original_method = attr
                
                @functools.wraps(original_method)
                def traced_method(*args, **kwargs):
                    # Get self as the first argument
                    self = args[0]
                    
                    # Update trace context for this execution
                    previous_trace_id = TraceContext.get_current_trace_id()
                    previous_parent_id = TraceContext.get_current_parent_id()
                    
                    TraceContext.set_current_trace_id(self.trace_id)
                    TraceContext.set_current_parent_id(self.execution_id)
                    
                    try:
                        # Start tracing the method
                        method_args = args[1:] if self.TRACED_RECORD_PARAMS else None
                        method_kwargs = kwargs if self.TRACED_RECORD_PARAMS else None
                        self._start_trace(original_method.__name__, method_args, method_kwargs)
                        
                        # Execute the original method
                        result = original_method(*args, **kwargs)
                        
                        # End trace successfully
                        method_result = result if self.TRACED_RECORD_RESULTS else None
                        self._end_trace(original_method.__name__, result=method_result)
                        
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
    
    def _start_trace(
        self,
        method_name: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None
    ) -> None:
        """
        Start tracing a method execution
        
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
        End tracing a method execution
        
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
        Save an artifact associated with this execution
        
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
        Record a custom trace event
        
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
        Get all events and artifacts for a trace
        
        Args:
            trace_id: ID of the trace
            
        Returns:
            Dictionary with events and artifacts
        """
        # Get the trace storage backend
        storage = _get_trace_storage()
        
        # Get trace data
        return storage.get_trace(trace_id)


# Decorator for tracing functions without class inheritance
def traced(
    func: Optional[Callable] = None,
    name: Optional[str] = None,
    trace_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    record_params: bool = True,
    record_results: bool = True
):
    """
    Decorator to trace a function
    
    This can be used directly as @traced or with parameters as @traced()
    
    Args:
        func: Function to decorate (automatically provided when used as @traced)
        name: Name for this traced function (defaults to function name)
        trace_id: ID for the trace (generated if not provided)
        parent_id: ID of the parent execution (None for root)
        record_params: Whether to record function parameters
        record_results: Whether to record function results
        
    Returns:
        Decorated function
    """
    # Handle direct decoration without parentheses
    if func is not None:
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            # Generate IDs and context
            current_trace_id = TraceContext.get_current_trace_id()
            current_parent_id = TraceContext.get_current_parent_id()
            
            trace = trace_id or current_trace_id or str(uuid.uuid4())
            execution = str(uuid.uuid4())
            parent = parent_id or current_parent_id
            function_name = name or func.__name__
            
            # Get the trace storage backend
            storage = _get_trace_storage()
            
            # Update trace context
            previous_trace_id = TraceContext.get_current_trace_id()
            previous_parent_id = TraceContext.get_current_parent_id()
            
            TraceContext.set_current_trace_id(trace)
            TraceContext.set_current_parent_id(execution)
            
            try:
                # Record start
                start_data = {}
                if record_params:
                    start_data["args"] = args
                    start_data["kwargs"] = kwargs
                
                start_event = TraceEvent(
                    trace_id=trace,
                    execution_id=execution,
                    parent_id=parent,
                    agent_name=function_name,
                    method_name="function",
                    event_type="start",
                    timestamp=time.time(),
                    data=start_data
                )
                storage.save_trace_event(start_event)
                
                # Call function
                result = func(*args, **kwargs)
                
                # Record end
                end_data = {}
                if record_results:
                    end_data["result"] = result
                
                end_event = TraceEvent(
                    trace_id=trace,
                    execution_id=execution,
                    parent_id=parent,
                    agent_name=function_name,
                    method_name="function",
                    event_type="end",
                    timestamp=time.time(),
                    data=end_data
                )
                storage.save_trace_event(end_event)
                
                return result
            except Exception as e:
                # Record error
                error_event = TraceEvent(
                    trace_id=trace,
                    execution_id=execution,
                    parent_id=parent,
                    agent_name=function_name,
                    method_name="function",
                    event_type="error",
                    timestamp=time.time(),
                    data={
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                storage.save_trace_event(error_event)
                raise
            finally:
                # Restore previous context
                if previous_trace_id:
                    TraceContext.set_current_trace_id(previous_trace_id)
                if previous_parent_id:
                    TraceContext.set_current_parent_id(previous_parent_id)
        
        return wrapped
    
    # Handle decoration with parameters
    def decorator(f):
        return traced(
            f,
            name=name,
            trace_id=trace_id,
            parent_id=parent_id,
            record_params=record_params,
            record_results=record_results
        )
    
    return decorator


# Decorator to exclude a method from tracing
def not_traced(func):
    """
    Decorator to exclude a method from tracing
    
    Args:
        func: Method to exclude
        
    Returns:
        Original method, marked as not to be traced
    """
    func._not_traced = True
    return func


# Context manager for trace spans
class TracedSpan:
    """Context manager for trace spans"""
    
    def __init__(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a trace span
        
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
    
    def __enter__(self):
        """Enter the context"""
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
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context"""
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
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add an event to this span
        
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
        Save an artifact associated with this span
        
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


# Utility function to create a trace span
def span(
    name: str,
    trace_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
) -> TracedSpan:
    """
    Create a trace span context manager
    
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


# Decorator for automatically tracing all methods in a class
def traced_class(cls):
    """
    Decorator to make all public methods in a class traced
    
    Args:
        cls: Class to decorate
        
    Returns:
        Decorated class
    """
    # Collect original methods
    original_methods = {}
    for attr_name in dir(cls):
        # Skip private methods
        if attr_name.startswith('_'):
            continue
            
        attr = getattr(cls, attr_name)
        
        # Only collect callable methods
        if callable(attr) and not hasattr(attr, '_not_traced'):
            original_methods[attr_name] = attr
    
    # Create a new class that inherits from Traced and the original class
    class TracedSubclass(Traced, cls):
        def __init__(self, *args, **kwargs):
            # Initialize Traced first
            Traced.__init__(self)
            
            # Then initialize the original class
            cls.__init__(self, *args, **kwargs)
    
    # Make the new class look like the original
    TracedSubclass.__name__ = cls.__name__
    TracedSubclass.__qualname__ = cls.__qualname__
    TracedSubclass.__module__ = cls.__module__
    TracedSubclass.__doc__ = cls.__doc__
    
    return TracedSubclass
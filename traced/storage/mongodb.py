"""MongoDB storage backend for traced package."""

import logging
from typing import Dict, Any

from traced.storage.base import BaseTraceStorage
from traced.core.events import TraceEvent, Artifact

# Set up logging
logger = logging.getLogger("traced.storage.mongodb")


class MongoDBTraceStorage(BaseTraceStorage):
    """
    MongoDB implementation of trace storage.
    
    This storage backend stores trace data in MongoDB,
    which is useful for production applications.
    
    Note: This requires the pymongo package to be installed.
    """
    
    def __init__(
        self, 
        uri: str = "mongodb://localhost:27017/",
        database: str = "traced",
        events_collection: str = "trace_events",
        artifacts_collection: str = "trace_artifacts"
    ):
        """
        Initialize MongoDB storage.
        
        Args:
            uri: MongoDB connection URI
            database: Database name
            events_collection: Collection name for events
            artifacts_collection: Collection name for artifacts
            
        Raises:
            ImportError: If pymongo is not installed
            Exception: If MongoDB connection fails
        """
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
        """
        Save a trace event to MongoDB.
        
        Args:
            event: The trace event to save
            
        Returns:
            ID of the saved event
        """
        event_dict = event.to_dict()
        result = self.events.insert_one(event_dict)
        return str(result.inserted_id)
    
    def save_artifact(self, artifact: Artifact) -> str:
        """
        Save an artifact to MongoDB.
        
        Args:
            artifact: The artifact to save
            
        Returns:
            ID of the saved artifact
        """
        artifact_dict = artifact.to_dict()
        result = self.artifacts.insert_one(artifact_dict)
        return str(result.inserted_id)
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Get all events and artifacts for a trace from MongoDB.
        
        Args:
            trace_id: ID of the trace
            
        Returns:
            Dictionary with events and artifacts
        """
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
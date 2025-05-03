"""SQLite storage backend for traced package."""

import sqlite3
import json
import os
import logging
import uuid
from typing import Dict, Any

from traced.storage.base import BaseTraceStorage
from traced.core.events import TraceEvent, Artifact

# Set up logging
logger = logging.getLogger("traced.storage.sqlite")


class SQLiteTraceStorage(BaseTraceStorage):
    """
    SQLite implementation of trace storage.
    
    This storage backend stores trace data in a SQLite database file,
    which is perfect for local development and small applications.
    """
    
    def __init__(self, database_path: str = "traces.db"):
        """
        Initialize SQLite storage.
        
        Args:
            database_path: Path to SQLite database file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(database_path)), exist_ok=True)
        
        self.database_path = database_path
        self._create_tables()
        logger.info(f"Connected to SQLite database at {database_path}")
    
    def _create_tables(self):
        """Create required tables if they don't exist."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Create events table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trace_events (
                id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                execution_id TEXT NOT NULL,
                parent_id TEXT,
                agent_name TEXT NOT NULL,
                method_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp REAL NOT NULL,
                data TEXT NOT NULL
            )
            ''')
            
            # Create indexes for events table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_trace_id ON trace_events(trace_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_execution_id ON trace_events(execution_id)')
            
            # Create artifacts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trace_artifacts (
                id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                execution_id TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
            ''')
            
            # Create indexes for artifacts table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_artifacts_trace_id ON trace_artifacts(trace_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_artifacts_execution_id ON trace_artifacts(execution_id)')
            
            conn.commit()
    
    def save_trace_event(self, event: TraceEvent) -> str:
        """
        Save a trace event to SQLite.
        
        Args:
            event: The trace event to save
            
        Returns:
            ID of the saved event
        """
        event_dict = event.to_dict()
        event_id = str(uuid.uuid4())
        
        # Serialize data to JSON
        event_data = json.dumps(event_dict["data"])
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO trace_events
            (id, trace_id, execution_id, parent_id, agent_name, method_name, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_id,
                event_dict["trace_id"],
                event_dict["execution_id"],
                event_dict["parent_id"],
                event_dict["agent_name"],
                event_dict["method_name"],
                event_dict["event_type"],
                event_dict["timestamp"],
                event_data
            ))
            conn.commit()
        
        return event_id
    
    def save_artifact(self, artifact: Artifact) -> str:
        """
        Save an artifact to SQLite.
        
        Args:
            artifact: The artifact to save
            
        Returns:
            ID of the saved artifact
        """
        artifact_dict = artifact.to_dict()
        
        # Serialize content to JSON
        artifact_content = json.dumps(artifact_dict["content"])
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO trace_artifacts
            (id, trace_id, execution_id, name, content, artifact_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                artifact_dict["id"],
                artifact_dict["trace_id"],
                artifact_dict["execution_id"],
                artifact_dict["name"],
                artifact_content,
                artifact_dict["artifact_type"],
                artifact_dict["timestamp"]
            ))
            conn.commit()
        
        return artifact_dict["id"]
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Get all events and artifacts for a trace from SQLite.
        
        Args:
            trace_id: ID of the trace
            
        Returns:
            Dictionary with events and artifacts
        """
        events = []
        artifacts = []
        
        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row  # Access rows as dictionaries
            cursor = conn.cursor()
            
            # Query events
            cursor.execute('SELECT * FROM trace_events WHERE trace_id = ?', (trace_id,))
            for row in cursor.fetchall():
                event = dict(row)
                
                # Deserialize data from JSON
                event["data"] = json.loads(event["data"])
                
                events.append(event)
            
            # Query artifacts
            cursor.execute('SELECT * FROM trace_artifacts WHERE trace_id = ?', (trace_id,))
            for row in cursor.fetchall():
                artifact = dict(row)
                
                # Deserialize content from JSON
                artifact["content"] = json.loads(artifact["content"])
                
                artifacts.append(artifact)
        
        return {
            "trace_id": trace_id,
            "events": events,
            "artifacts": artifacts
        }
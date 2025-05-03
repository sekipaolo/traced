"""
Data models for the traced viewer application.

This module provides helper classes to work with trace data
from the SQLite database.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional


def get_db_connection(db_path: str):
    """
    Get a connection to the SQLite database.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        SQLite connection with row factory set to dict
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@dataclass
class TraceEvent:
    """Represents a trace event in the database."""
    id: str
    trace_id: str
    execution_id: str
    parent_id: Optional[str]
    agent_name: str
    method_name: str
    event_type: str
    timestamp: float
    data: Dict[str, Any]
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'TraceEvent':
        """
        Create a TraceEvent from a database row.
        
        Args:
            row: Database row
            
        Returns:
            TraceEvent instance
        """
        row_dict = dict(row)
        # Parse data from JSON
        row_dict['data'] = json.loads(row_dict['data'])
        return cls(**row_dict)
    
    @property
    def formatted_timestamp(self) -> str:
        """
        Get a human-readable timestamp.
        
        Returns:
            Formatted timestamp string
        """
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    @property
    def short_id(self) -> str:
        """
        Get a shortened ID for display.
        
        Returns:
            First 8 characters of the ID
        """
        return self.id[:8]


@dataclass
class Artifact:
    """Represents a trace artifact in the database."""
    id: str
    trace_id: str
    execution_id: str
    name: str
    content: Any
    artifact_type: str
    timestamp: float
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Artifact':
        """
        Create an Artifact from a database row.
        
        Args:
            row: Database row
            
        Returns:
            Artifact instance
        """
        row_dict = dict(row)
        # Parse content from JSON
        row_dict['content'] = json.loads(row_dict['content'])
        return cls(**row_dict)
    
    @property
    def formatted_timestamp(self) -> str:
        """
        Get a human-readable timestamp.
        
        Returns:
            Formatted timestamp string
        """
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    @property
    def short_id(self) -> str:
        """
        Get a shortened ID for display.
        
        Returns:
            First 8 characters of the ID
        """
        return self.id[:8]
    
    @property
    def content_preview(self) -> str:
        """
        Get a preview of the content for display.
        
        Returns:
            String preview of the content
        """
        content_str = json.dumps(self.content, indent=2)
        if len(content_str) > 100:
            return content_str[:100] + '...'
        return content_str


@dataclass
class Execution:
    """Represents an execution in a trace."""
    id: str
    parent_id: Optional[str]
    agent_name: str
    events: List[TraceEvent]
    artifacts: List[Artifact]
    children: List[str]
    
    @property
    def start_time(self) -> Optional[float]:
        """
        Get the start time of the execution.
        
        Returns:
            Timestamp of the first event or None if no events
        """
        if not self.events:
            return None
        return min(event.timestamp for event in self.events)
    
    @property
    def end_time(self) -> Optional[float]:
        """
        Get the end time of the execution.
        
        Returns:
            Timestamp of the last event or None if no events
        """
        if not self.events:
            return None
        return max(event.timestamp for event in self.events)
    
    @property
    def duration(self) -> Optional[float]:
        """
        Get the duration of the execution in seconds.
        
        Returns:
            Duration in seconds or None if not available
        """
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time
    
    @property
    def method_names(self) -> List[str]:
        """
        Get a list of unique method names in this execution.
        
        Returns:
            List of method names
        """
        return sorted(set(event.method_name for event in self.events))
    
    @property
    def short_id(self) -> str:
        """
        Get a shortened ID for display.
        
        Returns:
            First 8 characters of the ID
        """
        return self.id[:8]


@dataclass
class Trace:
    """Represents a complete trace in the database."""
    id: str
    executions: Dict[str, Execution]
    root_executions: List[str]
    
    @classmethod
    def from_database(cls, db_path: str, trace_id: str) -> 'Trace':
        """
        Load a trace from the database.
        
        Args:
            db_path: Path to the database file
            trace_id: ID of the trace to load
            
        Returns:
            Trace instance
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Get all events for this trace
        cursor.execute('SELECT * FROM trace_events WHERE trace_id = ? ORDER BY timestamp ASC', (trace_id,))
        events = [TraceEvent.from_row(row) for row in cursor.fetchall()]
        
        # Get all artifacts for this trace
        cursor.execute('SELECT * FROM trace_artifacts WHERE trace_id = ?', (trace_id,))
        artifacts = [Artifact.from_row(row) for row in cursor.fetchall()]
        
        # Build execution map
        executions = {}
        for event in events:
            execution_id = event.execution_id
            if execution_id not in executions:
                executions[execution_id] = Execution(
                    id=execution_id,
                    parent_id=event.parent_id,
                    agent_name=event.agent_name,
                    events=[],
                    artifacts=[],
                    children=[]
                )
            executions[execution_id].events.append(event)
        
        # Add artifacts to their executions
        for artifact in artifacts:
            execution_id = artifact.execution_id
            if execution_id in executions:
                executions[execution_id].artifacts.append(artifact)
        
        # Build parent-child relationships
        for exec_id, execution in executions.items():
            parent_id = execution.parent_id
            if parent_id and parent_id in executions:
                executions[parent_id].children.append(exec_id)
        
        # Find root executions
        root_executions = [
            exec_id for exec_id, execution in executions.items()
            if not execution.parent_id or execution.parent_id not in executions
        ]
        
        conn.close()
        return cls(id=trace_id, executions=executions, root_executions=root_executions)
    
    @classmethod
    def list_traces(cls, db_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get a list of all traces in the database.
        
        Args:
            db_path: Path to the database file
            limit: Maximum number of traces to return
            
        Returns:
            List of trace summary dictionaries
        """
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Get unique trace_ids with metadata
        cursor.execute('''
        SELECT DISTINCT 
            e.trace_id, 
            COUNT(DISTINCT e.execution_id) as execution_count,
            MIN(e.timestamp) as start_time,
            MAX(e.timestamp) as end_time,
            (SELECT agent_name FROM trace_events 
             WHERE trace_id = e.trace_id 
             ORDER BY timestamp ASC LIMIT 1) as root_agent
        FROM trace_events e
        GROUP BY e.trace_id
        ORDER BY start_time DESC
        LIMIT ?
        ''', (limit,))
        
        traces = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Convert times to datetime objects
            start_time = datetime.fromtimestamp(row_dict['start_time'])
            duration = row_dict['end_time'] - row_dict['start_time']
            
            traces.append({
                'trace_id': row_dict['trace_id'],
                'root_agent': row_dict['root_agent'],
                'execution_count': row_dict['execution_count'],
                'duration': duration,
                'start_time': start_time,
                'formatted_start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'formatted_duration': f"{duration:.6f}s"
            })
        
        conn.close()
        return traces
    
    @property
    def total_events(self) -> int:
        """
        Get the total number of events in the trace.
        
        Returns:
            Total number of events
        """
        return sum(len(execution.events) for execution in self.executions.values())
    
    @property
    def total_artifacts(self) -> int:
        """
        Get the total number of artifacts in the trace.
        
        Returns:
            Total number of artifacts
        """
        return sum(len(execution.artifacts) for execution in self.executions.values())
    
    @property
    def duration(self) -> Optional[float]:
        """
        Get the total duration of the trace in seconds.
        
        Returns:
            Duration in seconds or None if not available
        """
        start_times = [execution.start_time for execution in self.executions.values() 
                     if execution.start_time is not None]
        end_times = [execution.end_time for execution in self.executions.values() 
                   if execution.end_time is not None]
        
        if not start_times or not end_times:
            return None
        
        return max(end_times) - min(start_times)
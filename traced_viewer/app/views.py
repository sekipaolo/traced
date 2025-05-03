"""
Route handlers for the traced viewer application.
"""

import os
import json
from flask import Blueprint, render_template, request, jsonify, current_app

from app.models import Trace

# Create blueprint
bp = Blueprint('views', __name__)

# Get database path from environment or use default
def get_db_path():
    """Get database path from environment or use default."""
    return os.environ.get('TRACED_DB_PATH', '/data/traces.db')


@bp.route('/')
def index():
    """Display the main dashboard."""
    return render_template('index.html')


@bp.route('/traces')
def traces_page():
    """Render the traces list page."""
    return render_template('trace_list.html')


@bp.route('/traces/<trace_id>')
def trace_detail_page(trace_id):
    """
    Render the trace detail page.
    
    Args:
        trace_id: ID of the trace to display
    """
    return render_template('trace_detail.html', trace_id=trace_id)


@bp.route('/api/traces')
def get_traces():
    """
    Get a list of all traces.
    
    Query Parameters:
        limit: Maximum number of traces to return (default: 100)
    
    Returns:
        JSON list of trace summaries
    """
    try:
        limit = int(request.args.get('limit', 100))
        traces = Trace.list_traces(get_db_path(), limit=limit)
        return jsonify(traces)
    except Exception as e:
        current_app.logger.error(f"Error getting traces: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/traces/<trace_id>')
def get_trace(trace_id):
    """
    Get details for a specific trace.
    
    Args:
        trace_id: ID of the trace to get
    
    Returns:
        JSON representation of the trace
    """
    try:
        trace = Trace.from_database(get_db_path(), trace_id)
        
        # Convert trace to JSON-serializable structure
        result = {
            'trace_id': trace.id,
            'root_executions': trace.root_executions,
            'total_events': trace.total_events,
            'total_artifacts': trace.total_artifacts,
            'duration': trace.duration,
            'executions': {}
        }
        
        # Convert executions
        for exec_id, execution in trace.executions.items():
            result['executions'][exec_id] = {
                'id': execution.id,
                'parent_id': execution.parent_id,
                'agent_name': execution.agent_name,
                'children': execution.children,
                'start_time': execution.start_time,
                'end_time': execution.end_time,
                'duration': execution.duration,
                'method_names': execution.method_names,
                'short_id': execution.short_id,
                
                # Convert events
                'events': [{
                    'id': event.id,
                    'short_id': event.short_id,
                    'method_name': event.method_name,
                    'event_type': event.event_type,
                    'timestamp': event.timestamp,
                    'formatted_timestamp': event.formatted_timestamp,
                    'data': event.data
                } for event in execution.events],
                
                # Convert artifacts
                'artifacts': [{
                    'id': artifact.id,
                    'short_id': artifact.short_id,
                    'name': artifact.name,
                    'artifact_type': artifact.artifact_type,
                    'timestamp': artifact.timestamp,
                    'formatted_timestamp': artifact.formatted_timestamp,
                    'content': artifact.content,
                    'content_preview': artifact.content_preview
                } for artifact in execution.artifacts]
            }
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error getting trace {trace_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/executions/<execution_id>/events')
def get_execution_events(execution_id):
    """
    Get events for a specific execution.
    
    Args:
        execution_id: ID of the execution to get events for
    
    Query Parameters:
        trace_id: ID of the trace (required)
    
    Returns:
        JSON list of events
    """
    try:
        trace_id = request.args.get('trace_id')
        if not trace_id:
            return jsonify({"error": "trace_id is required"}), 400
        
        trace = Trace.from_database(get_db_path(), trace_id)
        
        # Find the execution
        if execution_id not in trace.executions:
            return jsonify({"error": f"Execution {execution_id} not found"}), 404
        
        execution = trace.executions[execution_id]
        
        # Convert events to JSON
        events = [{
            'id': event.id,
            'short_id': event.short_id,
            'method_name': event.method_name,
            'event_type': event.event_type,
            'timestamp': event.timestamp,
            'formatted_timestamp': event.formatted_timestamp,
            'data': event.data
        } for event in execution.events]
        
        return jsonify(events)
    except Exception as e:
        current_app.logger.error(f"Error getting events for execution {execution_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/executions/<execution_id>/artifacts')
def get_execution_artifacts(execution_id):
    """
    Get artifacts for a specific execution.
    
    Args:
        execution_id: ID of the execution to get artifacts for
    
    Query Parameters:
        trace_id: ID of the trace (required)
    
    Returns:
        JSON list of artifacts
    """
    try:
        trace_id = request.args.get('trace_id')
        if not trace_id:
            return jsonify({"error": "trace_id is required"}), 400
        
        trace = Trace.from_database(get_db_path(), trace_id)
        
        # Find the execution
        if execution_id not in trace.executions:
            return jsonify({"error": f"Execution {execution_id} not found"}), 404
        
        execution = trace.executions[execution_id]
        
        # Convert artifacts to JSON
        artifacts = [{
            'id': artifact.id,
            'short_id': artifact.short_id,
            'name': artifact.name,
            'artifact_type': artifact.artifact_type,
            'timestamp': artifact.timestamp,
            'formatted_timestamp': artifact.formatted_timestamp,
            'content': artifact.content,
            'content_preview': artifact.content_preview
        } for artifact in execution.artifacts]
        
        return jsonify(artifacts)
    except Exception as e:
        current_app.logger.error(f"Error getting artifacts for execution {execution_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import os

app = Flask(__name__)

# Configuration
DATABASE_PATH = os.environ.get('TRACED_DB_PATH', '/data/traces.db')

def get_db():
    """Connect to the application's database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Display the main dashboard."""
    return render_template('index.html')

@app.route('/api/traces')
def get_traces():
    """Get a list of all traces."""
    conn = get_db()
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
    ''')
    
    traces = []
    for row in cursor.fetchall():
        traces.append({
            'trace_id': row['trace_id'],
            'root_agent': row['root_agent'],
            'execution_count': row['execution_count'],
            'duration': row['end_time'] - row['start_time'],
            'start_time': row['start_time']
        })
    
    return jsonify(traces)

@app.route('/api/traces/<trace_id>')
def get_trace(trace_id):
    """Get details for a specific trace."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all events for this trace
    cursor.execute('SELECT * FROM trace_events WHERE trace_id = ? ORDER BY timestamp ASC', (trace_id,))
    events = []
    for row in cursor.fetchall():
        event = dict(row)
        event['data'] = json.loads(event['data'])
        events.append(event)
    
    # Get all artifacts for this trace
    cursor.execute('SELECT * FROM trace_artifacts WHERE trace_id = ?', (trace_id,))
    artifacts = []
    for row in cursor.fetchall():
        artifact = dict(row)
        artifact['content'] = json.loads(artifact['content'])
        artifacts.append(artifact)
    
    # Build execution tree
    executions = {}
    for event in events:
        execution_id = event['execution_id']
        if execution_id not in executions:
            executions[execution_id] = {
                'id': execution_id,
                'parent_id': event['parent_id'],
                'agent_name': event['agent_name'],
                'events': [],
                'artifacts': [],
                'children': []
            }
        executions[execution_id]['events'].append(event)
    
    # Add artifacts to their executions
    for artifact in artifacts:
        execution_id = artifact['execution_id']
        if execution_id in executions:
            executions[execution_id]['artifacts'].append(artifact)
    
    # Build tree structure
    for exec_id, exec_data in executions.items():
        parent_id = exec_data['parent_id']
        if parent_id and parent_id in executions:
            executions[parent_id]['children'].append(exec_id)
    
    # Find root execution
    root_executions = [exec_id for exec_id, exec_data in executions.items() 
                      if not exec_data['parent_id'] or exec_data['parent_id'] not in executions]
    
    return jsonify({
        'trace_id': trace_id,
        'executions': executions,
        'root_executions': root_executions
    })

@app.route('/traces')
def traces_page():
    """Render the traces list page."""
    return render_template('trace_list.html')

@app.route('/traces/<trace_id>')
def trace_detail_page(trace_id):
    """Render the trace detail page."""
    return render_template('trace_detail.html', trace_id=trace_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
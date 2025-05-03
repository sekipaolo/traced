"""Function decorators for traced package."""

import uuid
import time
import functools
import logging
from typing import Dict, Any, Optional, Callable

from traced.core.context import TraceContext
from traced.core.events import TraceEvent
from traced.core.base import _get_trace_storage

# Set up logging
logger = logging.getLogger("traced.decorators")


def traced(
    func: Optional[Callable] = None,
    name: Optional[str] = None,
    trace_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    record_params: bool = True,
    record_results: bool = True
):
    """
    Decorator to trace a function.
    
    This can be used directly as @traced or with parameters as @traced().
    
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


def not_traced(func):
    """
    Decorator to exclude a method from tracing.
    
    Args:
        func: Method to exclude
        
    Returns:
        Original method, marked as not to be traced
    """
    func._not_traced = True
    return func
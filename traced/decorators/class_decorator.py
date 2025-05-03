"""Class decorators for traced package."""

import inspect
import logging
from typing import Type, Any, Callable

from traced.core.base import Traced

# Set up logging
logger = logging.getLogger("traced.decorators")


def traced_class(cls: Type) -> Type:
    """
    Decorator to make all public methods in a class traced.
    
    This decorator creates a new class that inherits from both Traced
    and the original class, making all public methods traced automatically.
    
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
        # Copy class-level configuration
        TRACED_EXCLUDE = getattr(cls, 'TRACED_EXCLUDE', [])
        TRACED_RECORD_PARAMS = getattr(cls, 'TRACED_RECORD_PARAMS', True)
        TRACED_RECORD_RESULTS = getattr(cls, 'TRACED_RECORD_RESULTS', True)
        
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
    
    logger.debug(f"Created traced class {cls.__name__}")
    return TracedSubclass
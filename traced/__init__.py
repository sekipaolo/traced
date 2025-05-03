"""
Traced: A simple but powerful tracing library for Python applications

This package provides an easy way to add tracing to any Python class
with minimal code changes - just inherit from Traced!
"""

import logging

# Set up logging
logger = logging.getLogger("traced")

# Import core components
from traced.core.base import Traced, configure_tracing
from traced.decorators.function import traced, not_traced
from traced.decorators.class_decorators import traced_class
from traced.utils.span import span, TracedSpan

# Set default version
__version__ = "0.1.0"

# Default exports
__all__ = [
    'Traced',
    'configure_tracing',
    'traced',
    'not_traced',
    'traced_class',
    'span',
    'TracedSpan'
]
"""Storage backends for traced package."""

from traced.storage.base import BaseTraceStorage
from traced.storage.memory import InMemoryTraceStorage

# Optional imports depending on dependencies
try:
    from traced.storage.mongodb import MongoDBTraceStorage
except ImportError:
    # mongodb is optional
    pass

try:
    from traced.storage.sql import SQLTraceStorage
except ImportError:
    # sqlalchemy is optional
    pass

__all__ = ['BaseTraceStorage', 'InMemoryTraceStorage']

# Add optional storage backends to __all__ if available
try:
    __all__.append('MongoDBTraceStorage')
except NameError:
    pass

try:
    __all__.append('SQLTraceStorage')
except NameError:
    pass
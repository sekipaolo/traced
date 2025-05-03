# Traced

A simple but powerful tracing library for Python applications with minimal code changes!

## Features

- **Simple Inheritance-Based Tracing**: Just inherit from `Traced` and all public methods are automatically traced!
- **Multiple Storage Backends**: Store traces in memory, MongoDB, or SQL databases
- **Flexible API Options**: Use inheritance, decorators, or context managers
- **Thread-Safe**: Works in multi-threaded applications
- **Minimal Impact**: Easy to add to existing code with minimal changes

## Installation

```bash
# Basic installation
pip install traced

# With MongoDB support
pip install traced[mongodb]

# With SQL support
pip install traced[sql]

# With all optional dependencies
pip install traced[all]
```

## Quick Start

### Basic Usage with Inheritance

```python
from traced import Traced, configure_tracing

# Configure tracing (once at application startup)
configure_tracing(
    storage_type="memory"  # Use in-memory storage for testing
)

# Create a traced class
class DataProcessor(Traced):
    def process(self, data):
        # This method is automatically traced
        result = self._transform(data)
        
        # Save an artifact
        self.save_artifact("processed_data", result, "json")
        
        return result
    
    def _transform(self, data):
        # Private methods (starting with _) are not traced
        return {"transformed": data}

# Use the class normally
processor = DataProcessor()
result = processor.process({"input": "value"})
```

### Function Decorator

```python
from traced import traced

@traced
def process_request(request_data):
    # Function will be traced
    return {"processed": request_data}
```

### Context Manager

```python
from traced import span

def complex_operation():
    with span("operation") as s:
        # First step
        s.add_event("step1_started")
        step1_result = do_step1()
        
        # Save intermediate artifact
        s.save_artifact("step1_result", step1_result, "json")
        
        # Second step
        s.add_event("step2_started")
        final_result = do_step2(step1_result)
        
    return final_result
```

### Using MongoDB Storage

```python
from traced import configure_tracing

# Configure MongoDB storage
configure_tracing(
    storage_type="mongodb",
    uri="mongodb://localhost:27017/",
    database="traced",
    events_collection="trace_events",
    artifacts_collection="trace_artifacts"
)
```

### Using SQL Storage

```python
from traced import configure_tracing

# Configure SQL storage
configure_tracing(
    storage_type="sql",
    connection_string="postgresql://user:pass@localhost/traced"
)
```

## Advanced Usage

### Class Decorator

```python
from traced import traced_class, not_traced

@traced_class
class ExistingService:
    def method1(self):
        # Will be traced
        pass
    
    @not_traced
    def internal_helper(self):
        # Won't be traced
        pass
```

### Excluding Methods from Tracing

```python
class MyService(Traced):
    # List methods to exclude from tracing
    TRACED_EXCLUDE = ['sensitive_method']
    
    def normal_method(self):
        # This method will be traced
        pass
    
    def sensitive_method(self):
        # This method won't be traced
        pass
```

### Controlling Parameter and Result Recording

```python
class MyService(Traced):
    # Don't record parameters (for privacy or performance)
    TRACED_RECORD_PARAMS = False
    
    # Don't record results (for privacy or performance)
    TRACED_RECORD_RESULTS = False
    
    def process(self, sensitive_data):
        # Parameters and results won't be recorded
        return process_data(sensitive_data)
```

## License

MIT
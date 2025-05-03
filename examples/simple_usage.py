"""
Simple example of using traced package.
"""

import time
from traced import Traced, configure_tracing, traced, span


# Configure tracing to use in-memory storage
configure_tracing(storage_type="memory")


# Example 1: Class inheritance
class DataProcessor(Traced):
    def process(self, data):
        """Process some data."""
        print(f"Processing {data}")
        
        # Simulate some work
        time.sleep(0.1)
        
        # Save an artifact
        self.save_artifact("input_data", data, "json")
        
        # Process the data
        result = self._transform(data)
        
        # Save another artifact
        self.save_artifact("processed_data", result, "json")
        
        return result
    
    def _transform(self, data):
        """Private method to transform data (not traced)."""
        if isinstance(data, dict):
            return {k.upper(): v.upper() if isinstance(v, str) else v 
                   for k, v in data.items()}
        elif isinstance(data, str):
            return data.upper()
        else:
            return data


# Example 2: Function decorator
@traced
def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    print(f"Calculating average of {numbers}")
    
    # Simulate some work
    time.sleep(0.1)
    
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    
    return average


# Example 3:
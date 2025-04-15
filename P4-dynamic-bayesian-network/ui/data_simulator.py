import random
import time
import numpy as np
import os
import json

class DataSimulator:
    """Simulates data for the bar plot visualization."""
    
    def __init__(self, num_bars=3, min_value=0, max_value=100, update_rate=0.5, data_file="barplot_data.json"):
        """Initialize the data simulator.
        
        Args:
            num_bars (int): Number of bars to generate data for
            min_value (float): Minimum value for generated data
            max_value (float): Maximum value for generated data
            update_rate (float): Rate of change (0-1, higher = more change)
            data_file (str): Path to JSON file to read values from
        """
        self.num_bars = num_bars
        self.min_value = min_value
        self.max_value = max_value
        self.update_rate = update_rate
        self.data_file = data_file
        
        # Initialize with default values
        self.current_values = np.random.uniform(min_value, max_value, num_bars)
        self.target_values = np.random.uniform(min_value, max_value, num_bars)
        
        # Track time for smooth transitions
        self.last_target_update = time.time()
        self.target_update_interval = 0.5  # seconds - check file more frequently
        
        # Track file modification time to only reload when changed
        self.last_file_mtime = 0
        
        # Create default data file if it doesn't exist
        self._create_default_data_file()
    
    def _create_default_data_file(self):
        """Create a default data file if it doesn't exist."""
        if not os.path.exists(self.data_file):
            # Create default data with random values
            data = {
                "values": [float(v) for v in np.random.uniform(self.min_value, self.max_value, self.num_bars)],
                "labels": [f"Bar {i+1}" for i in range(self.num_bars)],
                "title": "Data Visualization"
            }
            
            # Write to file
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Created default data file: {self.data_file}")
    
    def _check_file_for_updates(self):
        """Check if the data file has been updated and load new values if needed."""
        try:
            # Get file modification time
            if not os.path.exists(self.data_file):
                return False
                
            current_mtime = os.path.getmtime(self.data_file)
            
            # If file hasn't been modified since last check, return False
            if current_mtime <= self.last_file_mtime:
                return False
                
            # File has been modified, update the modification time
            self.last_file_mtime = current_mtime
            
            # Read the updated values
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Update target values if present in file
            if "values" in data and len(data["values"]) == self.num_bars:
                self.target_values = np.array(data["values"])
                return True
            
        except Exception as e:
            print(f"Error reading data file: {e}")
        
        return False
        
    def update(self):
        """Update the simulated data.
        
        Returns:
            numpy.ndarray: The updated values
        """
        current_time = time.time()
        
        # Check if we need to update values from file
        if current_time - self.last_target_update > self.target_update_interval:
            self._check_file_for_updates()
            self.last_target_update = current_time
        
        # Move current values toward target values
        diff = self.target_values - self.current_values
        step = diff * self.update_rate
        self.current_values += step
        
        return self.current_values.copy()
    
    def get_values(self):
        """Get the current data values.
        
        Returns:
            numpy.ndarray: The current values
        """
        return self.current_values.copy()
    
    def set_update_rate(self, rate):
        """Set the update rate.
        
        Args:
            rate (float): New update rate (0-1)
        """
        self.update_rate = max(0.0, min(1.0, rate))  # Clamp between 0 and 1

# Example usage of the DataSimulator class
if __name__ == "__main__":
    # Create a simulator for 3 bars
    simulator = DataSimulator(num_bars=3, update_rate=0.1)
    
    # Print values for a few iterations
    for i in range(10):
        values = simulator.update()
        print(f"Iteration {i + 1}: {[round(v, 2) for v in values]}")
        time.sleep(0.5) 
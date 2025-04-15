import datetime
import os

class InputTracker:
    def __init__(self):
        self.last_gesture = None
        self.last_hovered_sprite = None
        
        # Create a log file with timestamp in filename
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join(log_dir, f"interaction_log_{timestamp}.txt")
        
        # Write header to log file
        with open(self.log_filename, 'w') as f:
            f.write("Timestamp, Event Type, Value, Details\n")
        
        print(f"Logging interactions to: {self.log_filename}")
        
    def log_event(self, event_type, value, details=""):
        """Log an event to both console and file"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_line = f"{timestamp}, {event_type}, {value}, {details}"
        
        # Print to console
        # print(log_line)
        
        # Write to log file
        with open(self.log_filename, 'a') as f:
            f.write(log_line + "\n")


# Create a tracker for gestures and gaze
tracker = InputTracker()

# Custom update function to be called by the UI window
def track_inputs(ui_window):
    """Track gestures and gaze and log them"""
    try:
        # Get gesture from gesture detector if available
        if hasattr(ui_window, 'gesture_detection') and ui_window.gesture_detection:
            current_gesture = ui_window.gesture_detection.current_gesture
            # Record gesture on every detection
            tracker.log_event("GESTURE", current_gesture)
            tracker.last_gesture = current_gesture
        
        # Get hovered sprites from shape manager
        shape_manager = ui_window.get_shape_manager()
        hovered_shape = shape_manager.get_hovered_shape()
        
        # Record sprite gaze on every detection
        if hovered_shape and hovered_shape.shape_type == 'sprite':
            tracker.log_event("GAZE", hovered_shape.name, f"ID: {hovered_shape.shape_id}")
            tracker.last_hovered_sprite = hovered_shape
        else:
            # No sprite hovered
            tracker.log_event("GAZE", "None", "No sprite hovered")
            tracker.last_hovered_sprite = None
            
    except Exception as e:
        # Log any exceptions that occur during update
        tracker.log_event("ERROR", str(e), "Exception in update method")


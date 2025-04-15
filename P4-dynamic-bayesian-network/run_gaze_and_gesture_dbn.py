from ui.ui_window import UIWindow
from dbn_helpers import *
from dbn_helpers.input_tracker import tracker  # Import the tracker object
from dbn_helpers.gaze_and_gesture_net import GazeAndGestureNet
import numpy as np
from world_space.curr_world_space import interactions
from ui.bar_plot import BarPlot, BarPlotManager

## disregard 
# Create a simplified UI window without the default plot
class DBNUIWindow(UIWindow):
    def __init__(self, width=800, height=600, title="CMIS DBN Demo"):
        # Skip the setup_bar_plot method entirely - call parent's __init__ first
        super().__init__(width, height, title)
        
        # Then remove/reset the default plot stuff
        self.bar_plot_manager = BarPlotManager()  # Create a new empty manager
        
        # Disconnect the update code
        if hasattr(self, '_update'):
            original_update = self._update
            def new_update():
                # Skip the data simulator update part
                # Update components and call callbacks
                for renderer in self.external_renderers:
                    if hasattr(renderer, 'update'):
                        renderer.update()
                for callback in self.update_callbacks:
                    callback(self)
            self._update = new_update


# create the UI window, and gaze and gesture detectors
window = DBNUIWindow(width=800, height=600, title="CMIS DBN Demo")
# create the DBN
dbn = GazeAndGestureNet()
t = 0
# Add our input tracker to keep track of gaze and gestures detections per frame
window.add_update_callback(track_inputs)

# Create our own bar plot for intentions
intentions_plot = BarPlot(
    x=50,  # Move it more to the left
    y=300,  # Position it higher
    width=700,  # Make it wider to allow more space for labels
    height=200,  # Make it taller
    max_value=1.0,
    num_bars=len(interactions),
    bar_labels=interactions  # Use the interaction labels from world space
)
intentions_plot.set_title("Intention Probabilities")

# Add the plot to the manager
window.bar_plot_manager.add_plot("intentions", intentions_plot)


# Function to process inputs every frame
def process_inputs_every_frame(window):
    global t
    # Get current values from the tracker
    current_gesture = tracker.last_gesture
    current_gaze = tracker.last_hovered_sprite
    
    # Access current gesture
    gesture_value = current_gesture if current_gesture else "None"
    gaze_target = current_gaze.name if current_gaze else "None"

    print(f"Gesture: {gesture_value}, Gaze: {gaze_target}")
    update_dict = {f"t{t}": {f"GO{t}": gaze_target, f"HO{t}": gesture_value}}
    posteriors_this_frame = dbn.update(update_dict, visualize_inference=False, inference_engine="LazyPropagation")
    
    # Check if posteriors_this_frame is a dictionary or a string
    if posteriors_this_frame and isinstance(posteriors_this_frame, dict) and 'I1' in posteriors_this_frame:
        i1_values = posteriors_this_frame['I1']
        window.bar_plot_manager.update_plot_values("intentions", i1_values)
    elif posteriors_this_frame and isinstance(posteriors_this_frame, str):
        print(f"Received string posteriors: {posteriors_this_frame}")
        # Check if it's a string representation of the posteriors we can parse
        if "I1" in posteriors_this_frame and "[" in posteriors_this_frame and "]" in posteriors_this_frame:
            try:
                # Try to extract I1 values from the string output
                i1_start = posteriors_this_frame.find("'I1': [") + 6
                i1_end = posteriors_this_frame.find("]", i1_start) + 1
                i1_str = posteriors_this_frame[i1_start:i1_end]
                i1_values = eval(i1_str)  # Parse the list
                window.bar_plot_manager.update_plot_values("intentions", i1_values)
            except Exception as e:
                print(f"Error parsing posteriors: {e}")
    
    t += 1
# Add our per-frame processing function to the update callbacks
window.add_update_callback(process_inputs_every_frame)

# Run the window
window.run()

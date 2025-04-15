import pygame
# from ui.ui_window import UIWindow
from .hand_tracker import HandTracker

class GestureDetector:
    def __init__(self, ui_window):
        # self.ui_window = ui_window
        # self.shape_manager = ui_window.get_shape_manager()
        
        # Initialize hand tracker with gesture callback and Pygame visualization
        self.hand_tracker = HandTracker(callback=self.on_gesture, visualize_in_pygame=True)
        
        # Store selected shape and dragging state
        self.selected_shape_id = None
        self.is_dragging = False
        
        # Movement speed when using gestures
        self.move_speed = 10
        
        # Gesture history for debugging
        self.gesture_history = []
        self.max_history = 10
        
        # Camera feed display settings
        self.cam_display_width = 320
        self.cam_display_height = 240
        self.cam_display_x = 10
        self.cam_display_y = 10
        self.show_camera_feed = True
        
        # Current status text
        self.status_text = "Idle"
        
        # Current gesture visualization
        self.current_gesture = None
        self.gesture_display_time = 0
        self.gesture_display_duration = 1.0  # Show gesture indicator for 1 second
        
        # Colors for gesture visualization
        self.colors = {
            "drag_up": (0, 255, 0),      # Green
            "drag_down": (255, 0, 0),     # Red
            "drag_left": (255, 165, 0),   # Orange
            "drag_right": (0, 0, 255),    # Blue
            "tap": (255, 255, 0),         # Yellow
        }
        
        # Initialize fonts
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 20)
        
    def start(self):
        """Start the hand tracking."""
        success = self.hand_tracker.start(width=320, height=240)
        if not success:
            print("Failed to start hand tracker. Check camera connection.")
        else:
            print("Gesture detection started. Move your hand in front of the camera.")
        return success
        
    def stop(self):
        """Stop the hand tracking."""
        self.hand_tracker.stop()
        
    def on_gesture(self, gesture):
        """Handle gestures from the hand tracker."""
        # Add to history
        self.gesture_history.append(gesture)
        if len(self.gesture_history) > self.max_history:
            self.gesture_history.pop(0)
            
        # Update current gesture for visualization
        self.current_gesture = gesture
        self.gesture_display_time = pygame.time.get_ticks() / 1000.0  # Current time in seconds
            
        # # Handle tap gesture for selecting an object
        # if gesture == "tap":
        #     # Get currently hovered shape
        #     hovered_shape = self.shape_manager.get_hovered_shape()
        #     if hovered_shape:
        #         # Toggle selection
        #         if self.selected_shape_id == hovered_shape.shape_id:
        #             self.selected_shape_id = None
        #             self.status_text = f"Deselected shape {hovered_shape.shape_id}"
        #         else:
        #             self.selected_shape_id = hovered_shape.shape_id
        #             self.status_text = f"Selected shape {self.selected_shape_id}"
        #             print(f"Selected shape {self.selected_shape_id}")
        #     else:
        #         # Deselect if tapping on empty space
        #         self.selected_shape_id = None
        #         self.status_text = "No shape selected"
            
        # Handle drag gestures for movement
        # elif gesture.startswith("drag_"):
        #     if self.selected_shape_id:
        #         # Move the selected shape
        #         shape = self.shape_manager.get_shape(self.selected_shape_id)
        #         if shape:
        #             if gesture == "drag_up":
        #                 shape.y -= self.move_speed
        #                 self.status_text = f"Moving shape {self.selected_shape_id} up"
        #             elif gesture == "drag_down":
        #                 shape.y += self.move_speed
        #                 self.status_text = f"Moving shape {self.selected_shape_id} down"
        #             elif gesture == "drag_left":
        #                 shape.x -= self.move_speed
        #                 self.status_text = f"Moving shape {self.selected_shape_id} left"
        #             elif gesture == "drag_right":
        #                 shape.x += self.move_speed
        #                 self.status_text = f"Moving shape {self.selected_shape_id} right"
        #     else:
        #         # No shape selected, just update status
        #         direction = gesture.replace("drag_", "")
        #         self.status_text = f"Dragging {direction} (no shape selected)"
                
    def update(self):
        """Update method to be called in the game loop."""
        pass  # Additional updates can be added here
        
    def get_gesture_history(self):
        """Return the gesture history."""
        return self.gesture_history
        
    def toggle_camera_feed(self):
        """Toggle whether to show the camera feed."""
        self.show_camera_feed = not self.show_camera_feed
        
    def render(self, surface):
        """Render the camera feed and hand tracking visualization on the given surface."""
        if not self.show_camera_feed:
            return
        
        # Get the current frame and hand landmarks from hand tracker
        frame_data = self.hand_tracker.get_frame_for_pygame()
        if frame_data is None:
            return
            
        frame_surface, hand_landmarks = frame_data
        
        # Calculate position to render the camera feed
        window_w, window_h = surface.get_size()
        
        # Position in top right corner
        self.cam_display_x = window_w - self.cam_display_width - 10
        self.cam_display_y = 10
        
        try:
            # Create a surface for the camera feed
            camera_surface = pygame.Surface((self.cam_display_width, self.cam_display_height))
            
            # Scale the camera frame to fit in the corner
            scaled_frame = pygame.transform.scale(frame_surface, 
                                               (self.cam_display_width, self.cam_display_height))
            
            # Draw the camera feed as background
            camera_surface.blit(scaled_frame, (0, 0))
            
            # Draw hand landmarks on the camera surface - modified scale factor for better fit
            if hand_landmarks:
                self.hand_tracker.draw_hand_landmarks_pygame(
                    camera_surface, 
                    hand_landmarks,
                    scale_factor=1.0,  # Use natural scale to match camera view better
                    offset_x=0,
                    offset_y=0
                )
            
            # Create an overlay for the gesture visualization
            if self.current_gesture:
                current_time = pygame.time.get_ticks() / 1000.0
                if (current_time - self.gesture_display_time) < self.gesture_display_duration:
                    self._draw_gesture_visualization(camera_surface)
                
            # Draw the camera surface onto the main window
            surface.blit(camera_surface, (self.cam_display_x, self.cam_display_y))
            
            # Draw border around camera feed
            pygame.draw.rect(surface, (200, 200, 200), 
                            (self.cam_display_x - 1, self.cam_display_y - 1, 
                             self.cam_display_width + 2, self.cam_display_height + 2), 1)
            
            # Add labels
            label = self.font.render("Hand Tracking", True, (255, 255, 255))
            surface.blit(label, (self.cam_display_x, self.cam_display_y - 25))
            
            # Draw status text below the camera feed
            status_text = self.small_font.render(self.status_text, True, (255, 255, 255))
            surface.blit(status_text, (self.cam_display_x, self.cam_display_y + self.cam_display_height + 5))
            
        except Exception as e:
            print(f"Error rendering camera feed: {e}")
    
    def _draw_gesture_visualization(self, surface):
        """Draw a visualization of the current gesture on the camera surface."""
        if not self.current_gesture:
            return
            
        # Center of the camera surface
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2
        
        # Size of the gesture indicator (smaller for the camera window)
        indicator_size = min(60, surface.get_width() // 5)
        
        # Get color for current gesture
        color = self.colors.get(self.current_gesture, (255, 255, 255))
        
        # Calculate alpha based on how long the gesture has been displayed
        time_displayed = pygame.time.get_ticks() / 1000.0 - self.gesture_display_time
        alpha_factor = max(0, 1 - time_displayed / self.gesture_display_duration)
        
        # Draw different visualizations based on the gesture
        if self.current_gesture == "drag_up":
            # Draw up arrow
            points = [
                (center_x, center_y - indicator_size // 2),  # Top
                (center_x + indicator_size // 3, center_y + indicator_size // 4),  # Bottom right
                (center_x, center_y),  # Mid bottom
                (center_x - indicator_size // 3, center_y + indicator_size // 4),  # Bottom left
            ]
            pygame.draw.polygon(surface, color, points)
            
        elif self.current_gesture == "drag_down":
            # Draw down arrow
            points = [
                (center_x, center_y + indicator_size // 2),  # Bottom
                (center_x + indicator_size // 3, center_y - indicator_size // 4),  # Top right
                (center_x, center_y),  # Mid top
                (center_x - indicator_size // 3, center_y - indicator_size // 4),  # Top left
            ]
            pygame.draw.polygon(surface, color, points)
            
        elif self.current_gesture == "drag_left":
            # Draw left arrow
            points = [
                (center_x - indicator_size // 2, center_y),  # Left
                (center_x + indicator_size // 4, center_y + indicator_size // 3),  # Bottom right
                (center_x, center_y),  # Mid right
                (center_x + indicator_size // 4, center_y - indicator_size // 3),  # Top right
            ]
            pygame.draw.polygon(surface, color, points)
            
        elif self.current_gesture == "drag_right":
            # Draw right arrow
            points = [
                (center_x + indicator_size // 2, center_y),  # Right
                (center_x - indicator_size // 4, center_y + indicator_size // 3),  # Bottom left
                (center_x, center_y),  # Mid left
                (center_x - indicator_size // 4, center_y - indicator_size // 3),  # Top left
            ]
            pygame.draw.polygon(surface, color, points)
            
        elif self.current_gesture == "tap":
            # Draw tap visualization (tap)
            radius = indicator_size // 3
            pygame.draw.circle(surface, color, (center_x, center_y), radius, 0)
            # Draw a ripple effect
            pygame.draw.circle(surface, color, (center_x, center_y), radius * 1.3, 2)
            pygame.draw.circle(surface, color, (center_x, center_y), radius * 1.6, 1)
        
        # Draw gesture name at the top of the camera view
        text = self.current_gesture.replace('_', ' ').title()
        text_surface = self.small_font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(center_x, 20))
        surface.blit(text_surface, text_rect) 
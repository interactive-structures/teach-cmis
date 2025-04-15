import pygame
import sys
import os

# Add the parent directory to sys.path to find the gesture module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.shape_manager import ShapeManager
from ui.bar_plot import BarPlot, BarPlotManager
from ui.data_simulator import DataSimulator
from gesture.gesture_detector import GestureDetector
from gesture.hand_tracker import HandTracker

class UIWindow:
    def __init__(self, width=800, height=600, title="CMIS DBN Demo"):
        pygame.init()
        self.width = width
        self.height = height
        self.window = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Initialize fonts
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 24)
        
        # Colors
        self.BACKGROUND = (240, 240, 240)
        self.HIGHLIGHT = (100, 200, 255, 100)
        
        # Initialize shape manager
        self.shape_manager = ShapeManager()
        
        # Load and add sprite images
        self.load_and_add_sprites()

        # Initialize bar plot manager
        self.bar_plot_manager = BarPlotManager()
        
        # Initialize data simulator and create a bar plot
        self.setup_bar_plot()

        # External renderers (e.g., gesture detection visualization)
        self.external_renderers = []
        
        # Initialize gesture detection
        self.init_gesture_detection()
        
        # Custom update callbacks
        self.update_callbacks = []
    
    def setup_bar_plot(self):
        """Set up the bar plot and data simulator."""
        # Create a data simulator for 3 bars
        self.data_simulator = DataSimulator(
            num_bars=3,
            min_value=0,
            max_value=100,
            update_rate=0.1
        )
        
        # Create a bar plot for device probabilities
        plot_x = 100
        plot_y = 300
        plot_width = 600
        plot_height = 250
        
        device_plot = BarPlot(
            x=plot_x, 
            y=plot_y, 
            width=plot_width, 
            height=plot_height,
            max_value=100,
            num_bars=3,
            bar_labels=["Lamp", "Speaker", "Webcam"]
        )
        
        device_plot.set_title("Device Activation Probabilities (%)")
        
        # Add the plot to the manager
        self.bar_plot_manager.add_plot("devices", device_plot)
    
    def init_gesture_detection(self):
        """Initialize gesture detection module."""
        try:
            
            
            # Create the gesture detection module
            self.gesture_detection = GestureDetector(self)
            
            # Add it as an external renderer
            self.add_external_renderer(self.gesture_detection)
            
            # Start the finger tracking
            success = self.gesture_detection.start()
            if success:
                print("Gesture detection started successfully")
            else:
                print("Failed to start gesture detection. Check camera connection.")
        except ImportError as e:
            print(f"Gesture detection not available: {e}")
            self.gesture_detection = None
    
    def load_and_add_sprites(self):
        """Load sprite images and add them to the shape manager."""

        lamp_path = 'assets/lamp.png'
        # Load and resize the image to match sprite dimensions
        lamp_img = pygame.image.load(lamp_path).convert_alpha()
        lamp_width, lamp_height = 100, 100
        lamp_img = pygame.transform.scale(lamp_img, (lamp_width, lamp_height))
        lamp_id = self.shape_manager.add_sprite(x=100, y=100, width=lamp_width, height=lamp_height, color="white", name="Lamp")
        self.shape_manager.set_sprite_image(lamp_id, lamp_img)

        speaker_path = 'assets/speaker.png'
        # Load and resize the image to match sprite dimensions
        speaker_img = pygame.image.load(speaker_path).convert_alpha()
        speaker_width, speaker_height = 100, 100
        speaker_img = pygame.transform.scale(speaker_img, (speaker_width, speaker_height))
        speaker_id = self.shape_manager.add_sprite(x=200, y=100, width=speaker_width, height=speaker_height, color="white", name="Speaker")
        self.shape_manager.set_sprite_image(speaker_id, speaker_img)

        webcam_path = 'assets/webcam.png'
        # Load and resize the image to match sprite dimensions
        webcam_img = pygame.image.load(webcam_path).convert_alpha()
        webcam_width, webcam_height = 100, 100
        webcam_img = pygame.transform.scale(webcam_img, (webcam_width, webcam_height))
        webcam_id = self.shape_manager.add_sprite(x=300, y=100, width=webcam_width, height=webcam_height, color="white", name="Webcam")
        self.shape_manager.set_sprite_image(webcam_id, webcam_img)

    
    def run(self):
        """Start the main window loop."""
        print("UI Window running. Press 'q' to quit.")
        self.running = True
        
        try:
            while self.running:
                # Check for quit events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        break
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            print("Q key pressed, quitting.")
                            self.running = False
                            break
                        
                    if event.type == pygame.MOUSEMOTION:
                        mouse_pos = pygame.mouse.get_pos()
                        self.shape_manager.update_hover(*mouse_pos)
                
                # Update and render
                self._update()
                self._render()
                self.clock.tick(60)  # 60 FPS
        finally:
            print("Closing pygame window...")
            # Stop gesture detection if it's running
            if hasattr(self, 'gesture_detection') and self.gesture_detection:
                self.gesture_detection.stop()
            pygame.quit()
            print("Pygame closed.")
    
    def _update(self):
        """Update game state."""
        # Update the data simulator and bar plot values
        if hasattr(self, 'data_simulator'):
            new_values = self.data_simulator.update()
            self.bar_plot_manager.update_plot_values("devices", new_values)
        
        # Update any components that need updating
        for renderer in self.external_renderers:
            if hasattr(renderer, 'update'):
                renderer.update()
                
        # Call custom update callbacks
        for callback in self.update_callbacks:
            callback(self)
    
    def _render(self):
        """Render the UI."""
        self.window.fill(self.BACKGROUND)
        
        # Draw all shapes
        for shape in self.shape_manager.get_all_shapes():
            if shape.shape_type == 'rectangle':
                pygame.draw.rect(
                    self.window,
                    shape.color,
                    (shape.x, shape.y, shape.width, shape.height)
                )
                
                # Draw highlight if hovered
                if shape.is_hovered:
                    pygame.draw.rect(
                        self.window,
                        self.HIGHLIGHT,
                        (shape.x - 2, shape.y - 2, shape.width + 4, shape.height + 4),
                        3
                    )
                    
            elif shape.shape_type == 'circle':
                center = (shape.x + shape.width // 2, shape.y + shape.height // 2)
                radius = min(shape.width, shape.height) // 2
                
                pygame.draw.circle(
                    self.window,
                    shape.color,
                    center,
                    radius
                )
                
                # Draw highlight if hovered
                if shape.is_hovered:
                    pygame.draw.circle(
                        self.window,
                        self.HIGHLIGHT,
                        center,
                        radius + 2,
                        3
                    )
            
            elif shape.shape_type == 'sprite':
                # Draw sprite image if available
                if shape.sprite_image:
                    self.window.blit(shape.sprite_image, (shape.x, shape.y))
                else:
                    # Fallback: draw a placeholder rectangle
                    pygame.draw.rect(
                        self.window,
                        shape.color,
                        (shape.x, shape.y, shape.width, shape.height)
                    )
                
                # Draw highlight if hovered
                if shape.is_hovered:
                    pygame.draw.rect(
                        self.window,
                        self.HIGHLIGHT,
                        (shape.x - 2, shape.y - 2, shape.width + 4, shape.height + 4),
                        3
                    )
        
        # Draw hovered shape info
        hovered_shape = self.shape_manager.get_hovered_shape()
        if hovered_shape:
            if hovered_shape.name:
                info_text = f"{hovered_shape.name} (ID: {hovered_shape.shape_id})"
            else:
                info_text = f"Shape {hovered_shape.shape_id}: {hovered_shape.shape_type}"
            text_surface = self.font.render(info_text, True, (0, 0, 0))
            self.window.blit(text_surface, (10, self.height - 30))
        
        # Render all bar plots
        self.bar_plot_manager.render_all(self.window)
        
        # Call external renderers
        for renderer in self.external_renderers:
            if hasattr(renderer, 'render'):
                renderer.render(self.window)
        
        pygame.display.flip()
    
    def get_shape_manager(self):
        """Return the shape manager for external use."""
        return self.shape_manager
    
    def add_external_renderer(self, renderer):
        """Add an external renderer to be called during rendering."""
        if renderer not in self.external_renderers:
            self.external_renderers.append(renderer)
    
    def quit(self):
        """Properly quit pygame and clean up resources."""
        self.running = False

    def add_update_callback(self, callback):
        """Add a custom update callback function.
        
        The callback will be called during each update cycle with the UIWindow instance.
        """
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)

    def remove_update_callback(self, callback):
        """Remove a previously added update callback."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)

# Main execution block
if __name__ == "__main__":
    window = UIWindow(width=800, height=600, title="CMIS DBN Demo")
    window.run()


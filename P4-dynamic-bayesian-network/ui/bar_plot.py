import pygame
import numpy as np

class BarPlot:
    def __init__(self, x, y, width, height, max_value=100, num_bars=3, bar_labels=None):
        """Initialize a bar plot at the given position and size.
        
        Args:
            x (int): X position of the plot
            y (int): Y position of the plot
            width (int): Width of the entire plot
            height (int): Height of the entire plot
            max_value (float): Maximum value for scaling the bars
            num_bars (int): Number of bars to display
            bar_labels (list): Optional list of labels for each bar
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_value = max_value
        self.num_bars = num_bars
        
        # Set default bar values
        self.values = np.zeros(num_bars)
        
        # Default colors for bars
        self.colors = [
            (255, 0, 0),     # Red
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (255, 255, 0),   # Yellow
            (255, 0, 255),   # Magenta
            (0, 255, 255),   # Cyan
        ]
        
        # Add more default colors if needed
        while len(self.colors) < num_bars:
            self.colors.append((
                np.random.randint(100, 256),
                np.random.randint(100, 256),
                np.random.randint(100, 256)
            ))
        
        # Bar labels
        self.bar_labels = bar_labels if bar_labels else [f"Bar {i+1}" for i in range(num_bars)]
        
        # Font for labels
        self.font = pygame.font.SysFont(None, 20)
        
        # Title
        self.title = "Data Visualization"
        self.title_font = pygame.font.SysFont(None, 24)
        
        # Background and border
        self.bg_color = (240, 240, 240)
        self.border_color = (180, 180, 180)
        self.text_color = (0, 0, 0)
        
        # Calculate bar dimensions
        self._calculate_bar_dimensions()
    
    def _calculate_bar_dimensions(self):
        """Calculate the dimensions for each bar based on plot size and number of bars."""
        # Padding inside the plot
        self.padding = 40
        
        # Usable area
        self.plot_width = self.width - 2 * self.padding
        self.plot_height = self.height - 2 * self.padding
        
        # Calculate individual bar width - use smaller width and larger spacing
        self.bar_width = self.plot_width / (self.num_bars * 3)  # Give 2/3 of space to spacing
        self.bar_spacing = self.bar_width * 2  # Twice as much space between bars
    
    def update_values(self, values):
        """Update the values for all bars.
        
        Args:
            values (list): List of values for each bar
        """
        if len(values) != self.num_bars:
            raise ValueError(f"Expected {self.num_bars} values, got {len(values)}")
        
        self.values = np.array(values)
    
    def update_bar_value(self, bar_index, value):
        """Update the value for a specific bar.
        
        Args:
            bar_index (int): Index of the bar to update
            value (float): New value for the bar
        """
        if bar_index < 0 or bar_index >= self.num_bars:
            raise ValueError(f"Bar index {bar_index} out of range (0-{self.num_bars-1})")
        
        self.values[bar_index] = value
    
    def set_title(self, title):
        """Set the title of the plot.
        
        Args:
            title (str): Title text
        """
        self.title = title
    
    def set_bar_labels(self, labels):
        """Set the labels for all bars.
        
        Args:
            labels (list): List of label strings
        """
        if len(labels) != self.num_bars:
            raise ValueError(f"Expected {self.num_bars} labels, got {len(labels)}")
        
        self.bar_labels = labels
    
    def set_bar_colors(self, colors):
        """Set the colors for all bars.
        
        Args:
            colors (list): List of RGB color tuples
        """
        if len(colors) != self.num_bars:
            raise ValueError(f"Expected {self.num_bars} colors, got {len(colors)}")
        
        self.colors = colors
    
    def render(self, surface):
        """Render the bar plot on the given surface.
        
        Args:
            surface: Pygame surface to render on
        """
        # Draw background and border
        pygame.draw.rect(surface, self.bg_color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, self.border_color, (self.x, self.y, self.width, self.height), 2)
        
        # Draw title
        title_surf = self.title_font.render(self.title, True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.x + self.width//2, self.y + 15))
        surface.blit(title_surf, title_rect)
        
        # Draw bars
        for i in range(self.num_bars):
            # Calculate bar position and height
            bar_x = self.x + self.padding + i * (self.bar_width + self.bar_spacing)
            
            # Scale value to fit in plot height
            # Clamp value to max to prevent exceeding plot area
            scaled_value = min(self.values[i], self.max_value) / self.max_value
            
            bar_height = int(scaled_value * self.plot_height)
            bar_y = self.y + self.height - self.padding - bar_height
            
            # Draw the bar
            pygame.draw.rect(
                surface, 
                self.colors[i], 
                (bar_x, bar_y, self.bar_width, bar_height)
            )
            
            # Draw border around the bar
            pygame.draw.rect(
                surface, 
                (100, 100, 100), 
                (bar_x, bar_y, self.bar_width, bar_height),
                1
            )
            
            # Draw value above the bar
            value_text = f"{self.values[i]:.1f}"
            value_surf = self.font.render(value_text, True, self.text_color)
            value_rect = value_surf.get_rect(centerx=bar_x + self.bar_width/2, bottom=bar_y - 5)
            surface.blit(value_surf, value_rect)
            
            # Draw label below the bar at an angle
            label_surf = self.font.render(self.bar_labels[i], True, self.text_color)
            
            # Create a new rotated surface for the label (30 degrees)
            angle = 30
            rotated_label = pygame.transform.rotate(label_surf, angle)
            
            # Position the rotated label
            label_rect = rotated_label.get_rect(
                centerx=bar_x + self.bar_width/2,
                top=self.y + self.height - self.padding + 5
            )
            surface.blit(rotated_label, label_rect)


class BarPlotManager:
    """Manager class for handling multiple bar plots and their updates."""
    
    def __init__(self):
        self.plots = {}
    
    def add_plot(self, plot_id, bar_plot):
        """Add a new bar plot with the given ID.
        
        Args:
            plot_id: Unique identifier for the plot
            bar_plot: BarPlot instance
        """
        self.plots[plot_id] = bar_plot
    
    def remove_plot(self, plot_id):
        """Remove a plot by its ID."""
        if plot_id in self.plots:
            del self.plots[plot_id]
    
    def get_plot(self, plot_id):
        """Get a plot by its ID."""
        return self.plots.get(plot_id)
    
    def update_plot_values(self, plot_id, values):
        """Update values for a specific plot.
        
        Args:
            plot_id: ID of the plot to update
            values: New values for the plot's bars
        """
        plot = self.get_plot(plot_id)
        if plot:
            plot.update_values(values)
    
    def render_all(self, surface):
        """Render all plots on the given surface."""
        for plot in self.plots.values():
            plot.render(surface) 
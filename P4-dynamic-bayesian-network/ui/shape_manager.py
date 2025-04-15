class Shape:
    def __init__(self, shape_id, shape_type, x, y, width, height, color, name=None):
        self.shape_id = shape_id
        self.shape_type = shape_type  # 'rectangle', 'circle', 'sprite', etc.
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.is_hovered = False
        self.sprite_image = None  # Will hold the image for sprite shapes
        self.name = name  # Name property for shapes, particularly useful for sprites

    def contains_point(self, point_x, point_y):
        """Check if the point is inside the shape."""
        if self.shape_type == 'rectangle':
            return (self.x <= point_x <= self.x + self.width and 
                    self.y <= point_y <= self.y + self.height)
        elif self.shape_type == 'circle':
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            radius = min(self.width, self.height) // 2
            return ((point_x - center_x) ** 2 + (point_y - center_y) ** 2) <= radius ** 2
        elif self.shape_type == 'sprite':
            # For sprites, use the same rectangular hit detection
            return (self.x <= point_x <= self.x + self.width and 
                    self.y <= point_y <= self.y + self.height)
        return False

    def set_sprite_image(self, image):
        """Set the image for a sprite shape."""
        if self.shape_type == 'sprite':
            self.sprite_image = image

class ShapeManager:
    def __init__(self):
        self._shapes = {}
        self._next_id = 1
        self._currently_hovered = None
        self._hover_callbacks = []

    def add_shape(self, shape_type, x, y, width, height, color, name=None):
        """Add a new shape and return its ID."""
        shape_id = self._next_id
        self._next_id += 1
        self._shapes[shape_id] = Shape(shape_id, shape_type, x, y, width, height, color, name)
        return shape_id

    def add_sprite(self, x, y, width, height, color, image=None, name=None):
        """Add a sprite shape and return its ID."""
        shape_id = self.add_shape('sprite', x, y, width, height, color, name)
        if image:
            self._shapes[shape_id].set_sprite_image(image)
        return shape_id
        
    def set_sprite_image(self, shape_id, image):
        """Set the image for an existing sprite shape."""
        shape = self.get_shape(shape_id)
        if shape and shape.shape_type == 'sprite':
            shape.set_sprite_image(image)

    def remove_shape(self, shape_id):
        """Remove a shape by its ID."""
        if shape_id in self._shapes:
            del self._shapes[shape_id]
            if self._currently_hovered == shape_id:
                self._currently_hovered = None

    def get_shape(self, shape_id):
        """Get a shape by its ID."""
        return self._shapes.get(shape_id)

    def get_all_shapes(self):
        """Return all shapes."""
        return list(self._shapes.values())

    def update_hover(self, mouse_x, mouse_y):
        """Update hover state based on mouse position."""
        prev_hovered = self._currently_hovered
        self._currently_hovered = None
        
        # Reset all hover states
        for shape in self._shapes.values():
            shape.is_hovered = False
        
        # Find the topmost shape that contains the point
        # Assuming shapes are drawn in order of ID, higher IDs are on top
        for shape_id in sorted(self._shapes.keys(), reverse=True):
            shape = self._shapes[shape_id]
            if shape.contains_point(mouse_x, mouse_y):
                shape.is_hovered = True
                self._currently_hovered = shape_id
                break
        
        # If hover state changed, notify callbacks
        if prev_hovered != self._currently_hovered:
            self._notify_hover_change(prev_hovered, self._currently_hovered)
    
    
    def get_hovered_shape(self):
        """Return the currently hovered shape or None."""
        if self._currently_hovered is not None:
            return self._shapes.get(self._currently_hovered)
        return None

    def register_hover_callback(self, callback):
        """Register a callback for hover events.
        
        Callback will be called with (previous_shape_id, current_shape_id)
        where either may be None.
        """
        self._hover_callbacks.append(callback)
        
    def unregister_hover_callback(self, callback):
        """Unregister a hover callback."""
        if callback in self._hover_callbacks:
            self._hover_callbacks.remove(callback)
            
    def _notify_hover_change(self, prev_shape_id, current_shape_id):
        """Notify all registered callbacks about hover change."""
        for callback in self._hover_callbacks:
            callback(prev_shape_id, current_shape_id)

    def set_name(self, shape_id, name):
        """Set the name for a shape."""
        shape = self.get_shape(shape_id)
        if shape:
            shape.name = name
            
    def get_name(self, shape_id):
        """Get the name of a shape."""
        shape = self.get_shape(shape_id)
        if shape:
            return shape.name
        return None 
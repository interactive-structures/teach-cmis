import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import platform
import pygame

class HandTracker:
    def __init__(self, callback=None, mirror=True, visualize_in_pygame=False):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize MediaPipe Hands
        self.hands = self.mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_hands=1
        )
        
        self.mirror = mirror  # Mirror the camera feed
        self.running = False
        self.thread = None
        self.cap = None
        
        # Callback function to handle gesture events
        self.callback = callback
        
        # Variables for tracking hand movements
        self.prev_finger_positions = None
        self.finger_tips_idx = [4, 8, 12, 16, 20]  # Thumb, index, middle, ring, pinky tips
        self.palm_idx = 0  # Wrist landmark
        
        # Gesture tracking
        self.last_gesture_time = time.time()
        self.gesture_cooldown = 0.3  # seconds - reduced cooldown for more responsive movement
        self.last_gesture = None
        
        # Movement tracking - reduce threshold for more sensitive detection
        self.movement_threshold = 0.001  # Reduced threshold for movement detection
        
        # Pinch tracking
        self.pinch_threshold = 0.05  # Threshold for pinch detection
        self.is_pinched = False
        
        # Index finger up detection
        self.index_up_threshold = 0.1  # Height difference for index finger up detection
        self.index_up_cooldown = 0.5  # Seconds between index up detections
        self.last_index_up_time = 0
        
        # For visualization in Pygame window
        self.visualize_in_pygame = visualize_in_pygame
        self.current_frame = None
        self.hand_landmarks_data = None
        self.frame_ready = False
        
        # Check platform for macOS-specific workarounds
        self.is_macos = platform.system() == 'Darwin'
        
        # Debug visualization
        self.debug_info = {}
        
    def start(self, camera_index=0, width=320, height=240):
        """Start the webcam and hand tracking in a separate thread."""
        if self.running:
            return
            
        # Initialize webcam
        self.cap = cv2.VideoCapture(camera_index)
        
        # macOS sometimes needs multiple attempts to open the camera
        if self.is_macos:
            attempts = 0
            while not self.cap.isOpened() and attempts < 3:
                print(f"Retrying camera open... attempt {attempts+1}")
                self.cap.release()
                self.cap = cv2.VideoCapture(camera_index)
                attempts += 1
                time.sleep(0.5)
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            return False
            
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        return True
        
    def stop(self):
        """Stop hand tracking and release the webcam."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
        
        # Only destroy windows if not visualizing in Pygame
        if not self.visualize_in_pygame:
            try:
                cv2.destroyAllWindows()
            except:
                pass
        
    def _run(self):
        """Main loop for processing webcam frames and detecting hand gestures."""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                time.sleep(0.1)  # Short delay to prevent CPU spinning
                continue
                
            # Mirror the frame if needed
            if self.mirror:
                frame = cv2.flip(frame, 1)
                
            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame with MediaPipe Hands
            results = self.hands.process(frame_rgb)
            
            # Store data for visualization
            self.hand_landmarks_data = results.multi_hand_landmarks
            
            # Draw hand landmarks and process gestures
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw the hand landmarks if not visualizing in Pygame
                    if not self.visualize_in_pygame:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style()
                        )
                    
                    # Process hand movements and detect gestures
                    self._process_hand_landmarks(hand_landmarks)
            else:
                # Reset previous positions if no hand is detected
                self.prev_finger_positions = None
            
            # Store the current frame for Pygame visualization
            if self.visualize_in_pygame:
                self.current_frame = frame_rgb  # RGB for Pygame
                self.frame_ready = True
            # Display the frame in OpenCV window if not visualizing in Pygame
            elif not self.is_macos:  # Skip showing window on macOS to avoid issues
                try:
                    cv2.imshow('Hand Tracking', frame)
                    
                    # Break the loop on 'q' key press
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                except Exception as e:
                    print(f"Error displaying frame: {e}")
                    break
                
        self.running = False
        
    def _process_hand_landmarks(self, hand_landmarks):
        """Process hand landmarks to detect movements and gestures."""
        # Extract finger positions (normalized to 0-1)
        finger_positions = []
        for idx in range(21):  # MediaPipe detects 21 landmarks per hand
            finger_positions.append((
                hand_landmarks.landmark[idx].x,
                hand_landmarks.landmark[idx].y
            ))
        
        # Detect pinch between thumb and index finger
        thumb_tip = finger_positions[4]
        index_tip = finger_positions[8]
        
        pinch_distance = np.sqrt((thumb_tip[0] - index_tip[0])**2 + 
                               (thumb_tip[1] - index_tip[1])**2)
        
        # Update debug info
        self.debug_info['pinch_distance'] = pinch_distance
        
        # Detect index finger up gesture (pointing)
        index_tip = finger_positions[8]  # Index fingertip
        index_pip = finger_positions[6]  # Index PIP joint (middle knuckle)
        index_mcp = finger_positions[5]  # Index MCP joint (base knuckle)
        middle_tip = finger_positions[12]  # Middle fingertip
        
        # Index is pointing up if:
        # 1. Index finger is extended (tip is higher/lower than base depending on camera orientation)
        # 2. Other fingers are not extended (middle finger is not extended)
        index_extended = (index_tip[1] < index_mcp[1] - self.index_up_threshold)
        middle_not_extended = (middle_tip[1] > index_mcp[1] - self.index_up_threshold/2)
        
        # Check if index finger is pointing up and other fingers are down
        is_index_up = index_extended and middle_not_extended and not self.is_pinched
        
        # Detect index up gesture with cooldown
        if is_index_up and time.time() - self.last_index_up_time > self.index_up_cooldown:
            self.last_index_up_time = time.time()
            self._trigger_gesture("press down")
        
        # Toggle pinch state if distance crosses threshold
        prev_pinch_state = self.is_pinched
        if not self.is_pinched and pinch_distance < self.pinch_threshold:
            self.is_pinched = True
            # Don't trigger a gesture for pinch_start anymore, just track the state
        elif self.is_pinched and pinch_distance > self.pinch_threshold * 1.5:
            self.is_pinched = False
            # Don't trigger a gesture for pinch_end anymore, just track the state
        
        # Use wrist position for more stable movement tracking
        wrist_pos = finger_positions[0]  # Wrist landmark
        
        # Calculate direction of movement, but only if we're pinching
        if self.prev_finger_positions and self.is_pinched:
            prev_wrist_pos = self.prev_finger_positions[0]
            
            # Calculate movement deltas
            dx = wrist_pos[0] - prev_wrist_pos[0]
            dy = wrist_pos[1] - prev_wrist_pos[1]
            
            # Update debug info
            self.debug_info['dx'] = dx
            self.debug_info['dy'] = dy
            
            # Only process significant movements while pinching
            if time.time() - self.last_gesture_time > self.gesture_cooldown:
                # Determine the primary direction of movement
                if abs(dx) > self.movement_threshold or abs(dy) > self.movement_threshold:
                    if abs(dx) > abs(dy):
                        # Horizontal movement is primary
                        if dx > 0:
                            self._trigger_gesture("slide right")
                        else:
                            self._trigger_gesture("slide left")
                    else:
                        # Vertical movement is primary
                        if dy > 0:
                            self._trigger_gesture("slide down")
                        else:
                            self._trigger_gesture("slide up")
        
        # Store current positions for next frame
        self.prev_finger_positions = finger_positions
        
    def _trigger_gesture(self, gesture):
        """Trigger a gesture event with cooldown."""
        if time.time() - self.last_gesture_time > self.gesture_cooldown:
            self.last_gesture_time = time.time()
            self.last_gesture = gesture
            
            # Call the callback if registered
            if self.callback:
                self.callback(gesture)
            # else:
            #     # Only print if no callback is registered
            #     print(f"Gesture detected: {gesture}")
                
    def get_last_gesture(self):
        """Get the last detected gesture."""
        return self.last_gesture
    
    def get_frame_for_pygame(self):
        """Returns current frame as a pygame surface for rendering in the main window."""
        if not self.frame_ready or self.current_frame is None:
            return None
            
        # Convert OpenCV frame to Pygame surface
        frame = self.current_frame
        h, w = frame.shape[:2]
        pygame_frame = pygame.Surface((w, h))
        
        # Convert the OpenCV RGB image to Pygame surface format
        pygame_frame = pygame.image.frombuffer(frame.tobytes(), (w, h), 'RGB')
        
        return pygame_frame, self.hand_landmarks_data
    
    def draw_hand_landmarks_pygame(self, surface, hand_landmarks_data, scale_factor=1.0, offset_x=0, offset_y=0):
        """Draw hand landmarks on a pygame surface."""
        if hand_landmarks_data is None:
            return
            
        for hand_landmarks in hand_landmarks_data:
            # Calculate the bounding box of the hand to ensure proper positioning
            min_x, min_y = 1.0, 1.0
            max_x, max_y = 0.0, 0.0
            
            # Find the bounds of the hand
            for landmark in hand_landmarks.landmark:
                min_x = min(min_x, landmark.x)
                min_y = min(min_y, landmark.y)
                max_x = max(max_x, landmark.x)
                max_y = max(max_y, landmark.y)
            
            # Calculate scale for the hand itself to better fit the video
            hand_width = max_x - min_x
            hand_height = max_y - min_y
            
            # Adjust scale factor to make the hand more proportional
            # This helps with the skeleton appearing too large or misplaced
            adjusted_scale = scale_factor * 0.9  # Slightly reduce the overall scale
            
            # Draw connections between landmarks
            for connection in self.mp_hands.HAND_CONNECTIONS:
                start_idx, end_idx = connection
                
                # Get the coordinates
                start_x = int(hand_landmarks.landmark[start_idx].x * surface.get_width() * adjusted_scale) + offset_x
                start_y = int(hand_landmarks.landmark[start_idx].y * surface.get_height() * adjusted_scale) + offset_y
                end_x = int(hand_landmarks.landmark[end_idx].x * surface.get_width() * adjusted_scale) + offset_x
                end_y = int(hand_landmarks.landmark[end_idx].y * surface.get_height() * adjusted_scale) + offset_y
                
                # Draw the connection line
                pygame.draw.line(surface, (0, 255, 0), (start_x, start_y), (end_x, end_y), 2)
                
            # Draw landmark points
            for idx, landmark in enumerate(hand_landmarks.landmark):
                x = int(landmark.x * surface.get_width() * adjusted_scale) + offset_x
                y = int(landmark.y * surface.get_height() * adjusted_scale) + offset_y
                
                # Draw larger circles for fingertips
                if idx in self.finger_tips_idx:
                    pygame.draw.circle(surface, (255, 0, 0), (x, y), 4)  # Reduced from 6 to 4
                else:
                    pygame.draw.circle(surface, (0, 0, 255), (x, y), 3)  # Reduced from 4 to 3
            
            # Show pinch state
            font = pygame.font.SysFont(None, 18)
            pinch_status = "Pinching" if self.is_pinched else "Not Pinching"
            status_text = font.render(pinch_status, True, (255, 255, 255))
            surface.blit(status_text, (offset_x + 10, offset_y + 10))
            
            # Display debug info when pinching
            if self.is_pinched:
                # Format the movement values for display
                dx_text = f"dx: {self.debug_info.get('dx', 0):.4f}"
                dy_text = f"dy: {self.debug_info.get('dy', 0):.4f}"
                threshold_text = f"threshold: {self.movement_threshold:.4f}"
                
                dx_surface = font.render(dx_text, True, (255, 255, 0))
                dy_surface = font.render(dy_text, True, (255, 255, 0))
                threshold_surface = font.render(threshold_text, True, (255, 255, 0))
                
                # Position the debug text
                surface.blit(dx_surface, (offset_x + 10, offset_y + 30))
                surface.blit(dy_surface, (offset_x + 10, offset_y + 50))
                surface.blit(threshold_surface, (offset_x + 10, offset_y + 70)) 
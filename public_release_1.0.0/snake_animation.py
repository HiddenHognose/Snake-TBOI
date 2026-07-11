"""
COMPLETE SNAKE ANIMATION CLASS - ALL IN ONE

Snake sprite animation system with rendering, direction, and all animation logic.
Integrated with palette recoloring system.
"""

import math
import pygame
from PIL import Image
import numpy as np

# OPTIMIZATION: Global cache for snake animation frames to avoid expensive processing
_snake_sprite_sheet_cache = None
_snake_frames_cache = {}  # (palette_row, size) -> dict of animation states
_snake_palette_cache = None  # Cache the palette image
_snake_palette_colors_cache = {}  # Cache extracted colors: (row_index) -> list of colors
_snake_base_pil_cache = None  # Cache the base PIL image
_snake_base_array_cache = None  # Cache the base numpy array
_snake_row0_colors_cache = None  # Cache row 0 colors from palette

def get_snake_palette_row_colors(row_index):
    """Get colors from a specific row in the snake palette (0-indexed, row 1 = index 0) - CACHED"""
    # OPTIMIZATION: Check cache first
    if row_index in _snake_palette_colors_cache:
        return _snake_palette_colors_cache[row_index]
    
    try:
        global _snake_palette_cache
        # OPTIMIZATION: Load palette image once and cache it
        if _snake_palette_cache is None:
            _snake_palette_cache = Image.open('snake_sprite_sheet_palette.png')
            _snake_palette_cache = _snake_palette_cache.convert('RGB')
        
        swatch_size = 50
        row_y = row_index * swatch_size
        
        # Extract 9 colors from the row (columns 0-8, including column 8 for black pixels)
        colors = []
        for i in range(9):
            x = i * swatch_size
            color = _snake_palette_cache.getpixel((x, row_y))
            colors.append(color)
        
        # OPTIMIZATION: Cache the result
        _snake_palette_colors_cache[row_index] = colors
        return colors
    except Exception as e:
        return None

def recolor_snake_sprite_with_palette(sprite, palette_row_index):
    """Recolor snake sprite using colors from a palette row"""
    if sprite is None:
        return None
    
    # Get palette colors for this row
    palette_colors = get_snake_palette_row_colors(palette_row_index)
    if palette_colors is None:
        return sprite
    
    # OPTIMIZATION: Load the base image once and cache it
    try:
        global _snake_base_pil_cache, _snake_base_array_cache, _snake_palette_cache, _snake_row0_colors_cache
        
        # Load and cache base PIL image
        if _snake_base_pil_cache is None:
            _snake_base_pil_cache = Image.open('snake_sprite_sheet_palettebase.png')
            if _snake_base_pil_cache.mode != 'RGBA':
                _snake_base_pil_cache = _snake_base_pil_cache.convert('RGBA')
        
        # Cache base array
        if _snake_base_array_cache is None:
            _snake_base_array_cache = np.array(_snake_base_pil_cache)
        
        base_array = _snake_base_array_cache
        
        # OPTIMIZATION: Cache row 0 colors from palette
        if _snake_row0_colors_cache is None:
            if _snake_palette_cache is None:
                _snake_palette_cache = Image.open('snake_sprite_sheet_palette.png')
                _snake_palette_cache = _snake_palette_cache.convert('RGB')
            swatch_size = 50
            _snake_row0_colors_cache = []
            max_cols = _snake_palette_cache.size[0] // swatch_size
            for i in range(max_cols):
                x = i * swatch_size
                _snake_row0_colors_cache.append(_snake_palette_cache.getpixel((x, 0)))  # Row 0
        
        row0_colors = _snake_row0_colors_cache
        
        # Get unique colors from the base image (non-transparent)
        # OPTIMIZATION: Use numpy for faster color extraction
        mask = base_array[:, :, 3] > 0  # Non-transparent pixels
        rgb_array = base_array[mask, :3]  # Get RGB values
        # Convert to tuples and get unique colors
        original_colors = set(tuple(int(c) for c in rgb) for rgb in rgb_array)
        
        # Create mapping: original color -> palette color (by matching to row 0 colors, then mapping to target row)
        # Find which column each original color matches in row 0
        def color_distance(c1, c2):
            return sum((a - b) ** 2 for a, b in zip(c1, c2))
        
        # Check if a color is black (should route to column 8)
        def is_black(r, g, b):
            return r < 10 and g < 10 and b < 10
        
        color_mapping = {}
        for original_color in original_colors:
            # Black pixels should route to column 8 of the target palette row
            if is_black(original_color[0], original_color[1], original_color[2]):
                # Column 8 is index 8 (0-indexed)
                if len(palette_colors) > 8:
                    color_mapping[original_color] = palette_colors[8]  # Route to column 8
                else:
                    # Fallback if column 8 doesn't exist
                    color_mapping[original_color] = palette_colors[-1] if palette_colors else original_color
                continue
            
            # Find the closest matching color in row 0 (by column)
            best_match_idx = 0
            best_distance = float('inf')
            for i, row0_color in enumerate(row0_colors):
                dist = color_distance(original_color, row0_color)
                if dist < best_distance:
                    best_distance = dist
                    best_match_idx = i
            
            # Map to the same column in the target palette row
            if best_match_idx < len(palette_colors):
                color_mapping[original_color] = palette_colors[best_match_idx]
            else:
                # If column index is out of range, use the last palette color
                color_mapping[original_color] = palette_colors[-1] if palette_colors else original_color
        
        # Now convert the pygame sprite to PIL and apply the mapping
        size = sprite.get_size()
        
        # Try using surfarray first (faster if available)
        try:
            pixel_array = pygame.surfarray.array3d(sprite)
            alpha_array = pygame.surfarray.array_alpha(sprite)
            
            # Convert to numpy array format (height, width, channels)
            img_array = np.zeros((size[1], size[0], 4), dtype=np.uint8)
            img_array[:, :, 0] = np.swapaxes(pixel_array[:, :, 0], 0, 1)
            img_array[:, :, 1] = np.swapaxes(pixel_array[:, :, 1], 0, 1)
            img_array[:, :, 2] = np.swapaxes(pixel_array[:, :, 2], 0, 1)
            img_array[:, :, 3] = np.swapaxes(alpha_array, 0, 1)
        except:
            # Fallback: read pixels manually
            img_array = np.zeros((size[1], size[0], 4), dtype=np.uint8)
            for y in range(size[1]):
                for x in range(size[0]):
                    color = sprite.get_at((x, y))
                    img_array[y, x, 0] = color[0]
                    img_array[y, x, 1] = color[1]
                    img_array[y, x, 2] = color[2]
                    img_array[y, x, 3] = color[3]
        
        # Apply the color mapping (black pixels are mapped to column 8)
        for original_color, new_color in color_mapping.items():
            mask = (img_array[:, :, 0] == original_color[0]) & \
                   (img_array[:, :, 1] == original_color[1]) & \
                   (img_array[:, :, 2] == original_color[2]) & \
                   (img_array[:, :, 3] > 0)
            img_array[mask, 0] = new_color[0]
            img_array[mask, 1] = new_color[1]
            img_array[mask, 2] = new_color[2]
        
        # Convert back to pygame surface
        recolored_pil = Image.fromarray(img_array, 'RGBA')
        data = recolored_pil.tobytes()
        recolored_sprite = pygame.image.frombuffer(data, size, 'RGBA')
        return recolored_sprite.convert_alpha()
    except Exception as e:
        # Fallback: return original sprite
        return sprite


class SnakeAnimation:
    """
    Complete snake sprite animation system with rendering, direction, and all animation logic.
    Everything is in one class - ready to copy and use!
    """
    
    def __init__(self, x, y, size=4, sprite_sheet_path='snake_sprite_sheet_palettebase.png', palette_row=0, disable_flip=False):
        # Position and size
        self.x = x
        self.y = y
        self.size = size
        self.palette_row = palette_row
        self.disable_flip = disable_flip  # OPTIMIZATION: Disable flipping for test mode
        
        # Animation tracking variables
        self.animation_frame = 0  # Current animation frame
        self.animation_timer = 0  # Timer for animation
        self.animation_state = 'idle'  # Current animation state: idle, move, attack, going_down, defeated
        self.is_moving = False
        self.is_attacking = False
        self.attack_timer = 0
        self.facing_right = False  # Track if facing right (for horizontal flip)
        self.facing_direction = 'down'  # Track facing direction: 'up', 'down', 'left', 'right'
        self.projectile_fired = False  # Track if projectile was fired during this attack
        self.is_going_down = False  # Track if going to next floor
        self.going_down_timer = 0
        self.is_defeated = False  # Track if player is defeated
        self.defeated_timer = 0
        
        # Angle for aiming/shooting
        self.angle = 0
        
        # Load sprite sheet
        self.sprite_sheet = self.load_sprite_sheet(sprite_sheet_path)
        self.animation_states = {}  # Dictionary: state_name -> list of frames
        if self.sprite_sheet:
            self.split_sprite_sheet()
    
    def load_sprite_sheet(self, sprite_sheet_path):
        """Load sprite sheet from PNG file (cached globally)"""
        global _snake_sprite_sheet_cache
        if _snake_sprite_sheet_cache is None:
            try:
                _snake_sprite_sheet_cache = pygame.image.load(sprite_sheet_path).convert_alpha()
            except Exception as e:
                print(f"Error loading sprite sheet: {e}")
                import traceback
                traceback.print_exc()
                return None
        return _snake_sprite_sheet_cache
    
    def split_sprite_sheet(self):
        """Split sprite sheet into animation states and frames (OPTIMIZED with global cache)"""
        if not self.sprite_sheet:
            return
        
        # OPTIMIZATION: Check cache first to avoid expensive processing
        global _snake_frames_cache
        cache_key = (self.palette_row, self.size)
        if cache_key in _snake_frames_cache:
            # Use cached frames (copy lists to avoid sharing references)
            cached = _snake_frames_cache[cache_key]
            self.animation_states = {
                'idle': list(cached['idle']),
                'going_down': list(cached['going_down']),
                'move': list(cached['move']),
                'attack': list(cached['attack']),
                'defeated': list(cached['defeated'])
            }
            # Still need to create flipped frames if needed
            if not self.disable_flip:
                self.flipped_frames = {}
                for state_name, frames in self.animation_states.items():
                    flipped_state_frames = []
                    for frame in frames:
                        flipped_frame = pygame.transform.flip(frame, True, False)
                        flipped_state_frames.append(flipped_frame)
                    self.flipped_frames[state_name] = flipped_state_frames
            return
        
        sheet_width, sheet_height = self.sprite_sheet.get_size()
        
        # Snake sprite sheet layout: 5 rows, 10 columns
        rows = 5
        columns = 10
        
        frame_width = sheet_width // columns
        row_height = sheet_height // rows
        
        # Scale factor to make sprites bigger
        sprite_size = self.size * 8
        
        # Extract animations
        idle_frames = []
        going_down_frames = []
        move_frames = []
        attack_frames = []
        defeated_frames = []
        
        anim_states = [
            (0, idle_frames),
            (1, going_down_frames),
            (2, move_frames),
            (3, attack_frames),
            (4, defeated_frames)
        ]
        
        # OPTIMIZATION: Process all frames in one loop
        for frame_idx in range(columns):
            for anim_row, frame_list in anim_states:
                frame_rect = pygame.Rect(frame_idx * frame_width, anim_row * row_height, frame_width, row_height)
                frame = self.sprite_sheet.subsurface(frame_rect)
                scaled_frame = pygame.transform.scale(frame, (sprite_size, sprite_size))
                # Recolor using palette row
                if self.palette_row != 0:
                    recolored_frame = recolor_snake_sprite_with_palette(scaled_frame, self.palette_row)
                    frame_list.append(recolored_frame if recolored_frame else scaled_frame)
                else:
                    frame_list.append(scaled_frame)
        
        # Store animations by state
        self.animation_states = {
            'idle': idle_frames,
            'going_down': going_down_frames,
            'move': move_frames,
            'attack': attack_frames,
            'defeated': defeated_frames
        }
        
        # OPTIMIZATION: Cache the frames for reuse (deep copy lists)
        _snake_frames_cache[cache_key] = {
            'idle': list(idle_frames),
            'going_down': list(going_down_frames),
            'move': list(move_frames),
            'attack': list(attack_frames),
            'defeated': list(defeated_frames)
        }
        
        # OPTIMIZATION: Pre-flip all frames to avoid expensive flip operations every frame (skip if flip disabled)
        self.flipped_frames = {}
        if not self.disable_flip:
            for state_name, frames in self.animation_states.items():
                flipped_state_frames = []
                for frame in frames:
                    # Create flipped version once
                    flipped_frame = pygame.transform.flip(frame, True, False)
                    flipped_state_frames.append(flipped_frame)
                self.flipped_frames[state_name] = flipped_state_frames
    
    def update_animation(self):
        """
        Update all animation logic - timers, states, and frame progression
        Call this every frame in your game loop
        """
        # Update attack timer
        # Attack animation has 10 frames, plays at 4 frames per animation frame (double speed)
        # So total duration = 10 * 4 = 40 frames
        if self.is_attacking:
            self.attack_timer += 1
            attack_frames = self.animation_states.get('attack', [])
            if attack_frames:
                # Play through all attack frames
                total_attack_duration = len(attack_frames) * 4  # 4 frames per animation frame
                if self.attack_timer >= total_attack_duration:
                    self.is_attacking = False
                    self.attack_timer = 0
                    self.animation_frame = 0  # Reset to first frame
                    self.projectile_fired = False  # Reset projectile flag
            else:
                # Fallback if attack frames not loaded
                if self.attack_timer >= 40:
                    self.is_attacking = False
                    self.attack_timer = 0
                    self.projectile_fired = False  # Reset projectile flag
        
        # Update going down timer
        if self.is_going_down:
            self.going_down_timer += 1
            going_down_frames = self.animation_states.get('going_down', [])
            if going_down_frames:
                total_duration = len(going_down_frames) * 8  # 8 frames per animation frame
                if self.going_down_timer >= total_duration:
                    self.is_going_down = False
                    self.going_down_timer = 0
                    self.animation_frame = 0
        
        # OPTIMIZATION: Set animation state based on player action (only if changed)
        # Priority: defeated > going_down > attack > move > idle
        new_state = None
        if self.is_defeated:
            new_state = 'defeated'
        elif self.is_going_down:
            new_state = 'going_down'
        elif self.is_attacking:
            new_state = 'attack'
        elif self.is_moving:
            new_state = 'move'
        else:
            new_state = 'idle'
        
        # OPTIMIZATION: Only update state if changed
        if new_state != self.animation_state:
            self.animation_state = new_state
        
        # Update animation frame
        self.animation_timer += 1
        current_frames = self.animation_states.get(self.animation_state, [])
        if current_frames:
            # OPTIMIZATION: Cache frame duration calculation
            is_attack = self.animation_state == 'attack'
            frame_duration = 4 if is_attack else 8
            if self.animation_timer >= frame_duration:
                self.animation_timer = 0
                # Loop animation continuously for all states (including defeated)
                # For going_down, loop once then stop (handled by timer)
                if self.animation_state == 'going_down':
                    # Don't loop - let timer handle completion
                    if self.animation_frame < len(current_frames) - 1:
                        self.animation_frame += 1
                else:
                    # OPTIMIZATION: Use modulo for looping (faster than if/else)
                    self.animation_frame = (self.animation_frame + 1) % len(current_frames)
                
                # Fire projectile on 6th frame of attack animation (frame index 5)
                if self.animation_state == 'attack' and not self.projectile_fired:
                    if self.animation_frame == 5:  # 6th frame (0-indexed)
                        # This will be handled in the game loop
                        pass
    
    def set_facing_from_angle(self, angle):
        """
        Set facing direction based on angle (in radians)
        Right is when angle is between -45 and 45 degrees
        """
        self.angle = angle
        angle_deg = math.degrees(angle)
        self.facing_right = (angle_deg >= -45 and angle_deg < 45)
    
    def set_facing_from_mouse(self, mouse_pos):
        """
        Set facing direction based on mouse position
        Calculates angle and sets facing_right automatically
        """
        if mouse_pos:
            dx = mouse_pos[0] - self.x
            dy = mouse_pos[1] - self.y
            # Store angle for projectile direction (no snapping, smooth aiming)
            self.angle = math.atan2(dy, dx)
            # Determine if facing right (for horizontal flip)
            # Right is when angle is between -45 and 45 degrees (approximately)
            angle_deg = math.degrees(self.angle)
            self.facing_right = (angle_deg >= -45 and angle_deg < 45)
    
    def set_facing_from_direction(self, direction):
        """
        Set facing direction from movement direction string
        direction: 'left', 'right', 'up', 'down'
        """
        self.facing_direction = direction
        if direction == 'left':
            self.facing_right = False
        elif direction == 'right':
            self.facing_right = True
        # For up/down, keep current facing_right value
    
    def start_attack(self):
        """Start attack animation"""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0
            self.animation_frame = 0  # Reset to first frame of attack animation
            self.projectile_fired = False  # Reset projectile flag
    
    def start_going_down(self):
        """Start the going down animation"""
        self.is_going_down = True
        self.going_down_timer = 0
        self.animation_frame = 0  # Reset to first frame
    
    def set_defeated(self):
        """Set defeated state and start defeated animation"""
        self.is_defeated = True
        self.defeated_timer = 0
        self.animation_frame = 0  # Reset to first frame of defeated animation
    
    def should_fire_projectile(self):
        """
        Check if projectile should be fired (on 6th frame of attack)
        Returns True if projectile should be fired this frame
        """
        return (self.animation_state == 'attack' and 
                self.animation_frame == 5 and 
                not self.projectile_fired)
    
    def draw(self, screen, grid_cell_size=32, offset_y_adjust=-25):
        """
        Draw the sprite with animation
        screen: Pygame screen surface
        grid_cell_size: Size of grid cell (default 32)
        offset_y_adjust: Vertical offset adjustment (default -25)
        """
        # OPTIMIZATION: Skip flip logic entirely if disabled (for test mode)
        if self.disable_flip:
            current_frames = self.animation_states.get(self.animation_state, [])
        else:
            # Use pre-flipped frames instead of flipping every frame
            if self.facing_right:
                current_frames = self.flipped_frames.get(self.animation_state, [])
            else:
                current_frames = self.animation_states.get(self.animation_state, [])
        
        if current_frames and self.animation_frame < len(current_frames):
            sprite = current_frames[self.animation_frame]
            # Adjust vertical offset to fix sprite sheet alignment
            offset_y = self.y - grid_cell_size + offset_y_adjust
            sprite_rect = sprite.get_rect(center=(int(self.x), int(offset_y)))
            screen.blit(sprite, sprite_rect)
            return True
        return False
    
    def draw_with_fallback(self, screen, grid_cell_size=32, offset_y_adjust=-25, color=(255, 255, 255)):
        """
        Draw the sprite with animation or fallback to triangle if sprite didn't load
        screen: Pygame screen surface
        grid_cell_size: Size of grid cell (default 32)
        offset_y_adjust: Vertical offset adjustment (default -25)
        color: Color for fallback triangle
        """
        current_frames = self.animation_states.get(self.animation_state, [])
        if current_frames and self.animation_frame < len(current_frames):
            sprite = current_frames[self.animation_frame]
            # Flip sprite horizontally when facing right
            if self.facing_right:
                sprite = pygame.transform.flip(sprite, True, False)
            # Adjust vertical offset to fix sprite sheet alignment
            offset_y = self.y - grid_cell_size + offset_y_adjust
            sprite_rect = sprite.get_rect(center=(int(self.x), int(offset_y)))
            screen.blit(sprite, sprite_rect)
        else:
            # Fallback to triangle if sprite didn't load
            points = []
            for i in range(3):
                angle_offset = (i * 2 * math.pi / 3) + self.angle
                px = self.x + math.cos(angle_offset) * self.size
                py = self.y + math.sin(angle_offset) * self.size
                points.append((px, py))
            pygame.draw.polygon(screen, color, points)


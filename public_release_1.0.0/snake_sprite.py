import pygame
import numpy as np
from PIL import Image

def get_snake_palette_row_colors(row_index):
    """Get colors from a specific row in the snake palette (0-indexed, row 1 = index 0)"""
    try:
        palette_img = Image.open('snake_sprite_sheet_palette.png')
        palette_img = palette_img.convert('RGB')
        
        swatch_size = 50
        row_y = row_index * swatch_size
        
        # Extract 9 colors from the row (columns 0-8, including column 8 for black pixels)
        colors = []
        for i in range(9):
            x = i * swatch_size
            color = palette_img.getpixel((x, row_y))
            colors.append(color)
        
        return colors
    except Exception as e:
        return None

def recolor_snake_sprite_with_palette(sprite, palette_row_index):
    """Recolor snake sprite using colors from a palette row (same process as lizard)"""
    if sprite is None:
        return None
    
    # Get palette colors for this row
    palette_colors = get_snake_palette_row_colors(palette_row_index)
    if palette_colors is None:
        return sprite
    
    # Load the base image directly from snake_sprite_sheet_palettebase.png to get original colors
    try:
        # Load the base palette image to get original colors
        base_pil = Image.open('snake_sprite_sheet_palettebase.png')
        if base_pil.mode != 'RGBA':
            base_pil = base_pil.convert('RGBA')
        
        base_array = np.array(base_pil)
        
        # Get original colors from palette base row 0 (the target row used when creating palette base)
        # The palette base was created by mapping original colors to row 0 by column position
        # So we need to get row 0 colors from the palette to know which original colors map to which columns
        palette_img = Image.open('snake_sprite_sheet_palette.png')
        palette_img = palette_img.convert('RGB')
        swatch_size = 50
        row0_colors = []
        max_cols = palette_img.size[0] // swatch_size
        for i in range(max_cols):
            x = i * swatch_size
            row0_colors.append(palette_img.getpixel((x, 0)))  # Row 0
        
        # Get unique colors from the base image (non-transparent)
        original_colors = set()
        for y in range(base_array.shape[0]):
            for x in range(base_array.shape[1]):
                r, g, b, a = int(base_array[y, x, 0]), int(base_array[y, x, 1]), int(base_array[y, x, 2]), int(base_array[y, x, 3])
                if a > 0:
                    original_colors.add((r, g, b))
        
        # Create mapping: original color -> palette color (by matching to row 0 colors, then mapping to target row)
        # Find which column each original color matches in row 0
        def color_distance(c1, c2):
            return sum((a - b) ** 2 for a, b in zip(c1, c2))
        
        color_mapping = {}
        for original_color in original_colors:
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
        
        # Apply the color mapping
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

class SnakeSpriteData:
    """Data class for snake sprite state"""
    def __init__(self, x=0, y=0, max_health=100):
        self.x = x
        self.y = y
        self.max_health = max_health
        self.is_attacking = False
        self.is_moving = False
        self.facing_direction = 'right'  # 'right' or 'left'

class SnakeSpriteRenderer:
    """Renderer for snake sprite sheet with animation support"""
    def __init__(self, sprite_size=4):
        self.sprite_size = sprite_size  # Scale multiplier
        self.sprite_sheet = None
        self.frames = {}
        self.current_animation_state = 'idle'
        self.facing_right = True
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 200  # milliseconds per frame
        
        # Load the sprite sheet
        self._load_sprite_sheet()
    
    def _load_sprite_sheet(self):
        """Load and parse the snake sprite sheet from palette base"""
        try:
            # Load from palette base (same as lizard system)
            self.sprite_sheet = pygame.image.load('snake_sprite_sheet_palettebase.png').convert_alpha()
            sheet_width, sheet_height = self.sprite_sheet.get_size()
            
            # The spritesheet is organized with animations in ROWS (not columns)
            # Each row is a frame, full width
            # Try to detect number of rows - assume 8 frames (most common for animation)
            if sheet_height % 8 == 0:
                frame_height = sheet_height // 8
                frame_count = 8
            elif sheet_height % 4 == 0:
                frame_height = sheet_height // 4
                frame_count = 4
            else:
                # Default: assume 2 frames
                frame_height = sheet_height // 2
                frame_count = 2
            
            frame_width = sheet_width  # Full width per frame
            
            # Extract all frames (from rows, not columns)
            raw_frames = []
            for i in range(frame_count):
                frame_rect = pygame.Rect(0, i * frame_height, frame_width, frame_height)
                frame = self.sprite_sheet.subsurface(frame_rect)
                # Scale frame
                scaled_width = int(frame_width * self.sprite_size)
                scaled_height = int(frame_height * self.sprite_size)
                scaled_frame = pygame.transform.scale(frame, (scaled_width, scaled_height))
                raw_frames.append(scaled_frame)
            
            # Recolor frames using palette row 0 (same as lizard system)
            # Row 0 = lizard row 1 colors (the random colors row)
            recolored_frames = []
            for frame in raw_frames:
                recolored_frame = recolor_snake_sprite_with_palette(frame, 0)  # Use row 0
                if recolored_frame is not None:
                    recolored_frames.append(recolored_frame)
                else:
                    recolored_frames.append(frame)  # Fallback to original if recoloring fails
            
            # Organize frames by animation state
            # If we have 8 frames, assume: 0-1=idle, 2-3=move, 4-5=attack, 6-7=extra
            # If we have 4 frames, assume: 0=idle, 1=move, 2=attack, 3=extra
            if len(recolored_frames) >= 8:
                self.frames['idle'] = recolored_frames[0:2]  # 2 frames for idle
                self.frames['move'] = recolored_frames[2:4]  # 2 frames for move
                self.frames['attack'] = recolored_frames[4:6] if len(recolored_frames) > 4 else recolored_frames[0:2]  # 2 frames for attack
            elif len(recolored_frames) >= 4:
                self.frames['idle'] = [recolored_frames[0]]
                self.frames['move'] = [recolored_frames[1]]
                self.frames['attack'] = [recolored_frames[2]] if len(recolored_frames) > 2 else [recolored_frames[0]]
            else:
                # 2 or fewer frames: use first for idle, second for move/attack
                self.frames['idle'] = [recolored_frames[0]]
                self.frames['move'] = [recolored_frames[1]] if len(recolored_frames) > 1 else [recolored_frames[0]]
                self.frames['attack'] = [recolored_frames[1]] if len(recolored_frames) > 1 else [recolored_frames[0]]
            
        except Exception as e:
            print(f"Error loading snake sprite sheet: {e}")
            self.sprite_sheet = None
            self.frames = {
                'idle': [],
                'move': [],
                'attack': []
            }
    
    def update_animation(self, loop=True):
        """Update animation frame"""
        if self.sprite_sheet is None:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Check if it's time to advance to next frame
        if current_time - self.animation_timer >= self.animation_speed:
            animation_frames = self.frames.get(self.current_animation_state, [])
            if len(animation_frames) > 0:
                if loop:
                    self.animation_frame = (self.animation_frame + 1) % len(animation_frames)
                else:
                    self.animation_frame = min(self.animation_frame + 1, len(animation_frames) - 1)
            self.animation_timer = current_time
    
    def set_animation_state(self, state):
        """Set the current animation state ('idle', 'move', or 'attack')"""
        if state != self.current_animation_state:
            self.current_animation_state = state
            self.animation_frame = 0  # Reset to first frame of new animation
            self.animation_timer = pygame.time.get_ticks()
    
    def set_facing_direction(self, facing_right):
        """Set facing direction (True for right, False for left)"""
        self.facing_right = facing_right
    
    def draw(self, screen, x, y, offset_y=0):
        """Draw the sprite at the given position"""
        if self.sprite_sheet is None:
            return
        
        animation_frames = self.frames.get(self.current_animation_state, [])
        if len(animation_frames) == 0:
            return
        
        # Get current frame
        frame = animation_frames[self.animation_frame]
        
        # Flip horizontally if facing left
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        
        # Draw the sprite
        sprite_rect = frame.get_rect(center=(int(x), int(y + offset_y)))
        screen.blit(frame, sprite_rect)




from PIL import Image

def get_snake_palette_row_colors(row_index):
    """Get colors from a specific row in the snake palette (0-indexed, row 1 = index 0)"""
    try:
        palette_img = Image.open('snake_sprite_sheet_palette.png')
        palette_img = palette_img.convert('RGB')
        
        swatch_size = 50
        row_y = row_index * swatch_size
        
        # Extract 9 colors from the row (columns 0-8, including column 8 for black pixels)
        colors = []
        for i in range(9):
            x = i * swatch_size
            color = palette_img.getpixel((x, row_y))
            colors.append(color)
        
        return colors
    except Exception as e:
        return None

def recolor_snake_sprite_with_palette(sprite, palette_row_index):
    """Recolor snake sprite using colors from a palette row (same process as lizard)"""
    if sprite is None:
        return None
    
    # Get palette colors for this row
    palette_colors = get_snake_palette_row_colors(palette_row_index)
    if palette_colors is None:
        return sprite
    
    # Load the base image directly from snake_sprite_sheet_palettebase.png to get original colors
    try:
        # Load the base palette image to get original colors
        base_pil = Image.open('snake_sprite_sheet_palettebase.png')
        if base_pil.mode != 'RGBA':
            base_pil = base_pil.convert('RGBA')
        
        base_array = np.array(base_pil)
        
        # Get original colors from palette base row 0 (the target row used when creating palette base)
        # The palette base was created by mapping original colors to row 0 by column position
        # So we need to get row 0 colors from the palette to know which original colors map to which columns
        palette_img = Image.open('snake_sprite_sheet_palette.png')
        palette_img = palette_img.convert('RGB')
        swatch_size = 50
        row0_colors = []
        max_cols = palette_img.size[0] // swatch_size
        for i in range(max_cols):
            x = i * swatch_size
            row0_colors.append(palette_img.getpixel((x, 0)))  # Row 0
        
        # Get unique colors from the base image (non-transparent)
        original_colors = set()
        for y in range(base_array.shape[0]):
            for x in range(base_array.shape[1]):
                r, g, b, a = int(base_array[y, x, 0]), int(base_array[y, x, 1]), int(base_array[y, x, 2]), int(base_array[y, x, 3])
                if a > 0:
                    original_colors.add((r, g, b))
        
        # Create mapping: original color -> palette color (by matching to row 0 colors, then mapping to target row)
        # Find which column each original color matches in row 0
        def color_distance(c1, c2):
            return sum((a - b) ** 2 for a, b in zip(c1, c2))
        
        color_mapping = {}
        for original_color in original_colors:
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
        
        # Apply the color mapping
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

class SnakeSpriteData:
    """Data class for snake sprite state"""
    def __init__(self, x=0, y=0, max_health=100):
        self.x = x
        self.y = y
        self.max_health = max_health
        self.is_attacking = False
        self.is_moving = False
        self.facing_direction = 'right'  # 'right' or 'left'

class SnakeSpriteRenderer:
    """Renderer for snake sprite sheet with animation support"""
    def __init__(self, sprite_size=4):
        self.sprite_size = sprite_size  # Scale multiplier
        self.sprite_sheet = None
        self.frames = {}
        self.current_animation_state = 'idle'
        self.facing_right = True
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 200  # milliseconds per frame
        
        # Load the sprite sheet
        self._load_sprite_sheet()
    
    def _load_sprite_sheet(self):
        """Load and parse the snake sprite sheet from palette base"""
        try:
            # Load from palette base (same as lizard system)
            self.sprite_sheet = pygame.image.load('snake_sprite_sheet_palettebase.png').convert_alpha()
            sheet_width, sheet_height = self.sprite_sheet.get_size()
            
            # The spritesheet is organized with animations in ROWS (not columns)
            # Each row is a frame, full width
            # Try to detect number of rows - assume 8 frames (most common for animation)
            if sheet_height % 8 == 0:
                frame_height = sheet_height // 8
                frame_count = 8
            elif sheet_height % 4 == 0:
                frame_height = sheet_height // 4
                frame_count = 4
            else:
                # Default: assume 2 frames
                frame_height = sheet_height // 2
                frame_count = 2
            
            frame_width = sheet_width  # Full width per frame
            
            # Extract all frames (from rows, not columns)
            raw_frames = []
            for i in range(frame_count):
                frame_rect = pygame.Rect(0, i * frame_height, frame_width, frame_height)
                frame = self.sprite_sheet.subsurface(frame_rect)
                # Scale frame
                scaled_width = int(frame_width * self.sprite_size)
                scaled_height = int(frame_height * self.sprite_size)
                scaled_frame = pygame.transform.scale(frame, (scaled_width, scaled_height))
                raw_frames.append(scaled_frame)
            
            # Recolor frames using palette row 0 (same as lizard system)
            # Row 0 = lizard row 1 colors (the random colors row)
            recolored_frames = []
            for frame in raw_frames:
                recolored_frame = recolor_snake_sprite_with_palette(frame, 0)  # Use row 0
                if recolored_frame is not None:
                    recolored_frames.append(recolored_frame)
                else:
                    recolored_frames.append(frame)  # Fallback to original if recoloring fails
            
            # Organize frames by animation state
            # If we have 8 frames, assume: 0-1=idle, 2-3=move, 4-5=attack, 6-7=extra
            # If we have 4 frames, assume: 0=idle, 1=move, 2=attack, 3=extra
            if len(recolored_frames) >= 8:
                self.frames['idle'] = recolored_frames[0:2]  # 2 frames for idle
                self.frames['move'] = recolored_frames[2:4]  # 2 frames for move
                self.frames['attack'] = recolored_frames[4:6] if len(recolored_frames) > 4 else recolored_frames[0:2]  # 2 frames for attack
            elif len(recolored_frames) >= 4:
                self.frames['idle'] = [recolored_frames[0]]
                self.frames['move'] = [recolored_frames[1]]
                self.frames['attack'] = [recolored_frames[2]] if len(recolored_frames) > 2 else [recolored_frames[0]]
            else:
                # 2 or fewer frames: use first for idle, second for move/attack
                self.frames['idle'] = [recolored_frames[0]]
                self.frames['move'] = [recolored_frames[1]] if len(recolored_frames) > 1 else [recolored_frames[0]]
                self.frames['attack'] = [recolored_frames[1]] if len(recolored_frames) > 1 else [recolored_frames[0]]
            
        except Exception as e:
            print(f"Error loading snake sprite sheet: {e}")
            self.sprite_sheet = None
            self.frames = {
                'idle': [],
                'move': [],
                'attack': []
            }
    
    def update_animation(self, loop=True):
        """Update animation frame"""
        if self.sprite_sheet is None:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Check if it's time to advance to next frame
        if current_time - self.animation_timer >= self.animation_speed:
            animation_frames = self.frames.get(self.current_animation_state, [])
            if len(animation_frames) > 0:
                if loop:
                    self.animation_frame = (self.animation_frame + 1) % len(animation_frames)
                else:
                    self.animation_frame = min(self.animation_frame + 1, len(animation_frames) - 1)
            self.animation_timer = current_time
    
    def set_animation_state(self, state):
        """Set the current animation state ('idle', 'move', or 'attack')"""
        if state != self.current_animation_state:
            self.current_animation_state = state
            self.animation_frame = 0  # Reset to first frame of new animation
            self.animation_timer = pygame.time.get_ticks()
    
    def set_facing_direction(self, facing_right):
        """Set facing direction (True for right, False for left)"""
        self.facing_right = facing_right
    
    def draw(self, screen, x, y, offset_y=0):
        """Draw the sprite at the given position"""
        if self.sprite_sheet is None:
            return
        
        animation_frames = self.frames.get(self.current_animation_state, [])
        if len(animation_frames) == 0:
            return
        
        # Get current frame
        frame = animation_frames[self.animation_frame]
        
        # Flip horizontally if facing left
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        
        # Draw the sprite
        sprite_rect = frame.get_rect(center=(int(x), int(y + offset_y)))
        screen.blit(frame, sprite_rect)



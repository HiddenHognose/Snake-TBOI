import pygame
import math
import random

# Load lizard sprite base (from palette base)
_lizard_sprite_base = None

# Caching for color loading optimization
_lizard_palette_cache = {}  # Cache palette row colors
_lizard_palette_image = None  # Cache the palette image itself
_lizard_row0_colors = None  # Cache row 0 colors
_lizard_base_array = None  # Cache base image array
_lizard_color_mappings = {}  # Cache color mappings per palette row

# OPTIMIZATION: Cache unscaled base images and 8x scaled recolored sprites
_lizard_unscaled_pil = None  # Cache unscaled PIL image
_lizard_unscaled_pygame = None  # Cache unscaled pygame surface
_lizard_8x_recolored_cache = {}  # Cache: (palette_row) -> 8x scaled recolored sprite (before final scaling)

def get_lizard_sprite_base():
    """Load and return the base lizard sprite from lizard1_palletbase.png"""
    global _lizard_sprite_base
    if _lizard_sprite_base is None:
        try:
            from PIL import Image
            # Load the palette base image
            pil_image = Image.open('lizard1_palletbase.png')
            
            # Convert to RGBA if needed
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')
            
            # Enlarge the sprite (8x size for MANY BIGGER lizards)
            new_size = (int(pil_image.size[0] * 8), int(pil_image.size[1] * 8))
            # Use LANCZOS resampling
            try:
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            except AttributeError:
                # Older PIL version - use numeric constant
                pil_image = pil_image.resize(new_size, Image.LANCZOS)
            
            # Convert PIL image to pygame surface
            mode = pil_image.mode
            size = pil_image.size
            data = pil_image.tobytes()
            
            try:
                _lizard_sprite_base = pygame.image.frombuffer(data, size, mode)
            except:
                _lizard_sprite_base = pygame.image.fromstring(data, size, mode)
            _lizard_sprite_base = _lizard_sprite_base.convert_alpha()
        except Exception as e:
            _lizard_sprite_base = None
    return _lizard_sprite_base

def _load_lizard_palette_data():
    """Load and cache palette data (row 0 colors, base array) - called once"""
    global _lizard_row0_colors, _lizard_base_array, _lizard_palette_image
    if _lizard_row0_colors is None or _lizard_base_array is None:
        try:
            from PIL import Image
            import numpy as np
            
            # OPTIMIZATION: Use cached palette image if available
            if _lizard_palette_image is None:
                _lizard_palette_image = Image.open('lizard1_pallete.png')
                _lizard_palette_image = _lizard_palette_image.convert('RGB')
            
            # Get row 0 colors from cached image
            swatch_size = 50
            _lizard_row0_colors = []
            max_cols = _lizard_palette_image.size[0] // swatch_size
            for i in range(max_cols):
                x = i * swatch_size
                _lizard_row0_colors.append(_lizard_palette_image.getpixel((x, 0)))  # Row 0
            
            # Load base image array
            base_pil = Image.open('lizard1_palletbase.png')
            if base_pil.mode != 'RGBA':
                base_pil = base_pil.convert('RGBA')
            _lizard_base_array = np.array(base_pil)
        except Exception as e:
            _lizard_row0_colors = []
            _lizard_base_array = None

def get_palette_row_colors(row_index):
    """Get colors from a specific row in the palette (0-indexed, row 1 = index 0) - CACHED"""
    # Check cache first
    if row_index in _lizard_palette_cache:
        return _lizard_palette_cache[row_index]
    
    try:
        from PIL import Image
        global _lizard_palette_image
        # OPTIMIZATION: Load palette image once and cache it
        if _lizard_palette_image is None:
            _lizard_palette_image = Image.open('lizard1_pallete.png')
            _lizard_palette_image = _lizard_palette_image.convert('RGB')
        
        swatch_size = 50
        row_y = row_index * swatch_size
        
        # Extract 26 colors from the row
        colors = []
        for i in range(26):
            x = i * swatch_size
            color = _lizard_palette_image.getpixel((x, row_y))
            colors.append(color)
        
        # Cache the result
        _lizard_palette_cache[row_index] = colors
        return colors
    except Exception as e:
        return None

def recolor_sprite_with_palette(sprite, palette_row_index):
    """Recolor sprite using colors from a palette row - OPTIMIZED WITH CACHING"""
    if sprite is None:
        return None
    
    # Get palette colors for this row (cached)
    palette_colors = get_palette_row_colors(palette_row_index)
    if palette_colors is None:
        return sprite
    
    # Load palette data once (cached)
    _load_lizard_palette_data()
    if _lizard_row0_colors is None or _lizard_base_array is None:
        return sprite
    
    try:
        from PIL import Image
        import numpy as np
        
        # Check if color mapping is cached for this palette row
        if palette_row_index not in _lizard_color_mappings:
            # Build color mapping (only once per palette row)
            def color_distance(c1, c2):
                return sum((a - b) ** 2 for a, b in zip(c1, c2))
        
            # Get unique colors from the base image (non-transparent) - only once
            # OPTIMIZATION: Use numpy for faster color extraction
            mask = _lizard_base_array[:, :, 3] > 0  # Non-transparent pixels
            rgb_array = _lizard_base_array[mask, :3]  # Get RGB values
            # Convert to tuples and get unique colors
            original_colors = set(tuple(int(c) for c in rgb) for rgb in rgb_array)
            
            # Create mapping: original color -> palette color
            color_mapping = {}
            for original_color in original_colors:
                # Find the closest matching color in row 0 (by column)
                best_match_idx = 0
                best_distance = float('inf')
                for i, row0_color in enumerate(_lizard_row0_colors):
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
            
            # Cache the mapping
            _lizard_color_mappings[palette_row_index] = color_mapping
        else:
            # Use cached mapping
            color_mapping = _lizard_color_mappings[palette_row_index]
        
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
        # Use approximate color matching to handle conversion differences
        for original_color, new_color in color_mapping.items():
            # Allow small differences due to color space conversion (within 2 RGB units)
            tolerance = 2
            mask = (np.abs(img_array[:, :, 0].astype(int) - original_color[0]) <= tolerance) & \
                   (np.abs(img_array[:, :, 1].astype(int) - original_color[1]) <= tolerance) & \
                   (np.abs(img_array[:, :, 2].astype(int) - original_color[2]) <= tolerance) & \
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

# Palette row assignments for each enemy type
# Row indices are 0-based (row 1 = index 0, row 2 = index 1, etc.)
PALETTE_ROW_MAPPING = {
    'basic': 5,    # Row 6 (index 5)
    'fast': 1,     # Row 2 (index 1)
    'tank': 6,     # Row 7 (index 6)
    'ranged': 7,   # Row 8 (index 7)
    'zigzag': 4,   # Row 5 (index 4)
    'boss': 2      # Row 3 (index 2)
}

class Enemy:
    """Base enemy class"""
    def __init__(self, x, y, enemy_type='basic'):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.radius = 12
        self.speed = 2
        self.max_health = 2
        self.health = self.max_health
        # Color tint for this enemy type - NEON COLORS ONLY
        self.tint_color = (0, 255, 0)  # Neon Green
        self.sprite = None
        self._load_sprite()
    
    def _load_sprite(self):
        """Load and recolor the sprite using palette row - OPTIMIZED with caching, preserves color-before-scale"""
        global _lizard_unscaled_pil, _lizard_unscaled_pygame, _lizard_8x_recolored_cache
        
        try:
            from PIL import Image
            import numpy as np
            
            # OPTIMIZATION: Load unscaled base image once and cache it
            if _lizard_unscaled_pil is None:
                _lizard_unscaled_pil = Image.open('lizard1_palletbase.png')
                if _lizard_unscaled_pil.mode != 'RGBA':
                    _lizard_unscaled_pil = _lizard_unscaled_pil.convert('RGBA')
            
            # OPTIMIZATION: Convert to pygame surface once and cache it
            if _lizard_unscaled_pygame is None:
                mode = _lizard_unscaled_pil.mode
                size = _lizard_unscaled_pil.size
                data = _lizard_unscaled_pil.tobytes()
                try:
                    _lizard_unscaled_pygame = pygame.image.frombuffer(data, size, mode)
                except:
                    _lizard_unscaled_pygame = pygame.image.fromstring(data, size, mode)
                _lizard_unscaled_pygame = _lizard_unscaled_pygame.convert_alpha()
            
            if _lizard_unscaled_pygame:
                # Get palette row for this enemy type, default to row 0 if not assigned
                palette_row = PALETTE_ROW_MAPPING.get(self.enemy_type, 0)  # Default to row 0
                
                # OPTIMIZATION: Check cache for 8x scaled recolored sprite (color-before-scale preserved)
                if palette_row not in _lizard_8x_recolored_cache:
                    # Recolor the unscaled sprite first (CRITICAL: color before scale)
                    recolored_sprite = recolor_sprite_with_palette(_lizard_unscaled_pygame.copy(), palette_row)
                    
                    if recolored_sprite:
                        # Now scale up to 8x (like get_lizard_sprite_base does)
                        base_size = (int(recolored_sprite.get_width() * 8), int(recolored_sprite.get_height() * 8))
                        try:
                            # Convert pygame surface to numpy array, then to PIL for high-quality scaling
                            pixel_array = pygame.surfarray.array3d(recolored_sprite)
                            alpha_array = pygame.surfarray.array_alpha(recolored_sprite)
                            # Convert to (height, width, channels) format
                            img_array = np.zeros((recolored_sprite.get_height(), recolored_sprite.get_width(), 4), dtype=np.uint8)
                            img_array[:, :, 0] = np.swapaxes(pixel_array[:, :, 0], 0, 1)
                            img_array[:, :, 1] = np.swapaxes(pixel_array[:, :, 1], 0, 1)
                            img_array[:, :, 2] = np.swapaxes(pixel_array[:, :, 2], 0, 1)
                            img_array[:, :, 3] = np.swapaxes(alpha_array, 0, 1)
                            
                            pil_sprite = Image.fromarray(img_array, 'RGBA')
                            try:
                                pil_sprite = pil_sprite.resize(base_size, Image.Resampling.LANCZOS)
                            except AttributeError:
                                pil_sprite = pil_sprite.resize(base_size, Image.LANCZOS)
                            # Convert back to pygame
                            data = pil_sprite.tobytes()
                            try:
                                scaled_sprite = pygame.image.frombuffer(data, base_size, 'RGBA')
                            except:
                                scaled_sprite = pygame.image.fromstring(data, base_size, 'RGBA')
                            scaled_sprite = scaled_sprite.convert_alpha()
                        except:
                            # Fallback to pygame scaling if conversion fails
                            scaled_sprite = pygame.transform.scale(recolored_sprite, base_size)
                        
                        # Cache the 8x scaled recolored sprite
                        _lizard_8x_recolored_cache[palette_row] = scaled_sprite
                    else:
                        # If recoloring failed, use fallback
                        scaled_sprite = None
                else:
                    # Use cached 8x scaled recolored sprite
                    scaled_sprite = _lizard_8x_recolored_cache[palette_row]
                
                if scaled_sprite:
                    # Now scale to match enemy size (final scaling step)
                    target_size = self.radius * 2
                    current_size = max(scaled_sprite.get_width(), scaled_sprite.get_height())
                    if current_size > 0 and target_size > 0:
                        scale_factor = target_size / current_size
                        new_width = max(1, int(scaled_sprite.get_width() * scale_factor))
                        new_height = max(1, int(scaled_sprite.get_height() * scale_factor))
                        self.sprite = pygame.transform.scale(scaled_sprite, (new_width, new_height))
                    else:
                        self.sprite = scaled_sprite
        except Exception as e:
            # Fallback to old method if new method fails
            base_sprite = get_lizard_sprite_base()
            if base_sprite:
                palette_row = PALETTE_ROW_MAPPING.get(self.enemy_type, 0)
                self.sprite = recolor_sprite_with_palette(base_sprite, palette_row)
                if self.sprite:
                    target_size = self.radius * 2
                    current_size = max(self.sprite.get_width(), self.sprite.get_height())
                    if current_size != target_size:
                        scale_factor = target_size / current_size
                        new_width = int(self.sprite.get_width() * scale_factor)
                        new_height = int(self.sprite.get_height() * scale_factor)
                        self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
        
    def update(self, player_x, player_y):
        """Move towards the player"""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            dx /= dist
            dy /= dist
            self.x += dx * self.speed
            self.y += dy * self.speed
    
    def take_damage(self, amount):
        """Take damage"""
        self.health -= amount
    
    def collides_with(self, other):
        """Check collision with another object - OPTIMIZED with squared distance"""
        dx = self.x - other.x
        dy = self.y - other.y
        dist_sq = dx*dx + dy*dy
        radius_sum = self.radius + other.radius
        return dist_sq < (radius_sum * radius_sum)
    
    def draw(self, screen):
        """Draw the lizard enemy using sprite"""
        if self.sprite:
            # Draw sprite centered on enemy position
            sprite_rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.sprite, sprite_rect)
        else:
            # Fallback to simple circle if sprite not loaded
            pygame.draw.circle(screen, self.tint_color, (int(self.x), int(self.y)), self.radius)


class FastEnemy(Enemy):
    """Fast-moving enemy that's hard to hit"""
    def __init__(self, x, y):
        super().__init__(x, y, 'fast')
        self.speed = 3.5  # Much faster
        self.max_health = 1  # Less health
        self.health = self.max_health
        self.tint_color = (255, 0, 255)  # Neon Magenta/Pink
        self._load_sprite()
        self.dodge_timer = 0
        self.dodge_cooldown = 120  # Dodge every 2 seconds
    
    def update(self, player_x, player_y):
        """Fast enemy with dodge behavior"""
        self.dodge_timer += 1
        
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            dx /= dist
            dy /= dist
            
            # Occasionally dodge sideways
            if self.dodge_timer > self.dodge_cooldown:
                # Dodge perpendicular to player direction
                perp_x = -dy
                perp_y = dx
                self.x += perp_x * self.speed * 0.5
                self.y += perp_y * self.speed * 0.5
                self.dodge_timer = 0
            else:
                # Move towards player
                self.x += dx * self.speed
                self.y += dy * self.speed
    
    def draw(self, screen):
        """Draw fast enemy using sprite"""
        if self.sprite:
            sprite_rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.sprite, sprite_rect)
        else:
            pygame.draw.circle(screen, self.tint_color, (int(self.x), int(self.y)), self.radius)


class TankEnemy(Enemy):
    """Slow but tough enemy"""
    def __init__(self, x, y):
        super().__init__(x, y, 'tank')
        self.speed = 1.0  # Very slow
        self.max_health = 5  # More health
        self.health = self.max_health
        self.radius = 18  # Bigger
        self.tint_color = (0, 255, 255)  # Neon Cyan
        self._load_sprite()
    
    def draw(self, screen):
        """Draw tank enemy using sprite"""
        if self.sprite:
            sprite_rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.sprite, sprite_rect)
        else:
            pygame.draw.circle(screen, self.tint_color, (int(self.x), int(self.y)), self.radius)


class RangedEnemy(Enemy):
    """Enemy that shoots at the player"""
    def __init__(self, x, y):
        super().__init__(x, y, 'ranged')
        self.speed = 1.2  # Slower movement
        self.max_health = 2
        self.health = self.max_health
        self.tint_color = (255, 0, 128)  # Neon Pink
        self._load_sprite()
        self.shoot_cooldown = 0
        self.shoot_delay = 90  # Shoot every 1.5 seconds
        self.keep_distance = 200  # Try to stay this far from player
    
    def update(self, player_x, player_y, bullets):
        """Ranged enemy that keeps distance and shoots"""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            dx /= dist
            dy /= dist
            
            # Keep distance from player
            if dist < self.keep_distance:
                # Move away from player
                self.x -= dx * self.speed
                self.y -= dy * self.speed
            elif dist > self.keep_distance + 50:
                # Move towards player
                self.x += dx * self.speed * 0.5
                self.y += dy * self.speed * 0.5
        
        # Shooting logic
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        elif dist > 0 and dist < 400:  # Only shoot if player is in range
            # Shoot at player
            from bullet import Bullet
            bullet = Bullet(self.x, self.y, dx, dy, is_player=False)
            bullets.append(bullet)
            self.shoot_cooldown = self.shoot_delay
    
    def draw(self, screen):
        """Draw ranged enemy using sprite"""
        if self.sprite:
            sprite_rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.sprite, sprite_rect)
            
            # Draw weapon/aim indicator when ready to shoot
            if self.shoot_cooldown == 0:
                # Draw small crosshair
                pygame.draw.circle(screen, (255, 200, 0), 
                                  (int(self.x), int(self.y)), self.radius + 3, 1)
        else:
            pygame.draw.circle(screen, self.tint_color, (int(self.x), int(self.y)), self.radius)


class ZigzagEnemy(Enemy):
    """Enemy that moves in a zigzag pattern"""
    def __init__(self, x, y):
        super().__init__(x, y, 'zigzag')
        self.speed = 2.5
        self.max_health = 2
        self.health = self.max_health
        self.tint_color = (255, 255, 0)  # Neon Yellow
        self._load_sprite()
        self.zigzag_timer = 0
        self.zigzag_direction = 1
    
    def update(self, player_x, player_y):
        """Move in zigzag pattern towards player"""
        self.zigzag_timer += 1
        
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            dx /= dist
            dy /= dist
            
            # Change zigzag direction every 30 frames
            if self.zigzag_timer > 30:
                self.zigzag_direction *= -1
                self.zigzag_timer = 0
            
            # Move towards player but with perpendicular component
            perp_x = -dy * self.zigzag_direction
            perp_y = dx * self.zigzag_direction
            
            self.x += (dx * 0.7 + perp_x * 0.3) * self.speed
            self.y += (dy * 0.7 + perp_y * 0.3) * self.speed
    
    def draw(self, screen):
        """Draw zigzag enemy using sprite"""
        if self.sprite:
            sprite_rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.sprite, sprite_rect)
        else:
            pygame.draw.circle(screen, self.tint_color, (int(self.x), int(self.y)), self.radius)

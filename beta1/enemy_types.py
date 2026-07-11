import pygame
import math
import random

# Load lizard sprite
_lizard_sprite = None

def get_lizard_sprite():
    """Load and return the lizard sprite (supports AVIF via PIL with pillow-avif-plugin)"""
    global _lizard_sprite
    if _lizard_sprite is None:
        try:
            # Try loading AVIF with PIL first, then convert to pygame surface
            try:
                from PIL import Image
                import io
                # Import pillow-avif-plugin to register AVIF support
                try:
                    import pillow_avif
                except ImportError:
                    pass  # Plugin not available, will try anyway
                # Try to load lizard1 (try different extensions)
                pil_image = None
                for filename in ['lizard1.webp', 'lizard1.avif', 'lizard1.png', 'lizard1.jpg', 'Lizard1.webp', 'Lizard1.avif', 'Lizard1.png']:
                    try:
                        pil_image = Image.open(filename)
                        break
                    except:
                        continue
                
                if pil_image is None:
                    raise FileNotFoundError("Could not find lizard1 image file")
                
                # Convert to RGBA if needed
                if pil_image.mode != 'RGBA':
                    pil_image = pil_image.convert('RGBA')
                
                # Remove orange background FIRST (before grayscaling)
                # Use color distance to detect orange pixels more accurately
                pixels = pil_image.load()
                width, height = pil_image.size
                
                # Define orange color (typical orange background)
                orange_r, orange_g, orange_b = 255, 165, 0
                # Threshold for color matching (how close to orange)
                color_threshold = 80
                
                for y in range(height):
                    for x in range(width):
                        r, g, b, a = pixels[x, y]
                        # Calculate color distance from orange
                        color_distance = ((r - orange_r)**2 + (g - orange_g)**2 + (b - orange_b)**2)**0.5
                        
                        # Also check for bright orange/yellow-orange variations
                        is_orange = (
                            color_distance < color_threshold or
                            # Bright orange: high red, medium-high green, low blue
                            (r > 220 and g > 140 and g < 220 and b < 80) or
                            # Yellow-orange: very high red and green, low blue
                            (r > 240 and g > 200 and b < 60) or
                            # Darker orange: still high red, lower green
                            (r > 200 and g > 100 and g < 180 and b < 50)
                        )
                        
                        if is_orange:
                            # Make orange pixels transparent
                            pixels[x, y] = (r, g, b, 0)
                
                # NOW convert to grayscale (after background removal)
                # Split channels to preserve alpha
                r, g, b, a = pil_image.split()
                # Convert RGB to grayscale
                grayscale = pil_image.convert('L')
                # Merge grayscale RGB with alpha channel (transparent background preserved)
                pil_image = Image.merge('RGBA', (grayscale, grayscale, grayscale, a))
                
                # Enlarge the sprite (8x size for MANY BIGGER lizards)
                new_size = (int(pil_image.size[0] * 8), int(pil_image.size[1] * 8))
                # Use LANCZOS resampling (try new API first, fallback to old)
                try:
                    pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                except AttributeError:
                    # Older PIL version - use numeric constant
                    pil_image = pil_image.resize(new_size, Image.LANCZOS)
                
                # Convert PIL image to pygame surface using frombytes (newer pygame)
                # Get image data as bytes
                mode = pil_image.mode
                size = pil_image.size
                data = pil_image.tobytes()
                
                # Create pygame surface from PIL image data
                try:
                    _lizard_sprite = pygame.image.frombuffer(data, size, mode)
                except:
                    # Fallback for older pygame versions
                    _lizard_sprite = pygame.image.fromstring(data, size, mode)
                _lizard_sprite = _lizard_sprite.convert_alpha()
            except ImportError:
                # PIL not available, try direct pygame load (won't work for AVIF but worth trying)
                _lizard_sprite = pygame.image.load('leezard.avif').convert_alpha()
            except Exception as e:
                # If AVIF fails, try PNG as fallback
                try:
                    _lizard_sprite = pygame.image.load('Leezard.png').convert_alpha()
                except:
                    _lizard_sprite = None
        except:
            _lizard_sprite = None
    return _lizard_sprite

def tint_sprite(sprite, color):
    """Tint a grayscale sprite with a color, preserving transparency"""
    if sprite is None:
        return None
    
    # Create a copy to avoid modifying original
    tinted = sprite.copy()
    
    # Create a color surface with alpha channel
    color_surface = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    color_surface.fill((*color, 255))  # Fill with color and full alpha
    
    # Use multiply blend to tint the grayscale sprite
    # This preserves the alpha channel and applies color to grayscale
    tinted.blit(color_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    return tinted

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
        """Load and tint the sprite"""
        base_sprite = get_lizard_sprite()
        if base_sprite:
            self.sprite = tint_sprite(base_sprite, self.tint_color)
            # Scale sprite to match radius (sprite is already 2x enlarged, so scale appropriately)
            if self.sprite:
                # Scale to match enemy size - sprite is already 2x, so we scale based on radius
                target_size = self.radius * 2
                # Get current sprite size
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
        """Check collision with another object"""
        dx = self.x - other.x
        dy = self.y - other.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < (self.radius + other.radius)
    
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


import pygame
from PIL import Image

# Global variable to store selected snake variant (default to row 1)
SELECTED_SNAKE_VARIANT = 1  # Row 1 (0-indexed, default coloration)

def get_snake_palette_row_colors(row_index):
    """Get colors from a specific row in the snake palette"""
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

def get_column_0_color(row_index):
    """Get column 0 color from a specific row (average of skin columns 1,2,5,6)"""
    colors = get_snake_palette_row_colors(row_index)
    if colors and len(colors) > 0:
        return colors[0]  # Column 0 (average of skin columns)
    return (255, 255, 255)  # Default white

def get_available_snake_variants():
    """Get list of available snake variants (including row 0)"""
    try:
        palette_img = Image.open('snake_sprite_sheet_palette.png')
        num_rows = palette_img.size[1] // 50  # 50px per row
        # Return rows 0 through num_rows-1 (including row 0)
        return list(range(0, num_rows))
    except:
        return [0, 1, 2, 3, 4]  # Default variants (including row 0)

class SnakeCustomizationMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.available_variants = get_available_snake_variants()
        # Ensure selected variant is in available variants (default to 1 if not)
        if SELECTED_SNAKE_VARIANT in self.available_variants:
            self.selected_variant = SELECTED_SNAKE_VARIANT
        else:
            self.selected_variant = 1  # Default to row 1
        pygame.font.init()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
        # OPTIMIZATION: Pre-render and cache text surfaces
        self._cached_texts = {}
        self._cached_texts['title'] = self.font_large.render("CHOOSE YOUR SNAKE", True, (0, 255, 0))
        self._cached_texts['instructions'] = self.font_small.render("Use LEFT/RIGHT or A/D to select, ENTER to confirm, ESC to go back", 
                                                                   True, (150, 150, 150))
        
        # OPTIMIZATION: Create snake animations for each variant (for preview)
        self.snake_animations = {}
        # OPTIMIZATION: Cache glow surfaces and scaled sprites
        self._cached_glow_surfaces = {}
        self._cached_scaled_sprites = {}  # (variant, frame_index) -> scaled_sprite
        # OPTIMIZATION: Cache button background surface
        self._cached_button_bg = None
        try:
            from snake_animation import SnakeAnimation
            for variant in self.available_variants:
                # Create animation with idle state, bigger size for visibility, disable flip for performance
                # Much bigger base size for better visibility
                anim = SnakeAnimation(x=0, y=0, size=18, palette_row=variant, disable_flip=True)
                anim.animation_state = 'idle'  # Set to idle animation
                anim.animation_frame = 0
                self.snake_animations[variant] = anim
        except Exception as e:
            print(f"Warning: Could not load snake animations for customization: {e}")
            self.snake_animations = {}
        
        # OPTIMIZATION: Pre-create button background surface (only create once)
        button_size = 100
        self._cached_button_bg = pygame.Surface((button_size - 8, button_size - 8), pygame.SRCALPHA)
        self._cached_button_bg.fill((0, 50, 0, 100))
        
    def handle_events(self, events):
        """Handle menu input"""
        global SELECTED_SNAKE_VARIANT
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    # Move to previous variant
                    current_idx = self.available_variants.index(self.selected_variant)
                    self.selected_variant = self.available_variants[(current_idx - 1) % len(self.available_variants)]
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    # Move to next variant
                    current_idx = self.available_variants.index(self.selected_variant)
                    self.selected_variant = self.available_variants[(current_idx + 1) % len(self.available_variants)]
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Confirm selection
                    SELECTED_SNAKE_VARIANT = self.selected_variant
                    return "confirm"
                elif event.key == pygame.K_ESCAPE:
                    return "back"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # Check if clicking on a variant preview (updated spacing)
                    icon_spacing = 180
                    start_x = self.screen_width // 2 - (len(self.available_variants) * icon_spacing) // 2
                    start_y = self.screen_height // 2
                    
                    for i, variant in enumerate(self.available_variants):
                        icon_x = start_x + i * icon_spacing
                        icon_y = start_y
                        # Use larger click area for bigger snake animations
                        click_size = 120
                        if (icon_x - click_size//2 <= mouse_x <= icon_x + click_size//2 and
                            icon_y - click_size//2 <= mouse_y <= icon_y + click_size//2):
                            self.selected_variant = variant
                            SELECTED_SNAKE_VARIANT = variant
                            return "confirm"
        
        return None
    
    def draw(self, screen):
        """Draw the customization menu - OPTIMIZED"""
        # Background
        screen.fill((0, 0, 0))
        
        # OPTIMIZATION: Use cached title text
        title_rect = self._cached_texts['title'].get_rect(center=(self.screen_width // 2, 150))
        screen.blit(self._cached_texts['title'], title_rect)
        
        # Draw variant previews with idle animations (bigger spacing for bigger snakes)
        icon_spacing = 180
        start_x = self.screen_width // 2 - (len(self.available_variants) * icon_spacing) // 2
        start_y = self.screen_height // 2
        
        for i, variant in enumerate(self.available_variants):
            icon_x = start_x + i * icon_spacing
            icon_y = start_y
            
            is_selected = (variant == self.selected_variant)
            
            # Update and draw snake animation if available
            if variant in self.snake_animations:
                anim = self.snake_animations[variant]
                # Update animation position
                anim.x = icon_x
                anim.y = icon_y
                # Update animation frame
                anim.update_animation()
                
                # Draw selected snake as the button indicator itself (scaled up), unselected snakes normal size
                if is_selected:
                    # Get current frame sprite
                    current_frames = anim.animation_states.get(anim.animation_state, [])
                    if current_frames and anim.animation_frame < len(current_frames):
                        sprite = current_frames[anim.animation_frame]
                        # Scale up selected snake significantly to act as button indicator
                        scale_factor = 1.5  # 50% bigger than normal
                        scaled_size = (int(sprite.get_width() * scale_factor), int(sprite.get_height() * scale_factor))
                        # OPTIMIZATION: Cache scaled sprites
                        cache_key = (variant, anim.animation_frame, 'selected')
                        if cache_key not in self._cached_scaled_sprites:
                            self._cached_scaled_sprites[cache_key] = pygame.transform.scale(sprite, scaled_size)
                        scaled_sprite = self._cached_scaled_sprites[cache_key]
                        
                        # Draw button border around scaled snake
                        border_size = max(scaled_size) + 20
                        button_rect = pygame.Rect(icon_x - border_size//2, icon_y - border_size//2, border_size, border_size)
                        # Draw button border (green glow effect)
                        pygame.draw.rect(screen, (0, 200, 0), button_rect, 4)
                        # Draw subtle background (using cached surface)
                        if self._cached_button_bg:
                            bg_size = border_size - 8
                            bg_scaled = pygame.transform.scale(self._cached_button_bg, (bg_size, bg_size))
                            screen.blit(bg_scaled, (icon_x - bg_size//2, icon_y - bg_size//2))
                        
                        # Draw scaled snake as the button indicator
                        offset_y = anim.y - 32 - 25
                        sprite_rect = scaled_sprite.get_rect(center=(int(anim.x), int(offset_y)))
                        screen.blit(scaled_sprite, sprite_rect)
                    else:
                        # Fallback to normal draw
                        anim.draw(screen, grid_cell_size=32, offset_y_adjust=-25)
                else:
                    # Draw unselected snake at normal size
                    anim.draw(screen, grid_cell_size=32, offset_y_adjust=-25)
            else:
                # Fallback: draw circle if animation not available
                icon_color = get_column_0_color(variant)
                border_color = (0, 255, 0) if is_selected else (100, 100, 100)
                border_width = 4 if is_selected else 2
                icon_size = 60
                pygame.draw.circle(screen, border_color, (icon_x, icon_y), icon_size // 2 + border_width, border_width)
                pygame.draw.circle(screen, icon_color, (icon_x, icon_y), icon_size // 2)
        
        # OPTIMIZATION: Use cached instructions text
        inst_y = self.screen_height - 100
        inst_rect = self._cached_texts['instructions'].get_rect(center=(self.screen_width // 2, inst_y))
        screen.blit(self._cached_texts['instructions'], inst_rect)



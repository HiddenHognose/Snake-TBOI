import pygame

class Menu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_option = 0  # 0 = Start, 1 = Customize Snake, 2 = Testing Mode, 3 = Credits, 4 = Quit
        pygame.font.init()  # Ensure fonts are initialized
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
        # OPTIMIZATION: Pre-render and cache all text surfaces
        self._cached_texts = {}
        self._cached_glow_surfaces = {}
        self._cached_background = None
        self._precache_all_texts()
        self._precache_background()
        
        # Create snake animation for selection indicator (uses currently selected variant)
        self._selection_snake = None
        self._update_selection_snake()
    
    def _precache_all_texts(self):
        """Pre-render all text surfaces to avoid expensive rendering every frame"""
        # Title and subtitle
        self._cached_texts['title'] = self.font_large.render("SNAKETBOI", True, (0, 255, 0))
        self._cached_texts['title_shadow'] = self.font_large.render("SNAKETBOI", True, (0, 100, 0))
        self._cached_texts['subtitle'] = self.font_small.render("A Snake's Binding", True, (100, 255, 100))
        self._cached_texts['instructions'] = self.font_small.render("Use ARROW KEYS or WASD to navigate, ENTER to select", 
                                                                      True, (100, 100, 100))
        
        # Menu option texts (both selected and unselected)
        menu_options = ["START GAME", "CUSTOMISE SNAKE", "TESTING MODE", "CREDITS", "QUIT"]
        for option in menu_options:
            self._cached_texts[f'{option}_selected'] = self.font_medium.render(option, True, (0, 255, 0))
            self._cached_texts[f'{option}_unselected'] = self.font_medium.render(option, True, (120, 120, 120))
            self._cached_texts[f'{option}_glow'] = self.font_medium.render(option, True, (0, 150, 0))
        
        # OPTIMIZATION: Pre-create glow surfaces (only create once, reuse)
        glow_color = (0, 200, 0)
        glow_rect = pygame.Rect(0, 0, 360, 50)
        for i in range(3):
            alpha = 20 - i * 5
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*glow_color, alpha), 
                           (i, i, glow_rect.width - i*2, glow_rect.height - i*2), 
                           border_radius=10)
            self._cached_glow_surfaces[i] = glow_surf
    
    def _update_selection_snake(self):
        """Update the selection snake to use the currently selected variant"""
        try:
            from snake_customization import SELECTED_SNAKE_VARIANT
            from snake_animation import SnakeAnimation
            # Create snake animation with currently selected variant (larger size)
            # Only recreate if variant changed or doesn't exist
            if self._selection_snake is None or self._selection_snake.palette_row != SELECTED_SNAKE_VARIANT:
                self._selection_snake = SnakeAnimation(x=0, y=0, size=10, palette_row=SELECTED_SNAKE_VARIANT, disable_flip=True)
                self._selection_snake.animation_state = 'idle'
                self._selection_snake.animation_frame = 0
                self._selection_snake.animation_timer = 0  # Initialize timer
                self._selection_snake.is_moving = False  # Ensure idle state
        except Exception as e:
            self._selection_snake = None
    
    def _precache_background(self):
        """Pre-render background pattern to avoid drawing lines every frame"""
        # OPTIMIZATION: Create background surface once
        bg_surf = pygame.Surface((self.screen_width, self.screen_height))
        bg_surf.fill((5, 5, 10))
        # Draw decorative lines
        for y in range(0, self.screen_height, 40):
            pygame.draw.line(bg_surf, (0, 20, 0), (0, y), (self.screen_width, y), 1)
        self._cached_background = bg_surf
        
    def handle_events(self, events):
        """Handle menu input"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_option = (self.selected_option - 1) % 5
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_option = (self.selected_option + 1) % 5
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.get_selected_action()
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
            elif event.type == pygame.MOUSEMOTION:
                # OPTIMIZATION: Use correct spacing values (65px, not 50px)
                mouse_x, mouse_y = pygame.mouse.get_pos()
                menu_start_y = self.screen_height // 2 + 20
                option_spacing = 65
                start_y = menu_start_y
                customize_y = start_y + option_spacing
                testing_y = customize_y + option_spacing
                credits_y = testing_y + option_spacing
                quit_y = credits_y + option_spacing
                
                if start_y - 30 <= mouse_y <= start_y + 30:
                    self.selected_option = 0
                elif customize_y - 30 <= mouse_y <= customize_y + 30:
                    self.selected_option = 1
                elif testing_y - 30 <= mouse_y <= testing_y + 30:
                    self.selected_option = 2
                elif credits_y - 30 <= mouse_y <= credits_y + 30:
                    self.selected_option = 3
                elif quit_y - 30 <= mouse_y <= quit_y + 30:
                    self.selected_option = 4
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    return self.get_selected_action()
        
        return None
    
    def get_selected_action(self):
        """Return the action for the selected option"""
        if self.selected_option == 0:
            return "start"
        elif self.selected_option == 1:
            return "customize"
        elif self.selected_option == 2:
            return "testing"
        elif self.selected_option == 3:
            return "credits"
        else:
            return "quit"
    
    def draw(self, screen):
        """Draw the menu - OPTIMIZED with cached surfaces"""
        # OPTIMIZATION: Use pre-rendered background
        screen.blit(self._cached_background, (0, 0))
        
        # OPTIMIZATION: Use cached title text
        title_rect = self._cached_texts['title'].get_rect(center=(self.screen_width // 2, 120))
        # Draw title shadow/glow (cached)
        for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
            shadow_rect = self._cached_texts['title_shadow'].get_rect(center=(self.screen_width // 2 + offset[0], 120 + offset[1]))
            screen.blit(self._cached_texts['title_shadow'], shadow_rect)
        screen.blit(self._cached_texts['title'], title_rect)
        
        # OPTIMIZATION: Use cached subtitle
        subtitle_rect = self._cached_texts['subtitle'].get_rect(center=(self.screen_width // 2, 180))
        screen.blit(self._cached_texts['subtitle'], subtitle_rect)
        
        # Menu options with better spacing and styling
        menu_start_y = self.screen_height // 2 + 20
        option_spacing = 65
        start_y = menu_start_y
        customize_y = start_y + option_spacing
        testing_y = customize_y + option_spacing
        credits_y = testing_y + option_spacing
        quit_y = credits_y + option_spacing
        
        # OPTIMIZATION: Helper function using cached text surfaces
        def draw_menu_option(option_key, y_pos, is_selected):
            # Selection glow effect (using cached surfaces)
            if is_selected:
                glow_rect = pygame.Rect(self.screen_width // 2 - 180, y_pos - 25, 360, 50)
                # Draw cached glow surfaces
                for i in range(3):
                    screen.blit(self._cached_glow_surfaces[i], (glow_rect.x, glow_rect.y))
            
            # OPTIMIZATION: Use cached text surfaces
            if is_selected:
                # Draw glow text (cached)
                glow_text = self._cached_texts[f'{option_key}_glow']
                glow_rect = glow_text.get_rect(center=(self.screen_width // 2 + 1, y_pos + 1))
                screen.blit(glow_text, glow_rect)
                # Main text (cached)
                option_text = self._cached_texts[f'{option_key}_selected']
            else:
                option_text = self._cached_texts[f'{option_key}_unselected']
            
            option_rect = option_text.get_rect(center=(self.screen_width // 2, y_pos))
            screen.blit(option_text, option_rect)
            
            # Draw snake as selection indicator instead of arrows
            if is_selected:
                # Update selection snake if needed (check if variant changed)
                self._update_selection_snake()
                
                if self._selection_snake:
                    # Ensure animation state is idle and update animation every frame
                    self._selection_snake.animation_state = 'idle'
                    self._selection_snake.is_moving = False
                    self._selection_snake.is_attacking = False
                    self._selection_snake.is_going_down = False
                    self._selection_snake.is_defeated = False
                    
                    # Update animation (ensures idle animation plays every frame)
                    self._selection_snake.update_animation()
                    
                    # Get current frame sprite (gets updated frame from animation)
                    current_frames = self._selection_snake.animation_states.get(self._selection_snake.animation_state, [])
                    if current_frames and self._selection_snake.animation_frame < len(current_frames):
                        sprite = current_frames[self._selection_snake.animation_frame]
                        
                        # Position above text center
                        snake_y = y_pos - 25
                        
                        # Draw snake on left side (flip to face right toward center)
                        left_x = option_rect.left - 50
                        left_flipped = pygame.transform.flip(sprite, True, False)
                        left_rect = left_flipped.get_rect(center=(left_x, snake_y))
                        screen.blit(left_flipped, left_rect)
                        
                        # Draw snake on right side (no flip - original faces left toward center)
                        right_x = option_rect.right + 50
                        right_rect = sprite.get_rect(center=(right_x, snake_y))
                        screen.blit(sprite, right_rect)
            
            return option_rect
        
        # Draw all menu options (using cached surfaces)
        draw_menu_option("START GAME", start_y, self.selected_option == 0)
        draw_menu_option("CUSTOMISE SNAKE", customize_y, self.selected_option == 1)
        draw_menu_option("TESTING MODE", testing_y, self.selected_option == 2)
        draw_menu_option("CREDITS", credits_y, self.selected_option == 3)
        draw_menu_option("QUIT", quit_y, self.selected_option == 4)
        
        # OPTIMIZATION: Use cached instructions text
        inst_y = self.screen_height - 60
        inst_rect = self._cached_texts['instructions'].get_rect(center=(self.screen_width // 2, inst_y))
        screen.blit(self._cached_texts['instructions'], inst_rect)
        
        # Draw decorative snake
        self.draw_decorative_snake(screen)
    
    def draw_decorative_snake(self, screen):
        """Draw a decorative snake on the menu"""
        # Enhanced decorative snake with better visuals
        center_x = self.screen_width // 2
        center_y = 80
        
        # Draw snake segments in a smooth curve with gradient
        num_segments = 7
        for i in range(num_segments):
            x = center_x - 80 + i * 18
            y = center_y + int(i * 2.5)
            # Gradient effect - darker towards tail
            intensity = 150 + (i * 15)
            intensity = min(255, intensity)
            segment_color = (0, intensity, 0)
            # Outer glow
            pygame.draw.circle(screen, (0, intensity // 2, 0), (x, y), 14)
            # Main segment
            pygame.draw.circle(screen, segment_color, (x, y), 12)
            # Inner highlight
            pygame.draw.circle(screen, (0, min(255, intensity + 30), 0), (x, y), 8)
        
        # Draw head with more detail
        head_x = center_x - 80 + (num_segments - 1) * 18
        head_y = center_y + int((num_segments - 1) * 2.5)
        # Head glow
        pygame.draw.circle(screen, (0, 100, 0), (head_x, head_y), 18)
        # Head main
        pygame.draw.circle(screen, (0, 255, 0), (head_x, head_y), 16)
        # Eyes
        pygame.draw.circle(screen, (255, 255, 255), (head_x - 6, head_y - 4), 4)
        pygame.draw.circle(screen, (255, 255, 255), (head_x + 6, head_y - 4), 4)
        # Eye pupils
        pygame.draw.circle(screen, (0, 0, 0), (head_x - 6, head_y - 4), 2)
        pygame.draw.circle(screen, (0, 0, 0), (head_x + 6, head_y - 4), 2)

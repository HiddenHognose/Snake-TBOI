import pygame

class Menu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_option = 0  # 0 = Start, 1 = Quit
        pygame.font.init()  # Ensure fonts are initialized
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
    def handle_events(self, events):
        """Handle menu input"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_option = (self.selected_option - 1) % 2
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_option = (self.selected_option + 1) % 2
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return self.get_selected_action()
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
            elif event.type == pygame.MOUSEMOTION:
                # Check if mouse is over menu options
                mouse_x, mouse_y = pygame.mouse.get_pos()
                start_y = self.screen_height // 2 + 50
                quit_y = start_y + 60
                
                if start_y <= mouse_y <= start_y + 40:
                    self.selected_option = 0
                elif quit_y <= mouse_y <= quit_y + 40:
                    self.selected_option = 1
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    return self.get_selected_action()
        
        return None
    
    def get_selected_action(self):
        """Return the action for the selected option"""
        if self.selected_option == 0:
            return "start"
        else:
            return "quit"
    
    def draw(self, screen):
        """Draw the menu"""
        # Background
        screen.fill((0, 0, 0))
        
        # Title
        title_text = self.font_large.render("SNAKETBOI", True, (0, 255, 0))
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 150))
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_text = self.font_small.render("A Snake's Binding", True, (0, 200, 0))
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, 200))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Menu options
        start_y = self.screen_height // 2 + 50
        quit_y = start_y + 60
        
        # Start Game option
        start_color = (0, 255, 0) if self.selected_option == 0 else (100, 100, 100)
        start_text = self.font_medium.render("START GAME", True, start_color)
        start_rect = start_text.get_rect(center=(self.screen_width // 2, start_y))
        screen.blit(start_text, start_rect)
        
        # Draw selection indicator for Start
        if self.selected_option == 0:
            pygame.draw.circle(screen, (0, 255, 0), 
                             (start_rect.left - 30, start_rect.centery), 8)
            pygame.draw.circle(screen, (0, 255, 0), 
                             (start_rect.right + 30, start_rect.centery), 8)
        
        # Quit option
        quit_color = (0, 255, 0) if self.selected_option == 1 else (100, 100, 100)
        quit_text = self.font_medium.render("QUIT", True, quit_color)
        quit_rect = quit_text.get_rect(center=(self.screen_width // 2, quit_y))
        screen.blit(quit_text, quit_rect)
        
        # Draw selection indicator for Quit
        if self.selected_option == 1:
            pygame.draw.circle(screen, (0, 255, 0), 
                             (quit_rect.left - 30, quit_rect.centery), 8)
            pygame.draw.circle(screen, (0, 255, 0), 
                             (quit_rect.right + 30, quit_rect.centery), 8)
        
        # Instructions
        inst_y = self.screen_height - 80
        inst_text = self.font_small.render("Use ARROW KEYS or WASD to navigate, ENTER to select", 
                                          True, (150, 150, 150))
        inst_rect = inst_text.get_rect(center=(self.screen_width // 2, inst_y))
        screen.blit(inst_text, inst_rect)
        
        # Draw decorative snake
        self.draw_decorative_snake(screen)
    
    def draw_decorative_snake(self, screen):
        """Draw a decorative snake on the menu"""
        # Simple snake body segments
        center_x = self.screen_width // 2
        center_y = 100
        
        # Draw snake segments in a curve
        for i in range(5):
            x = center_x - 60 + i * 15
            y = center_y + i * 3
            pygame.draw.circle(screen, (0, 200, 0), (x, y), 12)
            pygame.draw.circle(screen, (0, 150, 0), (x, y), 10)
        
        # Draw head
        head_x = center_x - 60 + 4 * 15
        head_y = center_y + 4 * 3
        pygame.draw.circle(screen, (0, 255, 0), (head_x, head_y), 15)
        pygame.draw.circle(screen, (255, 255, 255), (head_x - 5, head_y - 3), 3)
        pygame.draw.circle(screen, (255, 255, 255), (head_x + 5, head_y - 3), 3)


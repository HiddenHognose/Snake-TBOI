import pygame
import math
import random
from enemy_types import get_lizard_sprite, tint_sprite

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 80  # BIIIIIG LEEZARD
        self.speed = 1.2
        self.max_health = 15
        self.health = self.max_health
        # Neon red for boss
        self.tint_color = (255, 0, 0)  # Neon Red
        self.sprite = None
        self._load_sprite()
        self.attack_cooldown = 0
        self.attack_delay = 90  # Attack every 1.5 seconds at 60 FPS
        self.charge_direction = None
        self.charging = False
        self.charge_timer = 0
    
    def _load_sprite(self):
        """Load and tint the boss sprite - BIIIIIG LEEZARD"""
        base_sprite = get_lizard_sprite()
        if base_sprite:
            self.sprite = tint_sprite(base_sprite, self.tint_color)
            # Boss is much bigger - scale to match radius
            if self.sprite:
                # Scale to match boss size
                target_size = self.radius * 2
                current_size = max(self.sprite.get_width(), self.sprite.get_height())
                if current_size > 0:
                    scale_factor = target_size / current_size
                    new_width = int(self.sprite.get_width() * scale_factor)
                    new_height = int(self.sprite.get_height() * scale_factor)
                    if new_width > 0 and new_height > 0:
                        self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
        
    def update(self, player_x, player_y, bullets):
        """Update boss AI and attacks"""
        # Handle charging attack
        if self.charging:
            self.charge_timer -= 1
            if self.charge_timer <= 0:
                self.charging = False
                self.charge_direction = None
            else:
                # Move in charge direction
                if self.charge_direction:
                    self.x += self.charge_direction[0] * self.speed * 2
                    self.y += self.charge_direction[1] * self.speed * 2
                return
        
        # Normal movement towards player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            # Normalize direction
            dx /= dist
            dy /= dist
            
            # Move towards player
            self.x += dx * self.speed
            self.y += dy * self.speed
        
        # Attack logic
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        else:
            # Start charge attack
            if dist > 0 and random.random() < 0.3:  # 30% chance to charge
                self.charging = True
                self.charge_timer = 60  # Charge for 1 second
                self.charge_direction = (dx, dy)
                self.attack_cooldown = self.attack_delay
    
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
        """Draw the BIIIIIG LEEZARD boss"""
        if self.sprite:
            # Draw sprite centered on boss position
            sprite_rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.sprite, sprite_rect)
        else:
            # Fallback to circle if sprite not loaded
            pygame.draw.circle(screen, self.tint_color, (int(self.x), int(self.y)), self.radius)
        
        # Draw health bar above boss
        bar_width = 120
        bar_height = 10
        bar_x = int(self.x - bar_width // 2)
        bar_y = int(self.y - self.radius - 20)
        
        # Background
        pygame.draw.rect(screen, (50, 50, 50), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Health
        health_width = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(screen, (255, 0, 0), 
                        (bar_x, bar_y, health_width, bar_height))
        
        # Border
        pygame.draw.rect(screen, (255, 255, 255), 
                        (bar_x, bar_y, bar_width, bar_height), 2)


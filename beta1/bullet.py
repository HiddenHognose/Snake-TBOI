import pygame
import math

class Bullet:
    def __init__(self, x, y, dx, dy, is_player=True, color=None):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 8
        self.radius = 4
        self.damage = 1
        self.is_player = is_player  # True if shot by player, False if shot by enemy
        self.color = color  # Custom color (if provided, overrides default colors)
        
    def update(self):
        """Move the bullet"""
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
    
    def collides_with(self, other):
        """Check collision with another object"""
        dx = self.x - other.x
        dy = self.y - other.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < (self.radius + other.radius)
    
    def draw(self, screen):
        """Draw the bullet"""
        if self.color:
            # Use custom color if provided
            # Create darker shade for inner circle
            dark_color = tuple(max(0, c - 50) for c in self.color)
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, dark_color, (int(self.x), int(self.y)), self.radius - 1)
        elif self.is_player:
            # Player bullets are green
            pygame.draw.circle(screen, (0, 255, 0), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (0, 200, 0), (int(self.x), int(self.y)), self.radius - 1)
        else:
            # Enemy bullets are red
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (200, 0, 0), (int(self.x), int(self.y)), self.radius - 1)


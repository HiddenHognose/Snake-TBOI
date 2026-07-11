import pygame
import math
import random

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.speed = 1.5  # Slower enemies (reduced from 2)
        self.max_health = 2
        self.health = self.max_health
        self.color = (139, 69, 19)  # Brown lizard color
        self.dark_color = (101, 67, 33)
        
    def update(self, player_x, player_y):
        """Move towards the player"""
        # Calculate direction to player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            # Normalize and move
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
        """Draw the lizard enemy"""
        # Draw lizard body (elongated oval)
        pygame.draw.ellipse(screen, self.color, 
                          (int(self.x - self.radius), int(self.y - self.radius//2),
                           self.radius * 2, self.radius))
        
        # Draw head
        pygame.draw.circle(screen, self.dark_color, 
                          (int(self.x - self.radius//2), int(self.y)), self.radius//2)
        
        # Draw legs (small circles)
        leg_size = 3
        pygame.draw.circle(screen, self.dark_color, 
                          (int(self.x - self.radius), int(self.y + 2)), leg_size)
        pygame.draw.circle(screen, self.dark_color, 
                          (int(self.x + self.radius), int(self.y + 2)), leg_size)
        
        # Draw tail
        pygame.draw.line(screen, self.color, 
                        (int(self.x + self.radius), int(self.y)),
                        (int(self.x + self.radius + 8), int(self.y - 3)), 2)


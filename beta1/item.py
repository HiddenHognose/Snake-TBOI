import pygame
import math
from item_definitions import generate_item_color

class Item:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.radius = 15  # Slightly bigger for treasure items
        self.item_type = item_type  # 'health', 'damage', 'speed', 'double_shot', 'follower'
        self.collected = False
        
        # Get color from item_definitions (auto-generates if not found)
        self.color = generate_item_color(item_type)
        
        # Colors for different items (legacy, kept for specific drawing)
        self.colors = {
            'health': (255, 0, 0),      # Red heart
            'damage': (255, 200, 0),   # Gold/yellow
            'speed': (0, 200, 255),    # Cyan
            'double_shot': (255, 100, 255),  # Magenta
            'follower': (0, 255, 255),  # Bright cyan
            'trapdoor': (50, 50, 50)  # Dark gray
        }
        
        # Use generated color if not in legacy colors dict
        if item_type not in self.colors:
            self.color = generate_item_color(item_type)
        else:
            self.color = self.colors.get(item_type, (255, 255, 255))
    
    def collides_with(self, other):
        """Check collision with player"""
        dx = self.x - other.x
        dy = self.y - other.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist < (self.radius + other.radius)
    
    def draw(self, screen):
        """Draw the item"""
        if self.collected:
            return
        
        # Draw item based on type
        if self.item_type == 'health':
            # Draw heart shape
            pygame.draw.circle(screen, self.color, 
                             (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 150, 150), 
                             (int(self.x), int(self.y)), self.radius - 3)
        elif self.item_type == 'damage':
            # Draw star/upgrade symbol
            pygame.draw.circle(screen, self.color, 
                             (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 100), 
                             (int(self.x), int(self.y)), self.radius - 3)
            # Draw plus sign
            pygame.draw.line(screen, (255, 255, 255), 
                           (int(self.x - 5), int(self.y)), 
                           (int(self.x + 5), int(self.y)), 2)
            pygame.draw.line(screen, (255, 255, 255), 
                           (int(self.x), int(self.y - 5)), 
                           (int(self.x), int(self.y + 5)), 2)
        elif self.item_type == 'speed':
            # Draw speed lines
            pygame.draw.circle(screen, self.color, 
                             (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (100, 255, 255), 
                             (int(self.x), int(self.y)), self.radius - 3)
            # Draw arrow
            pygame.draw.polygon(screen, (255, 255, 255), [
                (int(self.x - 4), int(self.y)),
                (int(self.x + 4), int(self.y)),
                (int(self.x), int(self.y - 6))
            ])
        elif self.item_type == 'double_shot':
            # Draw two bullets overlapping
            pygame.draw.circle(screen, self.color, 
                             (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 150, 255), 
                             (int(self.x), int(self.y)), self.radius - 3)
            # Draw two bullet symbols
            pygame.draw.circle(screen, (255, 255, 255), 
                             (int(self.x - 4), int(self.y)), 4)
            pygame.draw.circle(screen, (255, 255, 255), 
                             (int(self.x + 4), int(self.y)), 4)
        elif self.item_type == 'follower':
            # Draw follower symbol (orbiting companion)
            pygame.draw.circle(screen, self.color, 
                             (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (0, 200, 200), 
                             (int(self.x), int(self.y)), self.radius - 3)
            # Draw small companion circle
            angle = pygame.time.get_ticks() / 1000.0  # Animate rotation
            orbit_x = int(self.x + math.cos(angle) * 8)
            orbit_y = int(self.y + math.sin(angle) * 8)
            pygame.draw.circle(screen, (255, 255, 255), 
                             (orbit_x, orbit_y), 4)
        elif self.item_type == 'health_up':
            # Draw heart with plus
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 150, 150), (int(self.x), int(self.y)), self.radius - 3)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x - 4), int(self.y)), 
                           (int(self.x + 4), int(self.y)), 2)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y - 4)), 
                           (int(self.x), int(self.y + 4)), 2)
        elif self.item_type == 'damage_up':
            # Draw star with plus
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 220, 100), (int(self.x), int(self.y)), self.radius - 3)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x - 5), int(self.y)), 
                           (int(self.x + 5), int(self.y)), 2)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y - 5)), 
                           (int(self.x), int(self.y + 5)), 2)
        elif self.item_type == 'speed_up':
            # Draw speed arrow with plus
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (150, 255, 255), (int(self.x), int(self.y)), self.radius - 3)
            pygame.draw.polygon(screen, (255, 255, 255), [
                (int(self.x - 3), int(self.y)),
                (int(self.x + 3), int(self.y)),
                (int(self.x), int(self.y - 6))
            ])
        elif self.item_type == 'triple_shot':
            # Draw three bullets
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (200, 50, 200), (int(self.x), int(self.y)), self.radius - 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x - 5), int(self.y)), 4)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 4)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x + 5), int(self.y)), 4)
        elif self.item_type == 'bullet_size':
            # Draw large bullet
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 200, 100), (int(self.x), int(self.y)), self.radius - 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 8)
        elif self.item_type == 'bullet_speed':
            # Draw fast bullet
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 150), (int(self.x), int(self.y)), self.radius - 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 5)
            # Draw speed lines
            pygame.draw.line(screen, (255, 255, 255), (int(self.x - 6), int(self.y)), 
                           (int(self.x - 10), int(self.y)), 2)
        elif self.item_type == 'fire_rate':
            # Draw rapid fire symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 100, 200), (int(self.x), int(self.y)), self.radius - 3)
            # Draw multiple bullets
            for i in range(3):
                pygame.draw.circle(screen, (255, 255, 255), 
                                 (int(self.x - 4 + i * 4), int(self.y)), 3)
        elif self.item_type == 'knockback':
            # Draw knockback symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (200, 200, 255), (int(self.x), int(self.y)), self.radius - 3)
            # Draw arrow pointing outward
            pygame.draw.polygon(screen, (255, 255, 255), [
                (int(self.x), int(self.y)),
                (int(self.x + 8), int(self.y - 3)),
                (int(self.x + 8), int(self.y + 3))
            ])
        elif self.item_type == 'armor':
            # Draw shield
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (150, 150, 150), (int(self.x), int(self.y)), self.radius - 3)
            # Draw shield shape
            pygame.draw.arc(screen, (255, 255, 255), 
                          (int(self.x - 8), int(self.y - 8), 16, 16), 
                          0, math.pi, 3)
        elif self.item_type == 'regen':
            # Draw regeneration symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (100, 255, 100), (int(self.x), int(self.y)), self.radius - 3)
            # Draw plus sign
            pygame.draw.line(screen, (255, 255, 255), (int(self.x - 4), int(self.y)), 
                           (int(self.x + 4), int(self.y)), 2)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y - 4)), 
                           (int(self.x), int(self.y + 4)), 2)
        elif self.item_type == 'lucky':
            # Draw lucky clover/star
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 240, 0), (int(self.x), int(self.y)), self.radius - 3)
            # Draw star
            for i in range(4):
                angle = (math.pi / 2) * i
                x1 = int(self.x + math.cos(angle) * 6)
                y1 = int(self.y + math.sin(angle) * 6)
                pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), (x1, y1), 2)
        elif self.item_type == 'quad_shot':
            # Draw four bullets
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (150, 0, 150), (int(self.x), int(self.y)), self.radius - 3)
            for i in range(4):
                angle = (math.pi / 2) * i
                bullet_x = int(self.x + math.cos(angle) * 6)
                bullet_y = int(self.y + math.sin(angle) * 6)
                pygame.draw.circle(screen, (255, 255, 255), (bullet_x, bullet_y), 3)
        elif self.item_type == 'piercing':
            # Draw arrow through circle
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x - 8), int(self.y)), 
                           (int(self.x + 8), int(self.y)), 3)
        elif self.item_type == 'explosive':
            # Draw explosion symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            for i in range(6):
                angle = (math.pi / 3) * i
                x1 = int(self.x + math.cos(angle) * 8)
                y1 = int(self.y + math.sin(angle) * 8)
                pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), (x1, y1), 2)
        elif self.item_type == 'homing':
            # Draw target symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 6, 2)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 3, 2)
        elif self.item_type == 'chain_lightning':
            # Draw lightning bolt
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            points = [(int(self.x), int(self.y - 8)), (int(self.x + 3), int(self.y - 2)),
                     (int(self.x - 2), int(self.y)), (int(self.x + 2), int(self.y + 8))]
            pygame.draw.lines(screen, (255, 255, 255), False, points, 2)
        elif self.item_type == 'shield':
            # Draw shield
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.arc(screen, (255, 255, 255), (int(self.x - 8), int(self.y - 8), 16, 16), 
                         0, math.pi, 3)
        elif self.item_type == 'teleport':
            # Draw teleport symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 6, 2)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 3)
        elif self.item_type == 'slow_time':
            # Draw clock symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 7, 2)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), 
                           (int(self.x), int(self.y - 5)), 2)
        elif self.item_type == 'crit_chance':
            # Draw star
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            for i in range(5):
                angle = (2 * math.pi / 5) * i - math.pi / 2
                x1 = int(self.x + math.cos(angle) * 6)
                y1 = int(self.y + math.sin(angle) * 6)
                pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), (x1, y1), 2)
        elif self.item_type == 'life_steal':
            # Draw heart with arrow
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 150, 150), (int(self.x), int(self.y)), 5)
            pygame.draw.polygon(screen, (255, 255, 255), [
                (int(self.x + 4), int(self.y)), (int(self.x + 8), int(self.y - 2)),
                (int(self.x + 8), int(self.y + 2))
            ])
        elif self.item_type == 'bullet_bounce':
            # Draw bouncing arrow
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x - 6), int(self.y)), 
                           (int(self.x + 2), int(self.y - 4)), 2)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x + 2), int(self.y - 4)), 
                           (int(self.x + 6), int(self.y)), 2)
        elif self.item_type == 'split_shot':
            # Draw splitting arrows
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x - 6), int(self.y)), 
                           (int(self.x), int(self.y)), 2)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), 
                           (int(self.x + 4), int(self.y - 3)), 2)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), 
                           (int(self.x + 4), int(self.y + 3)), 2)
        elif self.item_type == 'rapid_fire':
            # Draw multiple bullets
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            for i in range(4):
                pygame.draw.circle(screen, (255, 255, 255), 
                                 (int(self.x - 6 + i * 4), int(self.y)), 2)
        elif self.item_type == 'mega_bullet':
            # Draw huge bullet
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 200, 100), (int(self.x), int(self.y)), 10)
        elif self.item_type == 'poison':
            # Draw poison symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (200, 255, 100), (int(self.x), int(self.y)), 6)
            pygame.draw.circle(screen, (100, 200, 50), (int(self.x), int(self.y)), 3)
        elif self.item_type == 'freeze':
            # Draw ice symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.polygon(screen, (255, 255, 255), [
                (int(self.x), int(self.y - 6)), (int(self.x - 3), int(self.y + 2)),
                (int(self.x + 3), int(self.y + 2))
            ])
        elif self.item_type == 'magnet':
            # Draw magnet symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.arc(screen, (255, 255, 255), (int(self.x - 6), int(self.y - 6), 12, 12),
                         0, math.pi, 2)
            pygame.draw.arc(screen, (255, 255, 255), (int(self.x - 6), int(self.y - 6), 12, 12),
                         math.pi, 2 * math.pi, 2)
        elif self.item_type == 'extra_life':
            # Draw extra life symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 200, 200), (int(self.x), int(self.y)), 7)
            pygame.draw.circle(screen, (255, 100, 100), (int(self.x), int(self.y)), 4)
        elif self.item_type == 'damage_boost':
            # Draw large damage symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 240, 0), (int(self.x), int(self.y)), self.radius - 3)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x - 6), int(self.y)), 
                           (int(self.x + 6), int(self.y)), 3)
            pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y - 6)), 
                           (int(self.x), int(self.y + 6)), 3)
        elif self.item_type == 'speed_boost':
            # Draw large speed symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.polygon(screen, (255, 255, 255), [
                (int(self.x - 5), int(self.y)), (int(self.x + 5), int(self.y)),
                (int(self.x), int(self.y - 8))
            ])
        elif self.item_type == 'health_boost':
            # Draw large health symbol
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 200, 200), (int(self.x), int(self.y)), 8)
            pygame.draw.circle(screen, (255, 150, 150), (int(self.x), int(self.y)), 5)
        elif self.item_type == 'trapdoor':
            # Draw trapdoor (dark circle with spiral pattern)
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (30, 30, 30), (int(self.x), int(self.y)), self.radius - 3)
            # Draw spiral pattern
            for i in range(8):
                angle = (2 * math.pi / 8) * i
                start_x = int(self.x + math.cos(angle) * (self.radius - 5))
                start_y = int(self.y + math.sin(angle) * (self.radius - 5))
                end_x = int(self.x + math.cos(angle) * (self.radius - 15))
                end_y = int(self.y + math.sin(angle) * (self.radius - 15))
                pygame.draw.line(screen, (100, 100, 100), (start_x, start_y), (end_x, end_y), 2)


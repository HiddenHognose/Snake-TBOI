import pygame
import math

# Define 20 different follower types with unique properties
FOLLOWER_TYPES = [
    {'name': 'Blue Buddy', 'orbit_distance': 40, 'orbit_speed': 0.03, 'color': (100, 150, 255), 'dark_color': (50, 100, 200), 'shoot_delay': 50},
    {'name': 'Red Rascal', 'orbit_distance': 55, 'orbit_speed': 0.04, 'color': (255, 100, 100), 'dark_color': (200, 50, 50), 'shoot_delay': 45},
    {'name': 'Green Guardian', 'orbit_distance': 70, 'orbit_speed': 0.05, 'color': (100, 255, 100), 'dark_color': (50, 200, 50), 'shoot_delay': 40},
    {'name': 'Purple Pal', 'orbit_distance': 85, 'orbit_speed': 0.06, 'color': (200, 100, 255), 'dark_color': (150, 50, 200), 'shoot_delay': 48},
    {'name': 'Yellow Yeller', 'orbit_distance': 100, 'orbit_speed': 0.07, 'color': (255, 255, 100), 'dark_color': (200, 200, 50), 'shoot_delay': 42},
    {'name': 'Cyan Circle', 'orbit_distance': 45, 'orbit_speed': 0.08, 'color': (100, 255, 255), 'dark_color': (50, 200, 200), 'shoot_delay': 38},
    {'name': 'Orange Orbit', 'orbit_distance': 60, 'orbit_speed': 0.09, 'color': (255, 150, 50), 'dark_color': (200, 100, 25), 'shoot_delay': 44},
    {'name': 'Pink Partner', 'orbit_distance': 75, 'orbit_speed': 0.04, 'color': (255, 150, 200), 'dark_color': (200, 100, 150), 'shoot_delay': 46},
    {'name': 'Lime Light', 'orbit_distance': 90, 'orbit_speed': 0.05, 'color': (150, 255, 100), 'dark_color': (100, 200, 50), 'shoot_delay': 41},
    {'name': 'Teal Team', 'orbit_distance': 50, 'orbit_speed': 0.06, 'color': (50, 200, 200), 'dark_color': (25, 150, 150), 'shoot_delay': 43},
    {'name': 'Magenta Mate', 'orbit_distance': 65, 'orbit_speed': 0.07, 'color': (255, 50, 200), 'dark_color': (200, 25, 150), 'shoot_delay': 39},
    {'name': 'Coral Comrade', 'orbit_distance': 80, 'orbit_speed': 0.08, 'color': (255, 127, 127), 'dark_color': (200, 80, 80), 'shoot_delay': 47},
    {'name': 'Mint Minder', 'orbit_distance': 95, 'orbit_speed': 0.09, 'color': (150, 255, 200), 'dark_color': (100, 200, 150), 'shoot_delay': 37},
    {'name': 'Lavender Link', 'orbit_distance': 42, 'orbit_speed': 0.10, 'color': (200, 150, 255), 'dark_color': (150, 100, 200), 'shoot_delay': 49},
    {'name': 'Peach Pal', 'orbit_distance': 58, 'orbit_speed': 0.11, 'color': (255, 200, 150), 'dark_color': (200, 150, 100), 'shoot_delay': 36},
    {'name': 'Turquoise Twin', 'orbit_distance': 72, 'orbit_speed': 0.12, 'color': (64, 224, 208), 'dark_color': (40, 180, 160), 'shoot_delay': 40},
    {'name': 'Salmon Sidekick', 'orbit_distance': 88, 'orbit_speed': 0.13, 'color': (250, 128, 114), 'dark_color': (200, 100, 90), 'shoot_delay': 45},
    {'name': 'Emerald Escort', 'orbit_distance': 52, 'orbit_speed': 0.14, 'color': (80, 200, 120), 'dark_color': (50, 150, 80), 'shoot_delay': 38},
    {'name': 'Violet Vanguard', 'orbit_distance': 68, 'orbit_speed': 0.15, 'color': (138, 43, 226), 'dark_color': (100, 30, 180), 'shoot_delay': 42},
    {'name': 'Amber Ally', 'orbit_distance': 82, 'orbit_speed': 0.16, 'color': (255, 191, 0), 'dark_color': (200, 150, 0), 'shoot_delay': 44},
]

class Follower:
    """A companion that follows the player and shoots at enemies"""
    def __init__(self, player, follower_type_index):
        self.player = player
        self.x = player.x
        self.y = player.y
        self.radius = 10
        self.follower_type_index = follower_type_index
        follower_data = FOLLOWER_TYPES[follower_type_index]
        self.name = follower_data['name']
        self.orbit_distance = follower_data['orbit_distance']
        self.orbit_angle = (follower_type_index * (2 * math.pi / 20))  # Start at different angles
        self.orbit_speed = follower_data['orbit_speed']
        self.shoot_cooldown = 0
        self.shoot_delay = follower_data['shoot_delay']
        self.color = follower_data['color']
        self.dark_color = follower_data['dark_color']
    
    def update(self, enemies, bosses, bullets):
        """Update follower position and shooting"""
        # Orbit around player
        self.orbit_angle += self.orbit_speed
        self.x = self.player.x + math.cos(self.orbit_angle) * self.orbit_distance
        self.y = self.player.y + math.sin(self.orbit_angle) * self.orbit_distance
        
        # Find nearest enemy or boss
        nearest_target = None
        nearest_dist = float('inf')
        
        # Check enemies
        for enemy in enemies:
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_target = enemy
        
        # Check bosses
        for boss in bosses:
            dx = boss.x - self.x
            dy = boss.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_target = boss
        
        # Shoot at nearest target
        if nearest_target and nearest_dist < 500:  # Increased range
            if self.shoot_cooldown <= 0:
                dx = nearest_target.x - self.x
                dy = nearest_target.y - self.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    dx /= dist
                    dy /= dist
                    from bullet import Bullet
                    # Pass follower's color to bullet
                    bullet = Bullet(self.x, self.y, dx, dy, is_player=True, color=self.color)
                    bullets.append(bullet)
                    self.shoot_cooldown = self.shoot_delay
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def draw(self, screen):
        """Draw the follower"""
        # Draw main body
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, self.dark_color, (int(self.x), int(self.y)), self.radius - 2)
        
        # Draw eyes
        eye_offset = 3
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(self.x - eye_offset), int(self.y - 2)), 2)
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(self.x + eye_offset), int(self.y - 2)), 2)
        pygame.draw.circle(screen, (0, 0, 0), 
                          (int(self.x - eye_offset), int(self.y - 2)), 1)
        pygame.draw.circle(screen, (0, 0, 0), 
                          (int(self.x + eye_offset), int(self.y - 2)), 1)

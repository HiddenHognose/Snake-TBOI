import pygame
import math
import random
from player import Player
from enemy_types import Enemy, FastEnemy, TankEnemy, RangedEnemy, ZigzagEnemy
from bullet import Bullet
from boss import Boss
from item import Item
from follower import Follower
from room import RoomManager
from menu import Menu

# Pygame will be initialized in main

# Game constants (will be set to fullscreen size in main)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
GRAY = (128, 128, 128)

class Game:
    def __init__(self, screen=None, clock=None, screen_width=800, screen_height=600):
        if screen is None:
            self.screen = pygame.display.set_mode((screen_width, screen_height))
        else:
            self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        pygame.display.set_caption("Snaketboi - A Snake's Binding")
        if clock is None:
            self.clock = pygame.time.Clock()
        else:
            self.clock = clock
        self.running = True
        self.return_to_menu = False  # Flag to return to menu instead of quitting
        
        # Game objects
        self.player = Player(screen_width // 2, screen_height // 2)
        self.player.screen_width = screen_width
        self.player.screen_height = screen_height
        self.enemies = []
        self.bosses = []  # Separate list for bosses
        self.bullets = []
        self.items = []
        self.followers = []  # List of followers (can have multiple)
        self.collected_follower_types = set()  # Track which follower types we've collected
        self.collected_items = set()  # Track all collected non-stackable items
        self.room_manager = RoomManager(screen_width, screen_height)
        
        # Spawn enemies/boss/items in current room
        self.spawn_for_current_room()
        
    def spawn_for_current_room(self):
        """Spawn enemies, boss, or items for the current room"""
        self.enemies = []
        self.bosses = []
        current_room = self.room_manager.get_current_room()
        
        # Preserve trapdoor if it exists in this room
        saved_trapdoor = None
        if current_room.trapdoor and not current_room.trapdoor.collected:
            saved_trapdoor = current_room.trapdoor
        
        # Preserve treasure item if it exists in this room
        saved_treasure = None
        if current_room.treasure_item and not current_room.treasure_item.collected:
            saved_treasure = current_room.treasure_item
        
        self.items = []
        
        # Restore trapdoor if it exists
        if saved_trapdoor:
            self.items.append(saved_trapdoor)
        
        # Restore treasure item if it exists
        if saved_treasure:
            self.items.append(saved_treasure)
        
        # Calculate room bounds (centered on screen)
        room_offset_x = (self.screen_width - current_room.width) // 2
        room_offset_y = (self.screen_height - current_room.height) // 2
        
        # Playable area (inside walls)
        min_x = room_offset_x + current_room.wall_thickness + 50
        max_x = room_offset_x + current_room.width - current_room.wall_thickness - 50
        min_y = room_offset_y + current_room.wall_thickness + 50
        max_y = room_offset_y + current_room.height - current_room.wall_thickness - 50
        
        if current_room.has_boss and not current_room.cleared:
            # Spawn boss in center of room
            boss_x = room_offset_x + current_room.width // 2
            boss_y = room_offset_y + current_room.height // 2
            self.bosses.append(Boss(boss_x, boss_y))
        elif current_room.has_enemies and not current_room.cleared:
            # Spawn 3-5 enemies of different types
            count = random.randint(3, 5)
            enemy_types = [
                ('basic', Enemy),
                ('fast', FastEnemy),
                ('tank', TankEnemy),
                ('ranged', RangedEnemy),
                ('zigzag', ZigzagEnemy)
            ]
            
            for _ in range(count):
                # Spawn enemies in playable area only
                attempts = 0
                while attempts < 50:  # Limit attempts to avoid infinite loop
                    x = random.randint(int(min_x), int(max_x))
                    y = random.randint(int(min_y), int(max_y))
                    # Make sure enemy isn't too close to player
                    dist = math.sqrt((x - self.player.x)**2 + (y - self.player.y)**2)
                    if dist > 150:
                        # Randomly choose enemy type (weighted)
                        rand = random.random()
                        if rand < 0.3:  # 30% basic
                            enemy_class = Enemy
                        elif rand < 0.5:  # 20% fast
                            enemy_class = FastEnemy
                        elif rand < 0.7:  # 20% tank
                            enemy_class = TankEnemy
                        elif rand < 0.85:  # 15% ranged
                            enemy_class = RangedEnemy
                        else:  # 15% zigzag
                            enemy_class = ZigzagEnemy
                        
                        self.enemies.append(enemy_class(x, y))
                        break
                    attempts += 1
        elif current_room.has_items:
            # Treasure room has ONE special item in center of room
            # Check if treasure item already exists (don't spawn new one)
            if current_room.treasure_item is not None and not current_room.treasure_item.collected:
                # Item already exists, don't spawn new one
                pass
            else:
                try:
                    from item_definitions import NON_STACKABLE_ITEMS, STACKABLE_ITEMS, is_stackable
                    
                    # Get available non-stackable items (ones we haven't collected)
                    available_non_stackable = [item for item in NON_STACKABLE_ITEMS 
                                             if item not in self.collected_items]
                    
                    # Get available follower types (ones we haven't collected)
                    from follower import FOLLOWER_TYPES
                    available_followers = [i for i in range(len(FOLLOWER_TYPES)) 
                                         if i not in self.collected_follower_types]
                    
                    # Choose between stackable and non-stackable (70% chance for non-stackable)
                    if available_non_stackable and random.random() < 0.7:
                        # Spawn a non-stackable item
                        item_type = random.choice(available_non_stackable)
                    else:
                        # Spawn a stackable item
                        item_type = random.choice(STACKABLE_ITEMS)
                    
                    # Special handling for follower items
                    if item_type == 'follower' and available_followers:
                        # Follower item is valid
                        pass
                    elif item_type == 'follower' and not available_followers:
                        # No more followers available, pick a different item
                        if available_non_stackable:
                            item_type = random.choice(available_non_stackable)
                        else:
                            item_type = random.choice(STACKABLE_ITEMS)
                    
                    x = room_offset_x + current_room.width // 2
                    y = room_offset_y + current_room.height // 2
                    treasure_item = Item(x, y, item_type)
                    self.items.append(treasure_item)
                    # Store treasure item in room so it persists
                    current_room.treasure_item = treasure_item
                except Exception as e:
                    print(f"Error spawning treasure item: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback: spawn a basic item
                    x = room_offset_x + current_room.width // 2
                    y = room_offset_y + current_room.height // 2
                    treasure_item = Item(x, y, 'health')
                    self.items.append(treasure_item)
                    current_room.treasure_item = treasure_item
    
    def handle_events(self):
        """Handle keyboard and mouse input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.return_to_menu = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    self.return_to_menu = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.player.shoot(mouse_x, mouse_y, self.bullets)
        
        # Check if left mouse button is held down (continuous shooting)
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:  # Left mouse button (index 0) is held
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.player.shoot(mouse_x, mouse_y, self.bullets)
    
    def update(self):
        """Update all game objects"""
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        
        # Check for wall collision - only against actual drawn walls (gray walls)
        current_room = self.room_manager.get_current_room()
        room_offset_x = (self.screen_width - current_room.width) // 2
        room_offset_y = (self.screen_height - current_room.height) // 2
        
        # Convert player position to room coordinates
        player_room_x = self.player.x - room_offset_x
        player_room_y = self.player.y - room_offset_y
        
        wall_thickness = current_room.wall_thickness
        
        # Check collision with walls regardless of room bounds
        # Closed/locked doors act like walls
        # Top wall (gray wall)
        if room_offset_y <= self.player.y <= room_offset_y + wall_thickness + self.player.radius:
            if (room_offset_x <= self.player.x <= room_offset_x + current_room.width):
                door_passable = False
                if 'north' in current_room.doors:
                    door = current_room.doors['north']
                    # Door is passable only if it's open and not locked
                    if door.open and not door.locked:
                        if (room_offset_x + door.x <= self.player.x <= 
                            room_offset_x + door.x + door.width):
                            door_passable = True
                
                if not door_passable:
                    self.player.y = room_offset_y + wall_thickness + self.player.radius
        
        # Bottom wall
        if room_offset_y + current_room.height - wall_thickness - self.player.radius <= self.player.y <= room_offset_y + current_room.height:
            if (room_offset_x <= self.player.x <= room_offset_x + current_room.width):
                door_passable = False
                if 'south' in current_room.doors:
                    door = current_room.doors['south']
                    if door.open and not door.locked:
                        if (room_offset_x + door.x <= self.player.x <= 
                            room_offset_x + door.x + door.width):
                            door_passable = True
                
                if not door_passable:
                    self.player.y = room_offset_y + current_room.height - wall_thickness - self.player.radius
        
        # Left wall
        if room_offset_x <= self.player.x <= room_offset_x + wall_thickness + self.player.radius:
            if (room_offset_y <= self.player.y <= room_offset_y + current_room.height):
                door_passable = False
                if 'west' in current_room.doors:
                    door = current_room.doors['west']
                    if door.open and not door.locked:
                        if (room_offset_y + door.y <= self.player.y <= 
                            room_offset_y + door.y + door.height):
                            door_passable = True
                
                if not door_passable:
                    self.player.x = room_offset_x + wall_thickness + self.player.radius
        
        # Right wall
        if room_offset_x + current_room.width - wall_thickness - self.player.radius <= self.player.x <= room_offset_x + current_room.width:
            if (room_offset_y <= self.player.y <= room_offset_y + current_room.height):
                door_passable = False
                if 'east' in current_room.doors:
                    door = current_room.doors['east']
                    if door.open and not door.locked:
                        if (room_offset_y + door.y <= self.player.y <= 
                            room_offset_y + door.y + door.height):
                            door_passable = True
                
                if not door_passable:
                    self.player.x = room_offset_x + current_room.width - wall_thickness - self.player.radius
        
        # Check for room transition
        transition_pos = self.room_manager.try_transition(
            self.player.x, self.player.y, self.player.radius)
        if transition_pos:
            self.player.x, self.player.y = transition_pos
            self.bullets = []  # Clear bullets on room transition
            self.spawn_for_current_room()
        
        # Update bosses
        current_room = self.room_manager.get_current_room()
        
        for boss in self.bosses[:]:
            boss.update(self.player.x, self.player.y, self.bullets)
            
            # Check if boss hits player
            if boss.collides_with(self.player):
                old_health = self.player.health
                self.player.take_damage(2)  # Boss does more damage
                if self.player.health < old_health:
                    dx = self.player.x - boss.x
                    dy = self.player.y - boss.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        self.player.x += (dx / dist) * 40
                        self.player.y += (dy / dist) * 40
        
        # Update all followers
        for follower in self.followers:
            follower.update(self.enemies, self.bosses, self.bullets)
        
        # Update enemies
        current_room = self.room_manager.get_current_room()
        
        for enemy in self.enemies[:]:
            # Different enemies have different update signatures
            if enemy.enemy_type == 'ranged':
                enemy.update(self.player.x, self.player.y, self.bullets)
            else:
                enemy.update(self.player.x, self.player.y)
            
            # Check if enemy hits player
            if enemy.collides_with(self.player):
                # Try to take damage (will be blocked if invincible)
                old_health = self.player.health
                damage = 2 if enemy.enemy_type == 'tank' else 1
                self.player.take_damage(damage)
                # Only apply knockback if damage was actually taken
                if self.player.health < old_health:
                    # Stronger knockback for tank enemies
                    knockback = 40 if enemy.enemy_type == 'tank' else 30
                    dx = self.player.x - enemy.x
                    dy = self.player.y - enemy.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        self.player.x += (dx / dist) * knockback
                        self.player.y += (dy / dist) * knockback
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update()
            # Remove bullets that go off screen or outside room bounds
            current_room = self.room_manager.get_current_room()
            room_offset_x = (self.screen_width - current_room.width) // 2
            room_offset_y = (self.screen_height - current_room.height) // 2
            if (bullet.x < room_offset_x or bullet.x > room_offset_x + current_room.width or 
                bullet.y < room_offset_y or bullet.y > room_offset_y + current_room.height):
                self.bullets.remove(bullet)
                continue
            
            # Check bullet-boss collisions
            for boss in self.bosses[:]:
                if bullet.collides_with(boss):
                    boss.take_damage(bullet.damage)
                    if boss.health <= 0:
                        self.bosses.remove(boss)
                        # Spawn trapdoor immediately when boss dies (only if not already spawned)
                        current_room = self.room_manager.get_current_room()
                        if current_room.has_boss:
                            # Check if trapdoor already exists in room or items
                            trapdoor_exists = (current_room.trapdoor is not None and not current_room.trapdoor.collected) or \
                                            any(item.item_type == 'trapdoor' for item in self.items)
                            if not trapdoor_exists:
                                room_offset_x = (self.screen_width - current_room.width) // 2
                                room_offset_y = (self.screen_height - current_room.height) // 2
                                trapdoor_x = room_offset_x + current_room.width // 2
                                trapdoor_y = room_offset_y + current_room.height // 2
                                trapdoor = Item(trapdoor_x, trapdoor_y, 'trapdoor')
                                self.items.append(trapdoor)
                                # Store trapdoor in room so it persists
                                current_room.trapdoor = trapdoor
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break
            
            # Check bullet-enemy collisions
            if bullet in self.bullets:  # Only check if bullet still exists
                for enemy in self.enemies[:]:
                    if bullet.collides_with(enemy):
                        # Only player bullets damage enemies
                        if bullet.is_player:
                            enemy.take_damage(bullet.damage)
                            if enemy.health <= 0:
                                self.enemies.remove(enemy)
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break
            
            # Check if enemy bullets hit player
            if not bullet.is_player and bullet in self.bullets:
                if bullet.collides_with(self.player):
                    self.player.take_damage(1)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
        
        # Check item collection
        for item in self.items[:]:
            if not item.collected and item.collides_with(self.player):
                item.collected = True
                item_type = item.item_type
                
                # Check if item is non-stackable and already collected
                from item_definitions import is_non_stackable
                if is_non_stackable(item_type) and item_type in self.collected_items:
                    # Already have this non-stackable item, don't collect again
                    item.collected = False
                    continue
                
                # Remove item before applying effect (in case effect modifies items list)
                self.items.remove(item)
                # Clear treasure item reference if this was a treasure item
                current_room = self.room_manager.get_current_room()
                if current_room.treasure_item == item:
                    current_room.treasure_item = None
                
                # Track non-stackable items
                if is_non_stackable(item_type):
                    self.collected_items.add(item_type)
                
                # Apply effect after removing to avoid iteration issues
                try:
                    self.apply_item_effect(item_type)
                except Exception as e:
                    print(f"Error applying item effect {item_type}: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Check if player is dead
        if self.player.health <= 0:
            self.running = False
            self.return_to_menu = True
        
        # Check if room is cleared
        current_room = self.room_manager.get_current_room()
        enemies_cleared = len(self.enemies) == 0
        bosses_cleared = len(self.bosses) == 0
        
        if ((enemies_cleared and current_room.has_enemies) or 
            (bosses_cleared and current_room.has_boss)) and not current_room.cleared:
            self.room_manager.clear_current_room()
            
            # Trapdoor is now spawned immediately when boss dies (in bullet collision check)
            # No need to spawn it here again
    
    def apply_item_effect(self, item_type):
        """Apply the effect of a collected item"""
        if item_type == 'health':
            # Restore health
            self.player.health = min(self.player.max_health, self.player.health + 3)
        elif item_type == 'damage':
            # Increase bullet damage (we'll need to track this)
            if not hasattr(self.player, 'damage_multiplier'):
                self.player.damage_multiplier = 1.0
            self.player.damage_multiplier += 0.5
        elif item_type == 'speed':
            # Increase player speed
            self.player.speed = min(8, self.player.speed + 0.5)
        elif item_type == 'double_shot':
            # Enable double shot
            self.player.double_shot = True
        elif item_type == 'follower':
            # Spawn a random follower companion (one we don't have yet)
            from follower import FOLLOWER_TYPES
            available_followers = [i for i in range(len(FOLLOWER_TYPES)) 
                                 if i not in self.collected_follower_types]
            if available_followers:
                follower_index = random.choice(available_followers)
                self.followers.append(Follower(self.player, follower_index))
                self.collected_follower_types.add(follower_index)
        elif item_type == 'health_up':
            # Increase max health
            self.player.max_health += 2
            self.player.health = min(self.player.health + 2, self.player.max_health)
        elif item_type == 'damage_up':
            # Increase damage multiplier
            if not hasattr(self.player, 'damage_multiplier'):
                self.player.damage_multiplier = 1.0
            self.player.damage_multiplier += 0.5
        elif item_type == 'speed_up':
            # Increase speed
            self.player.speed = min(10, self.player.speed + 0.5)
        elif item_type == 'triple_shot':
            # Enable triple shot
            self.player.triple_shot = True
            self.player.double_shot = False  # Triple replaces double
        elif item_type == 'bullet_size':
            # Increase bullet size (if player has bullet_size attribute)
            if not hasattr(self.player, 'bullet_size_multiplier'):
                self.player.bullet_size_multiplier = 1.0
            self.player.bullet_size_multiplier += 0.3
        elif item_type == 'bullet_speed':
            # Increase bullet speed (if player has bullet_speed attribute)
            if not hasattr(self.player, 'bullet_speed_multiplier'):
                self.player.bullet_speed_multiplier = 1.0
            self.player.bullet_speed_multiplier += 0.2
        elif item_type == 'fire_rate':
            # Decrease shoot delay (faster shooting)
            self.player.shoot_delay = max(5, self.player.shoot_delay - 2)
        elif item_type == 'knockback':
            # Increase knockback (if player has knockback attribute)
            if not hasattr(self.player, 'knockback_multiplier'):
                self.player.knockback_multiplier = 1.0
            self.player.knockback_multiplier += 0.5
        elif item_type == 'armor':
            # Reduce damage taken (if player has armor attribute)
            if not hasattr(self.player, 'armor'):
                self.player.armor = 0
            self.player.armor += 0.1  # 10% damage reduction per armor
        elif item_type == 'regen':
            # Health regeneration (if player has regen attribute)
            if not hasattr(self.player, 'regen_rate'):
                self.player.regen_rate = 0
            self.player.regen_rate += 0.01  # Regen per frame
        elif item_type == 'lucky':
            # Better item drops (if player has luck attribute)
            if not hasattr(self.player, 'luck'):
                self.player.luck = 0
            self.player.luck += 1
        elif item_type == 'quad_shot':
            # Enable quad shot (4 bullets)
            self.player.quad_shot = True
            self.player.triple_shot = False
            self.player.double_shot = False
        elif item_type == 'piercing':
            # Bullets pierce through enemies
            if not hasattr(self.player, 'piercing'):
                self.player.piercing = 0
            self.player.piercing += 1
        elif item_type == 'explosive':
            # Bullets explode on impact
            if not hasattr(self.player, 'explosive'):
                self.player.explosive = True
        elif item_type == 'homing':
            # Bullets home in on enemies
            if not hasattr(self.player, 'homing'):
                self.player.homing = True
        elif item_type == 'chain_lightning':
            # Bullets chain to nearby enemies
            if not hasattr(self.player, 'chain_lightning'):
                self.player.chain_lightning = True
        elif item_type == 'shield':
            # Temporary shield that blocks damage
            if not hasattr(self.player, 'shield_charges'):
                self.player.shield_charges = 0
            self.player.shield_charges += 2
        elif item_type == 'teleport':
            # Can teleport (spacebar)
            if not hasattr(self.player, 'can_teleport'):
                self.player.can_teleport = True
            if not hasattr(self.player, 'teleport_cooldown'):
                self.player.teleport_cooldown = 0
        elif item_type == 'slow_time':
            # Slow down time (right click)
            if not hasattr(self.player, 'slow_time'):
                self.player.slow_time = True
        elif item_type == 'crit_chance':
            # Critical hit chance
            if not hasattr(self.player, 'crit_chance'):
                self.player.crit_chance = 0
            self.player.crit_chance += 0.1  # 10% per upgrade
        elif item_type == 'life_steal':
            # Heal when dealing damage
            if not hasattr(self.player, 'life_steal'):
                self.player.life_steal = 0
            self.player.life_steal += 0.1  # 10% of damage as healing
        elif item_type == 'bullet_bounce':
            # Bullets bounce off walls
            if not hasattr(self.player, 'bullet_bounce'):
                self.player.bullet_bounce = 0
            self.player.bullet_bounce += 1
        elif item_type == 'split_shot':
            # Bullets split on impact
            if not hasattr(self.player, 'split_shot'):
                self.player.split_shot = True
        elif item_type == 'rapid_fire':
            # Even faster fire rate
            self.player.shoot_delay = max(3, self.player.shoot_delay - 3)
        elif item_type == 'mega_bullet':
            # Much larger bullets
            if not hasattr(self.player, 'bullet_size_multiplier'):
                self.player.bullet_size_multiplier = 1.0
            self.player.bullet_size_multiplier += 0.5
        elif item_type == 'poison':
            # Bullets poison enemies
            if not hasattr(self.player, 'poison'):
                self.player.poison = True
        elif item_type == 'freeze':
            # Bullets freeze enemies
            if not hasattr(self.player, 'freeze'):
                self.player.freeze = True
        elif item_type == 'magnet':
            # Attract items from further away
            if not hasattr(self.player, 'magnet_range'):
                self.player.magnet_range = 0
            self.player.magnet_range += 50
        elif item_type == 'extra_life':
            # Extra life (revive once)
            if not hasattr(self.player, 'extra_lives'):
                self.player.extra_lives = 0
            self.player.extra_lives += 1
        elif item_type == 'damage_boost':
            # Large damage boost
            if not hasattr(self.player, 'damage_multiplier'):
                self.player.damage_multiplier = 1.0
            self.player.damage_multiplier += 1.0
        elif item_type == 'speed_boost':
            # Large speed boost
            self.player.speed = min(12, self.player.speed + 1.0)
        elif item_type == 'health_boost':
            # Large health boost
            self.player.max_health += 5
            self.player.health = min(self.player.health + 5, self.player.max_health)
        elif item_type == 'trapdoor':
            # Go to next floor (regenerate map)
            try:
                self.room_manager = RoomManager(self.screen_width, self.screen_height)
                # Reset player position to start room center
                current_room = self.room_manager.get_current_room()
                room_offset_x = (self.screen_width - current_room.width) // 2
                room_offset_y = (self.screen_height - current_room.height) // 2
                self.player.x = room_offset_x + current_room.width // 2
                self.player.y = room_offset_y + current_room.height // 2
                # Clear all game objects
                self.bullets = []
                self.enemies = []
                self.bosses = []
                self.items = []  # Clear items (including any remaining trapdoors)
                # Keep followers - they're permanent upgrades!
                # Reset player body segments for new floor
                self.player.last_positions = []
                self.player.body_segments = []
                # Spawn enemies/boss/items for new floor
                self.spawn_for_current_room()
            except Exception as e:
                print(f"Error in trapdoor effect: {e}")
                import traceback
                traceback.print_exc()
    
    def draw(self):
        """Draw everything to the screen"""
        self.screen.fill(BLACK)
        
        # Draw current room (centered)
        current_room = self.room_manager.get_current_room()
        current_room.draw(self.screen, self.screen_width, self.screen_height, self.room_manager)
        
        # Draw items
        for item in self.items:
            item.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw bosses
        for boss in self.bosses:
            boss.draw(self.screen)
        
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen)
        
        # Draw all followers
        for follower in self.followers:
            follower.draw(self.screen)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """Draw health and other UI elements"""
        # Health bar
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 10
        
        # Background
        pygame.draw.rect(self.screen, DARK_BROWN, 
                       (bar_x, bar_y, bar_width, bar_height))
        
        # Health
        health_width = int((self.player.health / self.player.max_health) * bar_width)
        pygame.draw.rect(self.screen, RED, 
                       (bar_x, bar_y, health_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, WHITE, 
                       (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Health text
        font = pygame.font.Font(None, 24)
        health_text = font.render(f"Health: {self.player.health}/{self.player.max_health}", 
                                 True, WHITE)
        self.screen.blit(health_text, (bar_x, bar_y + 25))
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        # Return to menu instead of quitting pygame
        # pygame.quit() is only called when user quits from menu

def show_menu(screen, clock):
    """Show main menu and return action"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    menu = Menu(screen_width, screen_height)
    
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
        
        action = menu.handle_events(events)
        if action:
            return action
        
        menu.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    # Initialize pygame first
    pygame.init()
    pygame.display.init()
    pygame.font.init()
    
    # Start in fullscreen
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SCREEN_WIDTH = screen.get_width()
    SCREEN_HEIGHT = screen.get_height()
    
    pygame.display.set_caption("Snaketboi - A Snake's Binding")
    clock = pygame.time.Clock()
    
    # Show menu first
    while True:
        action = show_menu(screen, clock)
        
        if action == "quit":
            pygame.quit()
            break
        elif action == "start":
            # Start the game
            game = Game(screen, clock, SCREEN_WIDTH, SCREEN_HEIGHT)
            game.run()
            
            # After game ends, show menu again
            # (or you could add a game over screen here)


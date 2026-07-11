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
from snake_customization import SnakeCustomizationMenu, SELECTED_SNAKE_VARIANT
from item_definitions import is_non_stackable
import traceback

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
    def __init__(self, screen=None, clock=None, screen_width=800, screen_height=600, testing_mode=False):
        if screen is None:
            self.screen = pygame.display.set_mode((screen_width, screen_height))
        else:
            self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        pygame.display.set_caption("Snaketboi - A Snake's Binding" + (" - Testing Mode" if testing_mode else ""))
        if clock is None:
            self.clock = pygame.time.Clock()
        else:
            self.clock = clock
        self.running = True
        self.return_to_menu = False  # Flag to return to menu instead of quitting
        self.testing_mode = testing_mode
        
        # OPTIMIZATION: Cache fonts to avoid recreating every frame
        self.font_24 = pygame.font.Font(None, 24)
        self.font_20 = pygame.font.Font(None, 20)
        self.font_48 = pygame.font.Font(None, 48)
        
        # OPTIMIZATION: Pre-cache all lizard sprites for test mode (load once, reuse)
        self._cached_lizard_sprites = {}  # palette_row -> sprite
        if testing_mode:
            self._precache_lizard_sprites()
            # OPTIMIZATION: Pre-cache snake frames for all colors to avoid processing during room load
            self._precache_snake_frames()
        
        # Game objects
        # Get selected snake variant (default to row 1 if not set)
        from snake_customization import SELECTED_SNAKE_VARIANT
        snake_variant = SELECTED_SNAKE_VARIANT  # Default is row 1
        self.player = Player(screen_width // 2, screen_height // 2, snake_variant=snake_variant)
        self.player.screen_width = screen_width
        self.player.screen_height = screen_height
        self.enemies = []
        self.bosses = []  # Separate list for bosses
        self.bullets = []
        self.items = []
        self.followers = []  # List of followers (can have multiple)
        self.collected_follower_types = set()  # Track which follower types we've collected
        self.collected_items = set()  # Track all collected non-stackable items
        
        # In test mode, use a simple static room instead of procedural generation
        if testing_mode:
            # Create a simple static room for testing (no procedural generation, no doors)
            from room import Room
            self.test_room = Room((0, 0), 'start', width=int(screen_width * 0.9), height=int(screen_height * 0.9),
                                 screen_width=screen_width, screen_height=screen_height)
            # Remove all doors from test room to reduce lag
            self.test_room.doors = {}
            self.room_manager = None  # Don't use RoomManager in test mode
            self.testing_snakes = []  # List for testing snake entities
            self.test_room_index = 0  # Track which test room we're in (0 = lizards, 1+ = snake colors)
            self.test_animation_states = ['idle', 'going_down', 'move', 'attack', 'defeated']  # Animation states to show
            # Get number of snake palette rows for room count (limit to reduce load)
            try:
                from PIL import Image
                palette_img = Image.open('snake_sprite_sheet_palette.png')
                total_colors = palette_img.size[1] // 50  # 50px per row
                self.num_snake_colors = min(6, total_colors)  # Limit to 6 colors to reduce load
            except:
                self.num_snake_colors = 6  # Default to 6 colors (reduced from 8)
            self.spawn_testing_entities()
        else:
            self.room_manager = RoomManager(screen_width, screen_height)
            self.testing_snakes = []  # List for testing snake entities
            self.test_room_index = None
            self.test_animation_states = None
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
    
    def _precache_lizard_sprites(self):
        """Pre-cache all 8 lizard color variants to avoid expensive processing during spawn"""
        # CRITICAL: Work entirely in PIL/numpy space to avoid color conversion issues
        from enemy_types import get_palette_row_colors, _load_lizard_palette_data
        from PIL import Image
        import numpy as np
        
        try:
            # Load unscaled base image
            unscaled_pil = Image.open('lizard1_palletbase.png')
            if unscaled_pil.mode != 'RGBA':
                unscaled_pil = unscaled_pil.convert('RGBA')
            
            # Load palette data
            _load_lizard_palette_data()
            from enemy_types import _lizard_row0_colors, _lizard_base_array
            
            if _lizard_row0_colors is None or _lizard_base_array is None:
                return
            
            # Get unique colors from base array (for color matching)
            mask = _lizard_base_array[:, :, 3] > 0
            rgb_array = _lizard_base_array[mask, :3]
            original_colors = set(tuple(int(c) for c in rgb) for rgb in rgb_array)
            
            # Color distance function
            def color_distance(c1, c2):
                return sum((a - b) ** 2 for a, b in zip(c1, c2))
            
            # Pre-cache all 8 color variants
            for palette_row in range(8):
                # Get palette colors for this row
                palette_colors = get_palette_row_colors(palette_row)
                if palette_colors is None:
                    continue
                
                # Build color mapping for this palette row
                color_mapping = {}
                for original_color in original_colors:
                    # Find closest match in row 0
                    best_match_idx = 0
                    best_distance = float('inf')
                    for i, row0_color in enumerate(_lizard_row0_colors):
                        dist = color_distance(original_color, row0_color)
                        if dist < best_distance:
                            best_distance = dist
                            best_match_idx = i
                    
                    # Map to same column in target palette row
                    if best_match_idx < len(palette_colors):
                        color_mapping[original_color] = palette_colors[best_match_idx]
                    else:
                        color_mapping[original_color] = palette_colors[-1] if palette_colors else original_color
                
                # Apply color mapping to unscaled PIL image (WORK IN PIL SPACE)
                # CRITICAL: Make a fresh copy for each palette row!
                base_array = np.array(unscaled_pil).copy()
                for original_color, new_color in color_mapping.items():
                    mask = (base_array[:, :, 0] == original_color[0]) & \
                           (base_array[:, :, 1] == original_color[1]) & \
                           (base_array[:, :, 2] == original_color[2]) & \
                           (base_array[:, :, 3] > 0)
                    base_array[mask, 0] = new_color[0]
                    base_array[mask, 1] = new_color[1]
                    base_array[mask, 2] = new_color[2]
                
                # Create recolored PIL image
                recolored_pil = Image.fromarray(base_array, 'RGBA')
                
                # Scale to 8x (color-before-scale preserved)
                base_size = (int(recolored_pil.size[0] * 8), int(recolored_pil.size[1] * 8))
                try:
                    scaled_pil = recolored_pil.resize(base_size, Image.Resampling.LANCZOS)
                except AttributeError:
                    scaled_pil = recolored_pil.resize(base_size, Image.LANCZOS)
                
                # Scale to test size (radius * 6 = 72)
                target_size = 12 * 6
                current_size = max(scaled_pil.size[0], scaled_pil.size[1])
                if current_size > 0 and target_size > 0:
                    scale_factor = target_size / current_size
                    test_size = (int(scaled_pil.size[0] * scale_factor), int(scaled_pil.size[1] * scale_factor))
                    try:
                        final_pil = scaled_pil.resize(test_size, Image.Resampling.LANCZOS)
                    except AttributeError:
                        final_pil = scaled_pil.resize(test_size, Image.LANCZOS)
                else:
                    final_pil = scaled_pil
                
                # Convert to pygame surface only at the very end
                data = final_pil.tobytes()
                try:
                    final_sprite = pygame.image.frombuffer(data, final_pil.size, 'RGBA')
                except:
                    final_sprite = pygame.image.fromstring(data, final_pil.size, 'RGBA')
                final_sprite = final_sprite.convert_alpha()
                
                self._cached_lizard_sprites[palette_row] = final_sprite
                
        except Exception as e:
            print(f"Error precaching lizard sprites: {e}")
            import traceback
            traceback.print_exc()
    
    def _precache_snake_frames(self):
        """Pre-cache snake animation frames for all colors to avoid expensive processing during room load"""
        from snake_animation import SnakeAnimation
        try:
            # OPTIMIZATION: Create one snake animation per color to trigger frame caching
            # This will populate the global cache, so subsequent snakes use cached frames
            for color_idx in range(self.num_snake_colors):
                # Create a dummy snake animation to trigger frame processing and caching
                # Size 15 matches test mode size, disable_flip for performance
                dummy_snake = SnakeAnimation(x=0, y=0, size=15, palette_row=color_idx, disable_flip=True)
                # The frames are now cached globally, so we can discard this dummy
                del dummy_snake
        except Exception as e:
            print(f"Error precaching snake frames: {e}")
            traceback.print_exc()
    
    def show_loading_screen(self):
        """Show loading screen while switching rooms"""
        self.screen.fill(BLACK)
        # OPTIMIZATION: Use cached font
        loading_text = self.font_48.render("Loading...", True, WHITE)
        text_rect = loading_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(loading_text, text_rect)
        pygame.display.flip()
    
    def spawn_testing_entities(self):
        """Spawn entities for current test room (one room at a time to reduce load)"""
        # STEP 1: DELOAD - Clear all entities FIRST before loading new ones
        # This ensures proper deloading and prevents memory issues
        # Clear all entity lists completely
        if self.enemies:
            self.enemies.clear()
        if self.bosses:
            self.bosses.clear()
        if self.items:
            self.items.clear()
        if self.testing_snakes:
            self.testing_snakes.clear()
        if self.bullets:
            self.bullets.clear()
        
        # Reassign to empty lists to ensure all references are cleared
        self.enemies = []
        self.bosses = []
        self.items = []
        self.testing_snakes = []
        self.bullets = []
        
        # STEP 2: Now that everything is cleared, load new entities for the current room
        
        # Use test room instead of room_manager in test mode
        current_room = self.test_room if self.testing_mode else self.room_manager.get_current_room()
        room_offset_x = (self.screen_width - current_room.width) // 2
        room_offset_y = (self.screen_height - current_room.height) // 2
        
        # Playable area (inside walls)
        min_x = room_offset_x + current_room.wall_thickness + 50
        max_x = room_offset_x + current_room.width - current_room.wall_thickness - 50
        min_y = room_offset_y + current_room.wall_thickness + 50
        max_y = room_offset_y + current_room.height - current_room.wall_thickness - 50
        
        # Room 0: Lizards only
        if self.test_room_index == 0:
            # Spawn all 8 lizard color variations (one of each variant)
            num_lizard_rows = 8  # Always show all 8 variants
            
            # Spawn lizards in a grid
            lizard_spacing = 100  # Spacing between lizards
            lizard_start_x = min_x + 100
            lizard_start_y = min_y + 100
            cols = 4  # 4 columns
            rows = (num_lizard_rows + cols - 1) // cols  # Calculate rows needed (2 rows for 8 lizards)
            
            for i in range(num_lizard_rows):
                col = i % cols
                row = i // cols
                lizard_x = lizard_start_x + col * lizard_spacing
                lizard_y = lizard_start_y + row * lizard_spacing
                
                # OPTIMIZATION: Use pre-cached sprite instead of processing on the fly
                test_lizard = Enemy(lizard_x, lizard_y, 'basic')
                palette_row = i  # Each lizard gets a different palette row (0-7)
                
                # Use cached sprite if available - use at full test size (radius * 6 = 72) for bigger display
                if palette_row in self._cached_lizard_sprites:
                    # Use cached sprite directly at test size (already scaled to radius * 6 = 72)
                    # Make a copy to avoid sharing the same surface
                    test_lizard.sprite = self._cached_lizard_sprites[palette_row].copy()
                # Fallback: manually load sprite with correct palette row at test size
                else:
                    # Create sprite with correct palette row at test size (radius * 6 = 72)
                    from enemy_types import recolor_sprite_with_palette, get_lizard_sprite_base
                    base_sprite = get_lizard_sprite_base()
                    if base_sprite:
                        recolored = recolor_sprite_with_palette(base_sprite, palette_row)
                        if recolored:
                            # Scale to test size (radius * 6 = 72)
                            target_size = test_lizard.radius * 6  # 72 pixels for test mode
                            current_size = max(recolored.get_width(), recolored.get_height())
                            if current_size > 0 and target_size > 0:
                                scale_factor = target_size / current_size
                                new_width = max(1, int(recolored.get_width() * scale_factor))
                                new_height = max(1, int(recolored.get_height() * scale_factor))
                                test_lizard.sprite = pygame.transform.scale(recolored, (new_width, new_height))
                            else:
                                test_lizard.sprite = recolored
                
                self.enemies.append(test_lizard)
        
        # Rooms 1+: One snake color per room (all animations for that color)
        elif self.test_room_index > 0 and self.test_room_index <= self.num_snake_colors:
            snake_color_index = self.test_room_index - 1  # Color index (0-based)
            
            from snake_animation import SnakeAnimation
            
            # Spawn all animation states for this snake color
            row_spacing = 100  # Reduced spacing to fit more
            start_x = min_x + 200  # Center horizontally
            start_y = min_y + 80  # Start higher
            
            for anim_idx, anim_state in enumerate(self.test_animation_states):
                anim_y = start_y + anim_idx * row_spacing
                
                # Create snake animation with the specific color (bigger in test mode, disable flip for performance)
                snake_animation = SnakeAnimation(x=start_x, y=anim_y, size=15, palette_row=snake_color_index, disable_flip=True)  # 3x bigger, no flip in test mode
                
                # Set the animation state and make sure it loops
                if anim_state == 'idle':
                    snake_animation.is_moving = False
                    snake_animation.is_attacking = False
                    snake_animation.is_going_down = False
                    snake_animation.is_defeated = False
                elif anim_state == 'going_down':
                    snake_animation.is_going_down = True
                    snake_animation.is_moving = False
                    snake_animation.is_attacking = False
                    snake_animation.is_defeated = False
                elif anim_state == 'move':
                    snake_animation.is_moving = True
                    snake_animation.is_attacking = False
                    snake_animation.is_going_down = False
                    snake_animation.is_defeated = False
                elif anim_state == 'attack':
                    snake_animation.is_attacking = True
                    snake_animation.is_moving = False
                    snake_animation.is_going_down = False
                    snake_animation.is_defeated = False
                elif anim_state == 'defeated':
                    snake_animation.is_defeated = True
                    snake_animation.is_moving = False
                    snake_animation.is_attacking = False
                    snake_animation.is_going_down = False
                
                # Simple entity wrapper
                class SnakeTestEntity:
                    def __init__(self, x, y, animation, anim_state_name):
                        self.x = x
                        self.y = y
                        self.radius = 20
                        self.snake_animation = animation
                        self.anim_state_name = anim_state_name
                
                snake_entity = SnakeTestEntity(start_x, anim_y, snake_animation, anim_state)
                self.testing_snakes.append(snake_entity)
    
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
                elif self.testing_mode:
                    # Navigation between test rooms
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        # Previous room
                        if self.test_room_index > 0:
                            self.test_room_index -= 1
                            self.show_loading_screen()
                            self.spawn_testing_entities()
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        # Next room
                        max_rooms = self.num_snake_colors  # 0 = lizards, 1+ = snake colors
                        if self.test_room_index < max_rooms:
                            self.test_room_index += 1
                            self.show_loading_screen()
                            self.spawn_testing_entities()
                    elif event.key >= pygame.K_0 and event.key <= pygame.K_9:
                        # Number keys to jump to specific room
                        room_num = event.key - pygame.K_0
                        max_rooms = self.num_snake_colors
                        if room_num <= max_rooms:
                            self.test_room_index = room_num
                            self.show_loading_screen()
                            self.spawn_testing_entities()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not self.testing_mode:  # Left click (disabled in test mode)
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.player.shoot(mouse_x, mouse_y, self.bullets)
        
        # Check if left mouse button is held down (continuous shooting) - disabled in test mode
        if not self.testing_mode:
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:  # Left mouse button (index 0) is held
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.player.shoot(mouse_x, mouse_y, self.bullets)
    
    def update(self):
        """Update all game objects"""
        # Skip player movement in test mode (only room navigation)
        if not self.testing_mode:
            keys = pygame.key.get_pressed()
            self.player.update(keys)
        
        # Skip room logic in test mode (no walls, no transitions)
        if not self.testing_mode:
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
        
        # OPTIMIZATION: Update testing snakes animation (batch update, skip if empty, skip None checks)
        if self.testing_mode and self.testing_snakes:
            for snake in self.testing_snakes:
                anim = snake.snake_animation
                if not anim:
                    continue
                # OPTIMIZATION: Only update position if changed
                if anim.x != snake.x:
                    anim.x = snake.x
                if anim.y != snake.y:
                    anim.y = snake.y
                # OPTIMIZATION: Only check animation state if needed
                state_name = snake.anim_state_name
                if state_name == 'attack' and not anim.is_attacking:
                    anim.start_attack()
                elif state_name == 'going_down' and not anim.is_going_down:
                    anim.start_going_down()
                # Only update animation - states are set once during spawn
                anim.update_animation()
        
        # OPTIMIZATION: Update bosses (skip AI in testing mode, skip if empty)
        if not self.testing_mode and self.bosses:
            # OPTIMIZATION: Cache player position
            player_x, player_y = self.player.x, self.player.y
            for boss in self.bosses:
                boss.update(player_x, player_y, self.bullets)
                
                # Check if boss hits player
                if boss.collides_with(self.player):
                    old_health = self.player.health
                    self.player.take_damage(2)  # Boss does more damage
                    if self.player.health < old_health:
                        dx = player_x - boss.x
                        dy = player_y - boss.y
                        dist_sq = dx*dx + dy*dy
                        if dist_sq > 0:
                            # OPTIMIZATION: Avoid sqrt by using inverse distance squared
                            inv_dist = 40.0 / math.sqrt(dist_sq)
                            self.player.x += dx * inv_dist
                            self.player.y += dy * inv_dist
                        # Update cached position
                        player_x, player_y = self.player.x, self.player.y
        
        # OPTIMIZATION: Update followers (skip if empty)
        if self.followers:
            for follower in self.followers:
                follower.update(self.enemies, self.bosses, self.bullets)
        
        # OPTIMIZATION: Update enemies (skip AI in testing mode, skip if empty, cache player pos)
        if not self.testing_mode and self.enemies:
            # OPTIMIZATION: Cache player position
            player_x, player_y = self.player.x, self.player.y
            for enemy in self.enemies:
                # Different enemies have different update signatures
                if enemy.enemy_type == 'ranged':
                    enemy.update(player_x, player_y, self.bullets)
                else:
                    enemy.update(player_x, player_y)
                
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
                        dist_sq = dx*dx + dy*dy
                        if dist_sq > 0:
                            # OPTIMIZATION: Avoid sqrt by using inverse distance
                            inv_dist = knockback / math.sqrt(dist_sq)
                            self.player.x += dx * inv_dist
                            self.player.y += dy * inv_dist
        
        # OPTIMIZATION: Update bullets (skip if empty, cache room calculations)
        if self.bullets:
            # OPTIMIZATION: Cache room calculations
            if self.testing_mode:
                current_room = self.test_room
            else:
                current_room = self.room_manager.get_current_room()
            room_offset_x = (self.screen_width - current_room.width) // 2
            room_offset_y = (self.screen_height - current_room.height) // 2
            room_max_x = room_offset_x + current_room.width
            room_max_y = room_offset_y + current_room.height
            
            # OPTIMIZATION: Iterate backwards to safely remove items
            i = len(self.bullets) - 1
            while i >= 0:
                bullet = self.bullets[i]
                bullet.update()
                # Remove bullets that go off screen or outside room bounds
                if (bullet.x < room_offset_x or bullet.x > room_max_x or 
                    bullet.y < room_offset_y or bullet.y > room_max_y):
                    self.bullets.pop(i)
                    i -= 1
                    continue
                
                # OPTIMIZATION: Check bullet-boss collisions (skip if no bosses)
                bullet_removed = False
                if self.bosses:
                    for boss in self.bosses:
                        if bullet.collides_with(boss):
                            boss.take_damage(bullet.damage)
                            if boss.health <= 0:
                                self.bosses.remove(boss)
                                # Spawn trapdoor immediately when boss dies (only if not already spawned)
                                if not self.testing_mode:
                                    current_room = self.room_manager.get_current_room()
                                    if current_room.has_boss:
                                        # OPTIMIZATION: Cache room offsets
                                        room_offset_x = (self.screen_width - current_room.width) // 2
                                        room_offset_y = (self.screen_height - current_room.height) // 2
                                        # Check if trapdoor already exists in room or items
                                        trapdoor_exists = (current_room.trapdoor is not None and not current_room.trapdoor.collected) or \
                                                        any(item.item_type == 'trapdoor' for item in self.items)
                                        if not trapdoor_exists:
                                            trapdoor_x = room_offset_x + current_room.width // 2
                                            trapdoor_y = room_offset_y + current_room.height // 2
                                            trapdoor = Item(trapdoor_x, trapdoor_y, 'trapdoor')
                                            self.items.append(trapdoor)
                                            # Store trapdoor in room so it persists
                                            current_room.trapdoor = trapdoor
                            # OPTIMIZATION: Remove bullet and break
                            self.bullets.pop(i)
                            bullet_removed = True
                            break
                
                if bullet_removed:
                    i -= 1
                    continue
                
                # OPTIMIZATION: Check bullet-enemy collisions (skip if no enemies)
                if self.enemies:
                    for enemy in self.enemies:
                        if bullet.collides_with(enemy):
                            # Only player bullets damage enemies
                            if bullet.is_player:
                                enemy.take_damage(bullet.damage)
                                if enemy.health <= 0:
                                    self.enemies.remove(enemy)
                            # OPTIMIZATION: Remove bullet and break
                            self.bullets.pop(i)
                            bullet_removed = True
                            break
                
                if bullet_removed:
                    i -= 1
                    continue
                
                # OPTIMIZATION: Check if enemy bullets hit player
                if not bullet.is_player and bullet.collides_with(self.player):
                    self.player.take_damage(1)
                    # OPTIMIZATION: Remove bullet
                    self.bullets.pop(i)
                    i -= 1
                    continue
                
                i -= 1
        
        # OPTIMIZATION: Check item collection (skip if empty, skip in test mode)
        if not self.testing_mode and self.items:
            for item in self.items:
                if not item.collected and item.collides_with(self.player):
                    item.collected = True
                    item_type = item.item_type
                    
                    # Check if item is non-stackable and already collected
                    is_non_stack = is_non_stackable(item_type)
                    if is_non_stack and item_type in self.collected_items:
                        # Already have this non-stackable item, don't collect again
                        item.collected = False
                        continue
                    
                    # Remove item before applying effect (in case effect modifies items list)
                    self.items.remove(item)
                    # Clear treasure item reference if this was a treasure item
                    current_room = self.room_manager.get_current_room()
                    if current_room.treasure_item == item:
                        current_room.treasure_item = None
                    
                    # Track non-stackable items (reuse check result)
                    if is_non_stack:
                        self.collected_items.add(item_type)
                    
                    # Apply effect after removing to avoid iteration issues
                    try:
                        self.apply_item_effect(item_type)
                    except Exception as e:
                        print(f"Error applying item effect {item_type}: {e}")
                        traceback.print_exc()
        
        # Check if player is dead
        if self.player.health <= 0:
            self.running = False
            self.return_to_menu = True
        
        # OPTIMIZATION: Check if room is cleared (skip in test mode, avoid redundant checks)
        if not self.testing_mode:
            current_room = self.room_manager.get_current_room()
            # OPTIMIZATION: Only check if room has enemies/boss and they're cleared
            if not current_room.cleared:
                if current_room.has_enemies and not self.enemies:
                    self.room_manager.clear_current_room()
                elif current_room.has_boss and not self.bosses:
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
                traceback.print_exc()
    
    def draw(self):
        """Draw everything to the screen"""
        self.screen.fill(BLACK)
        
        # OPTIMIZATION: Draw current room (avoid unnecessary variable assignment)
        if self.testing_mode:
            self.test_room.draw(self.screen, self.screen_width, self.screen_height, None)
        else:
            self.room_manager.get_current_room().draw(self.screen, self.screen_width, self.screen_height, self.room_manager)
        
        # OPTIMIZATION: Draw items (skip if empty)
        if self.items:
            for item in self.items:
                item.draw(self.screen)
        
        # OPTIMIZATION: Draw enemies (skip if empty)
        if self.enemies:
            for enemy in self.enemies:
                enemy.draw(self.screen)
        
        # OPTIMIZATION: Draw testing snakes (skip None checks, position already updated)
        if self.testing_mode and self.testing_snakes:
            for snake in self.testing_snakes:
                anim = snake.snake_animation
                if anim:
                    # Draw the snake (position and animation already updated in update loop)
                    anim.draw(self.screen, grid_cell_size=32, offset_y_adjust=-25)
        
        # OPTIMIZATION: Draw bosses (skip in test mode, skip if empty)
        if not self.testing_mode and self.bosses:
            for boss in self.bosses:
                boss.draw(self.screen)
        
        # OPTIMIZATION: Draw bullets (skip if empty)
        if self.bullets:
            for bullet in self.bullets:
                bullet.draw(self.screen)
        
        # OPTIMIZATION: Draw followers (skip if empty)
        if self.followers:
            for follower in self.followers:
                follower.draw(self.screen)
        
        # Draw player (skip in test mode)
        if not self.testing_mode:
            self.player.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """Draw health and other UI elements"""
        # Skip health display in testing mode
        if not self.testing_mode:
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
            
            # Health text (OPTIMIZATION: Use cached font)
            health_text = self.font_24.render(f"Health: {self.player.health}/{self.player.max_health}", 
                                             True, WHITE)
            self.screen.blit(health_text, (bar_x, bar_y + 25))
        
        # Test mode room indicator
        if self.testing_mode:
            # OPTIMIZATION: Use cached font
            if self.test_room_index == 0:
                room_name = 'Lizards'
            else:
                room_name = f'Snake Color {self.test_room_index - 1}'
            max_rooms = self.num_snake_colors
            # OPTIMIZATION: Use cached font
            room_text = self.font_20.render(f"Test Room: {room_name} ({self.test_room_index}/{max_rooms})", 
                                           True, WHITE)
            self.screen.blit(room_text, (10, 10))
            
            # Navigation hint
            nav_text = self.font_20.render(f"Left/Right or A/D: Navigate | 0-{max_rooms}: Jump to room", 
                                          True, (200, 200, 200))
            self.screen.blit(nav_text, (10, 30))
    
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

# OPTIMIZATION: Cache credits text surfaces (module-level cache)
_credits_text_cache = None

def _get_credits_text_cache(screen_width, screen_height):
    """Get or create cached credits text surfaces"""
    global _credits_text_cache
    if _credits_text_cache is None:
        # Fonts
        font_title = pygame.font.Font(None, 72)
        font_large = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 28)
        
        cache = {
            'fonts': {'title': font_title, 'large': font_large, 'medium': font_medium, 'small': font_small},
            'texts': {}
        }
        
        # Pre-render all text surfaces
        cache['texts']['title'] = font_title.render("CREDITS", True, (0, 255, 0))
        cache['texts']['coding_label'] = font_medium.render("Coded by", True, (150, 150, 150))
        cache['texts']['coder'] = font_large.render("HiddenHognose", True, (0, 255, 0))
        cache['texts']['snake_sprite_label'] = font_medium.render("Snake sprite by", True, (150, 150, 150))
        cache['texts']['snake_sprite'] = font_large.render("Calciumtrice", True, (0, 255, 0))
        cache['texts']['recoloring_label'] = font_medium.render("Sprite recoloring by", True, (150, 150, 150))
        cache['texts']['recoloring'] = font_large.render("HiddenHognose", True, (0, 255, 0))
        cache['texts']['lizard_sprite_label'] = font_medium.render("Lizard sprite by", True, (150, 150, 150))
        cache['texts']['lizard_sprite'] = font_large.render("HiddenHognose", True, (0, 255, 0))
        cache['texts']['name'] = font_large.render("Ed and Emily from Snake Discovery", True, (0, 255, 0))
        cache['texts']['attribution'] = font_medium.render("for helping my passion for snakes thrive", True, (200, 200, 200))
        cache['texts']['inspiration_label'] = font_medium.render("Inspired by", True, (150, 150, 150))
        cache['texts']['isaac'] = font_large.render("The Binding of Isaac", True, (0, 255, 0))
        cache['texts']['libraries_label'] = font_medium.render("Built with", True, (150, 150, 150))
        cache['texts']['pygame'] = font_medium.render("pygame", True, (0, 255, 0))
        cache['texts']['pillow'] = font_medium.render("PIL/Pillow", True, (0, 255, 0))
        cache['texts']['numpy'] = font_medium.render("numpy", True, (0, 255, 0))
        cache['texts']['instructions'] = font_small.render("Press ESC, ENTER, or SPACE to return to menu", True, (150, 150, 150))
        
        _credits_text_cache = cache
    return _credits_text_cache

def show_credits(screen, clock):
    """Show credits screen - OPTIMIZED with cached text"""
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # OPTIMIZATION: Use cached text surfaces
    cache = _get_credits_text_cache(screen_width, screen_height)
    texts = cache['texts']
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return "menu"
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # OPTIMIZATION: Use cached text surfaces
        # Title
        title_rect = texts['title'].get_rect(center=(screen_width // 2, 80))
        screen.blit(texts['title'], title_rect)
        
        # Credits content
        y_offset = 130
        line_spacing = 40
        section_spacing = 60
        
        current_y = y_offset
        
        # Coding section
        coding_rect = texts['coding_label'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['coding_label'], coding_rect)
        
        current_y += line_spacing
        coder_rect = texts['coder'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['coder'], coder_rect)
        
        current_y += section_spacing
        
        # Snake sprite section
        snake_sprite_rect = texts['snake_sprite_label'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['snake_sprite_label'], snake_sprite_rect)
        
        current_y += line_spacing
        snake_sprite_creator_rect = texts['snake_sprite'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['snake_sprite'], snake_sprite_creator_rect)
        
        current_y += section_spacing
        
        # Sprite recoloring section
        recoloring_rect = texts['recoloring_label'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['recoloring_label'], recoloring_rect)
        
        current_y += line_spacing
        recoloring_creator_rect = texts['recoloring'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['recoloring'], recoloring_creator_rect)
        
        current_y += section_spacing
        
        # Lizard sprite section
        lizard_sprite_rect = texts['lizard_sprite_label'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['lizard_sprite_label'], lizard_sprite_rect)
        
        current_y += line_spacing
        lizard_sprite_creator_rect = texts['lizard_sprite'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['lizard_sprite'], lizard_sprite_creator_rect)
        
        current_y += section_spacing
        
        # Ed and Emily from Snake Discovery
        name_rect = texts['name'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['name'], name_rect)
        
        attribution_rect = texts['attribution'].get_rect(center=(screen_width // 2, current_y + line_spacing))
        screen.blit(texts['attribution'], attribution_rect)
        
        current_y += section_spacing + 10
        
        # Inspiration
        inspiration_rect = texts['inspiration_label'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['inspiration_label'], inspiration_rect)
        
        current_y += line_spacing
        isaac_rect = texts['isaac'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['isaac'], isaac_rect)
        
        current_y += section_spacing
        
        # Libraries section
        libraries_rect = texts['libraries_label'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['libraries_label'], libraries_rect)
        
        current_y += line_spacing
        pygame_rect = texts['pygame'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['pygame'], pygame_rect)
        
        current_y += line_spacing - 10
        pillow_rect = texts['pillow'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['pillow'], pillow_rect)
        
        current_y += line_spacing - 10
        numpy_rect = texts['numpy'].get_rect(center=(screen_width // 2, current_y))
        screen.blit(texts['numpy'], numpy_rect)
        
        # Instructions to go back
        inst_y = screen_height - 60
        inst_rect = texts['instructions'].get_rect(center=(screen_width // 2, inst_y))
        screen.blit(texts['instructions'], inst_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return "menu"

if __name__ == "__main__":
    # Initialize pygame first
    pygame.init()
    pygame.display.init()
    pygame.font.init()
    
    # Start in windowed mode (for screenshots)
    SCREEN_WIDTH = 1600
    SCREEN_HEIGHT = 900
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
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
            game = Game(screen, clock, SCREEN_WIDTH, SCREEN_HEIGHT, testing_mode=False)
            game.run()
            
            # After game ends, show menu again
            # (or you could add a game over screen here)
        elif action == "testing":
            # Start testing mode
            game = Game(screen, clock, SCREEN_WIDTH, SCREEN_HEIGHT, testing_mode=True)
            game.run()
            
            # After testing ends, show menu again
        elif action == "customize":
            # Show snake customization menu
            customization_menu = SnakeCustomizationMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
            while True:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                
                customize_action = customization_menu.handle_events(events)
                if customize_action == "back" or customize_action == "confirm":
                    # Return to main menu
                    break
                
                customization_menu.draw(screen)
                pygame.display.flip()
                clock.tick(FPS)
        elif action == "credits":
            # Show credits screen
            credits_action = show_credits(screen, clock)
            if credits_action == "quit":
                pygame.quit()
                break
            # Otherwise return to menu (loop continues)


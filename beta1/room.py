import pygame
import random

class Door:
    def __init__(self, direction, x, y, width, height):
        self.direction = direction  # 'north', 'south', 'east', 'west'
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.locked = True
        self.open = False
    
    def collides_with(self, x, y, radius):
        """Check if player is colliding with door"""
        # Check if player center is within door bounds
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def draw(self, screen):
        """Draw the door"""
        if self.locked:
            # Locked door - dark brown
            pygame.draw.rect(screen, (60, 30, 10), 
                           (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (100, 50, 20), 
                           (self.x, self.y, self.width, self.height), 2)
        elif self.open:
            # Open door - lighter (passable)
            pygame.draw.rect(screen, (40, 40, 40), 
                           (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (100, 100, 100), 
                           (self.x, self.y, self.width, self.height), 2)
        else:
            # Closed but unlocked
            pygame.draw.rect(screen, (80, 40, 20), 
                           (self.x, self.y, self.width, self.height))

class Room:
    def __init__(self, room_id, room_type='normal', width=None, height=None, screen_width=800, screen_height=600):
        self.room_id = room_id
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Random room sizes (but ensure they fit on screen with margins)
        max_width = int(screen_width * 0.9)  # Max 90% of screen width
        max_height = int(screen_height * 0.9)  # Max 90% of screen height
        min_width = int(screen_width * 0.5)   # Min 50% of screen width
        min_height = int(screen_height * 0.5) # Min 50% of screen height
        
        if width is None:
            self.width = random.randint(min_width, max_width)
        else:
            self.width = min(width, max_width)  # Cap at max
        if height is None:
            self.height = random.randint(min_height, max_height)
        else:
            self.height = min(height, max_height)  # Cap at max
        self.wall_thickness = 20
        self.room_type = room_type  # 'normal', 'boss', 'treasure', 'start'
        
        # Set room properties based on type
        if room_type == 'boss':
            self.floor_color = (60, 20, 20)  # Dark red
            self.wall_color = (100, 40, 40)
            self.has_enemies = True
            self.has_boss = True
            self.has_items = False
        elif room_type == 'treasure':
            self.floor_color = (40, 40, 60)  # Dark blue/purple
            self.wall_color = (60, 60, 100)
            self.has_enemies = False
            self.has_boss = False
            self.has_items = True
        elif room_type == 'start':
            self.floor_color = (50, 50, 50)
            self.wall_color = (80, 80, 80)
            self.has_enemies = False
            self.has_boss = False
            self.has_items = False
        else:  # normal
            self.floor_color = (50, 50, 50)
            self.wall_color = (80, 80, 80)
            self.has_enemies = True
            self.has_boss = False
            self.has_items = False
        
        self.cleared = False
        self.trapdoor = None  # Store trapdoor item for this room
        self.treasure_item = None  # Store treasure item for this room
        
        # Door dimensions
        door_width = 60
        door_height = 20
        
        # Create doors (north, south, east, west)
        self.doors = {}
        
        # Boss rooms only have ONE door (the entrance)
        if room_type == 'boss':
            # Boss room only has one door - find which direction connects to another room
            # This will be set later in RoomManager after rooms are connected
            # For now, create all doors but we'll remove extras later
            self.doors['north'] = Door('north', 
                                      self.width // 2 - door_width // 2, 
                                      0, 
                                      door_width, 
                                      door_height)
            self.doors['south'] = Door('south', 
                                      self.width // 2 - door_width // 2, 
                                      self.height - door_height, 
                                      door_width, 
                                      door_height)
            self.doors['east'] = Door('east', 
                                     self.width - door_height, 
                                     self.height // 2 - door_width // 2, 
                                     door_height, 
                                     door_width)
            self.doors['west'] = Door('west', 
                                     0, 
                                     self.height // 2 - door_width // 2, 
                                     door_height, 
                                     door_width)
        else:
            # Normal rooms have all doors
            self.doors['north'] = Door('north', 
                                      self.width // 2 - door_width // 2, 
                                      0, 
                                      door_width, 
                                      door_height)
            self.doors['south'] = Door('south', 
                                      self.width // 2 - door_width // 2, 
                                      self.height - door_height, 
                                      door_width, 
                                      door_height)
            self.doors['east'] = Door('east', 
                                     self.width - door_height, 
                                     self.height // 2 - door_width // 2, 
                                     door_height, 
                                     door_width)
            self.doors['west'] = Door('west', 
                                     0, 
                                     self.height // 2 - door_width // 2, 
                                     door_height, 
                                     door_width)
        
        # Initially lock all doors if room has enemies or boss
        if self.has_enemies or self.has_boss:
            for door in self.doors.values():
                door.locked = True
                door.open = False
        else:
            # Empty/treasure rooms have open doors
            for door in self.doors.values():
                door.locked = False
                door.open = True
    
    def unlock_doors(self):
        """Unlock all doors (called when enemies/boss are cleared)"""
        self.cleared = True
        for door in self.doors.values():
            door.locked = False
            door.open = True
    
    def get_door_at(self, x, y, player_radius, screen_width, screen_height):
        """Get the door the player is colliding with, if any"""
        # Calculate room offset (centered)
        offset_x = (screen_width - self.width) // 2
        offset_y = (screen_height - self.height) // 2
        
        # Adjust player position relative to room
        room_x = x - offset_x
        room_y = y - offset_y
        
        for door in self.doors.values():
            # Temporarily adjust door position for collision check
            old_x, old_y = door.x, door.y
            door.x += offset_x
            door.y += offset_y
            if door.collides_with(x, y, player_radius) and door.open:
                door.x, door.y = old_x, old_y
                return door
            door.x, door.y = old_x, old_y
        return None
    
    def draw(self, screen, screen_width, screen_height, room_manager=None):
        """Draw the room (floor, walls, and doors) - centered on screen"""
        # Calculate offset to center room on screen
        offset_x = (screen_width - self.width) // 2
        offset_y = (screen_height - self.height) // 2
        
        # Draw floor (centered)
        pygame.draw.rect(screen, self.floor_color, 
                        (offset_x + self.wall_thickness, 
                         offset_y + self.wall_thickness,
                         self.width - 2*self.wall_thickness,
                         self.height - 2*self.wall_thickness))
        
        # Draw walls (but leave space for doors)
        wall_color = (100, 100, 100) if self.cleared else self.wall_color
        
        # Top wall (with door gap if door exists)
        if 'north' in self.doors:
            door = self.doors['north']
            pygame.draw.rect(screen, wall_color, 
                           (offset_x, offset_y, door.x, self.wall_thickness))
            pygame.draw.rect(screen, wall_color, 
                            (offset_x + door.x + door.width, offset_y, 
                             self.width - (door.x + door.width), self.wall_thickness))
        else:
            pygame.draw.rect(screen, wall_color, 
                           (offset_x, offset_y, self.width, self.wall_thickness))
        
        # Bottom wall (with door gap if door exists)
        if 'south' in self.doors:
            door = self.doors['south']
            pygame.draw.rect(screen, wall_color, 
                            (offset_x, offset_y + self.height - self.wall_thickness, 
                             door.x, self.wall_thickness))
            pygame.draw.rect(screen, wall_color, 
                            (offset_x + door.x + door.width, 
                             offset_y + self.height - self.wall_thickness, 
                             self.width - (door.x + door.width), self.wall_thickness))
        else:
            pygame.draw.rect(screen, wall_color, 
                           (offset_x, offset_y + self.height - self.wall_thickness, 
                            self.width, self.wall_thickness))
        
        # Left wall (with door gap if door exists)
        if 'west' in self.doors:
            door = self.doors['west']
            pygame.draw.rect(screen, wall_color, 
                           (offset_x, offset_y, self.wall_thickness, door.y))
            pygame.draw.rect(screen, wall_color, 
                            (offset_x, offset_y + door.y + door.height, 
                             self.wall_thickness, 
                             self.height - (door.y + door.height)))
        else:
            pygame.draw.rect(screen, wall_color, 
                           (offset_x, offset_y, self.wall_thickness, self.height))
        
        # Right wall (with door gap if door exists)
        if 'east' in self.doors:
            door = self.doors['east']
            pygame.draw.rect(screen, wall_color, 
                            (offset_x + self.width - self.wall_thickness, offset_y, 
                             self.wall_thickness, door.y))
            pygame.draw.rect(screen, wall_color, 
                            (offset_x + self.width - self.wall_thickness, 
                             offset_y + door.y + door.height, 
                             self.wall_thickness, 
                             self.height - (door.y + door.height)))
        else:
            pygame.draw.rect(screen, wall_color, 
                           (offset_x + self.width - self.wall_thickness, offset_y, 
                            self.wall_thickness, self.height))
        
        # Draw doors (with offset)
        for door in self.doors.values():
            # Temporarily adjust door position for drawing
            old_x, old_y = door.x, door.y
            door.x += offset_x
            door.y += offset_y
            
            # Draw colored walls on either side of door based on CONNECTED room type
            # Check what room this door connects to
            door_wall_color = None
            if room_manager:
                x, y = self.room_id
                connected_room_id = None
                if door.direction == 'north':
                    connected_room_id = (x, y - 1)
                elif door.direction == 'south':
                    connected_room_id = (x, y + 1)
                elif door.direction == 'east':
                    connected_room_id = (x + 1, y)
                elif door.direction == 'west':
                    connected_room_id = (x - 1, y)
                
                # Check if connected room exists and what type it is
                if connected_room_id and connected_room_id in room_manager.room_grid:
                    connected_room = room_manager.room_grid[connected_room_id]
                    if connected_room.room_type == 'boss':
                        # Red walls on either side of door leading to boss room
                        door_wall_color = (150, 0, 0)  # Dark red
                    elif connected_room.room_type == 'treasure':
                        # Yellow walls on either side of door leading to treasure room
                        door_wall_color = (150, 150, 0)  # Dark yellow
            
            # Draw colored walls if we found a special room
            if door_wall_color:
                if door.direction == 'north' or door.direction == 'south':
                    # Horizontal door - draw walls on left and right
                    pygame.draw.rect(screen, door_wall_color,
                                   (door.x - self.wall_thickness, door.y,
                                    self.wall_thickness, door.height))
                    pygame.draw.rect(screen, door_wall_color,
                                   (door.x + door.width, door.y,
                                    self.wall_thickness, door.height))
                else:  # east or west
                    # Vertical door - draw walls on top and bottom
                    pygame.draw.rect(screen, door_wall_color,
                                   (door.x, door.y - self.wall_thickness,
                                    door.width, self.wall_thickness))
                    pygame.draw.rect(screen, door_wall_color,
                                   (door.x, door.y + door.height,
                                    door.width, self.wall_thickness))
            
            door.draw(screen)
            door.x, door.y = old_x, old_y

class RoomManager:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rooms = {}
        self.current_room_id = (0, 0)  # Grid coordinates
        self.room_grid = {}  # Maps (x, y) -> Room
        
        # Create procedurally generated map
        self.generate_rooms()
        
        # Get current room
        self.current_room = self.room_grid[self.current_room_id]
    
    def get_playable_area(self):
        """Get the playable area bounds for the current room"""
        room = self.current_room
        return {
            'min_x': self.wall_thickness,
            'max_x': room.width - self.wall_thickness,
            'min_y': self.wall_thickness,
            'max_y': room.height - self.wall_thickness
        }
    
    def generate_rooms(self):
        """Procedurally generate a connected map of rooms"""
        # Use a simple algorithm: start from (0,0) and branch out
        visited = set()
        to_visit = [(0, 0)]
        
        # Track special rooms
        boss_room_created = False
        treasure_room_created = False
        
        # Always start with a start room (standard size for start, but not full screen)
        start_width = int(self.screen_width * 0.7)
        start_height = int(self.screen_height * 0.7)
        start_room = Room((0, 0), 'start', width=start_width, height=start_height,
                         screen_width=self.screen_width, screen_height=self.screen_height)
        self.room_grid[(0, 0)] = start_room
        visited.add((0, 0))
        
        # Generate rooms in a branching pattern
        max_rooms = random.randint(8, 12)
        room_count = 1
        
        while to_visit and room_count < max_rooms:
            current = to_visit.pop(0)
            x, y = current
            
            # Try to add adjacent rooms
            directions = [('north', 0, -1), ('south', 0, 1), 
                         ('east', 1, 0), ('west', -1, 0)]
            random.shuffle(directions)
            
            for direction, dx, dy in directions:
                new_pos = (x + dx, y + dy)
                
                # 60% chance to create a new room from this position
                if new_pos not in visited and random.random() < 0.6 and room_count < max_rooms:
                    # Decide room type
                    # GUARANTEE at least one boss room and one treasure room
                    # Force create boss room if we're near the end and haven't created one
                    if not boss_room_created and (room_count >= max_rooms - 2 or 
                                                   (not treasure_room_created and room_count >= max_rooms - 3)):
                        # Create boss room (guaranteed)
                        room_type = 'boss'
                        boss_room_created = True
                    elif not treasure_room_created and (room_count >= max_rooms - 2 or 
                                                         (not boss_room_created and room_count >= max_rooms - 3)):
                        # Create treasure room (guaranteed)
                        room_type = 'treasure'
                        treasure_room_created = True
                    elif not boss_room_created and random.random() < 0.25:
                        # Create boss room
                        room_type = 'boss'
                        boss_room_created = True
                    elif not treasure_room_created and random.random() < 0.2:
                        # Create treasure room
                        room_type = 'treasure'
                        treasure_room_created = True
                    else:
                        # Normal room
                        room_type = 'normal'
                    
                    # Create room with random size (ensured to fit on screen)
                    new_room = Room(new_pos, room_type, 
                                   screen_width=self.screen_width, 
                                   screen_height=self.screen_height)
                    self.room_grid[new_pos] = new_room
                    visited.add(new_pos)
                    to_visit.append(new_pos)
                    room_count += 1
        
        # GUARANTEE at least one boss and one treasure room
        # If we didn't create them during generation, force create them
        if not boss_room_created:
            # Find a room to convert to boss room (prefer rooms far from start)
            candidates = [pos for pos, room in self.room_grid.items() 
                          if room.room_type == 'normal']
            if candidates:
                # Convert the farthest normal room to boss room
                import math
                farthest = max(candidates, key=lambda pos: math.sqrt(pos[0]**2 + pos[1]**2))
                self.room_grid[farthest].room_type = 'boss'
                self.room_grid[farthest].has_boss = True
                self.room_grid[farthest].has_enemies = True
                self.room_grid[farthest].floor_color = (60, 20, 20)
                self.room_grid[farthest].wall_color = (100, 40, 40)
        
        if not treasure_room_created:
            # Find a room to convert to treasure room
            candidates = [pos for pos, room in self.room_grid.items() 
                          if room.room_type == 'normal']
            if candidates:
                # Convert a normal room to treasure room
                import math
                farthest = max(candidates, key=lambda pos: math.sqrt(pos[0]**2 + pos[1]**2))
                if self.room_grid[farthest].room_type != 'boss':  # Don't convert if it's already boss
                    self.room_grid[farthest].room_type = 'treasure'
                    self.room_grid[farthest].has_items = True
                    self.room_grid[farthest].has_enemies = False
                    self.room_grid[farthest].has_boss = False
                    self.room_grid[farthest].floor_color = (40, 40, 60)
                    self.room_grid[farthest].wall_color = (60, 60, 100)
        
        # Connect rooms (set which doors exist)
        for (x, y), room in self.room_grid.items():
            # Boss rooms: keep only ONE door (the entrance)
            if room.room_type == 'boss':
                # Find which direction has a connecting room (the entrance)
                entrance_direction = None
                if (x, y - 1) in self.room_grid:
                    entrance_direction = 'north'
                elif (x, y + 1) in self.room_grid:
                    entrance_direction = 'south'
                elif (x + 1, y) in self.room_grid:
                    entrance_direction = 'east'
                elif (x - 1, y) in self.room_grid:
                    entrance_direction = 'west'
                
                # Remove all doors except the entrance
                doors_to_remove = []
                for door_dir in list(room.doors.keys()):
                    if door_dir != entrance_direction:
                        doors_to_remove.append(door_dir)
                for door_dir in doors_to_remove:
                    del room.doors[door_dir]
            else:
                # Normal rooms: remove doors that lead to non-existent rooms
                if (x, y - 1) not in self.room_grid:
                    if 'north' in room.doors:
                        del room.doors['north']
                if (x, y + 1) not in self.room_grid:
                    if 'south' in room.doors:
                        del room.doors['south']
                if (x + 1, y) not in self.room_grid:
                    if 'east' in room.doors:
                        del room.doors['east']
                if (x - 1, y) not in self.room_grid:
                    if 'west' in room.doors:
                        del room.doors['west']
    
    def get_current_room(self):
        """Get the current room"""
        return self.current_room
    
    def try_transition(self, player_x, player_y, player_radius):
        """Try to transition to a new room if player is at a door"""
        door = self.current_room.get_door_at(player_x, player_y, player_radius,
                                            self.screen_width, self.screen_height)
        if door is None:
            return None
        
        # Calculate new room position
        x, y = self.current_room_id
        new_room_id = None
        new_room_relative_x = 0
        new_room_relative_y = 0
        
        if door.direction == 'north':
            new_room_id = (x, y - 1)
            new_room_relative_x = 0.5  # Center of room width
            new_room_relative_y = 0.85  # Near bottom of room
        elif door.direction == 'south':
            new_room_id = (x, y + 1)
            new_room_relative_x = 0.5  # Center of room width
            new_room_relative_y = 0.15  # Near top of room
        elif door.direction == 'east':
            new_room_id = (x + 1, y)
            new_room_relative_x = 0.15  # Near left of room
            new_room_relative_y = 0.5  # Center of room height
        elif door.direction == 'west':
            new_room_id = (x - 1, y)
            new_room_relative_x = 0.85  # Near right of room
            new_room_relative_y = 0.5  # Center of room height
        else:
            return None
        
        # Check if new room exists
        if new_room_id in self.room_grid:
            new_room = self.room_grid[new_room_id]
            self.current_room_id = new_room_id
            self.current_room = new_room
            
            # Calculate player position in new room (relative to room, then convert to screen coords)
            new_room_offset_x = (self.screen_width - new_room.width) // 2
            new_room_offset_y = (self.screen_height - new_room.height) // 2
            new_player_x = new_room_offset_x + (new_room.width * new_room_relative_x)
            new_player_y = new_room_offset_y + (new_room.height * new_room_relative_y)
            
            return (new_player_x, new_player_y)
        
        return None
    
    def clear_current_room(self):
        """Mark current room as cleared and unlock doors"""
        self.current_room.unlock_doors()

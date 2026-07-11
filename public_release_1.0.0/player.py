import pygame
import math

class Player:
    def __init__(self, x, y, snake_variant=0):
        self.x = x
        self.y = y
        self.radius = 15
        self.speed = 5
        self.max_health = 10  # Increased from 6
        self.health = self.max_health
        self.shoot_cooldown = 0
        self.shoot_delay = 10  # Faster shooting (reduced from 15)
        self.invincibility_frames = 0  # I-frames after taking damage
        self.invincibility_duration = 60  # 1 second of invincibility at 60 FPS
        self.double_shot = False  # Can shoot two bullets at once
        self.triple_shot = False  # Can shoot three bullets at once
        self.quad_shot = False  # Can shoot four bullets at once
        
        # Snake body segments (for visual effect)
        self.body_segments = []
        self.last_positions = []  # Track previous positions for body segments
        self.segment_count = 5  # Number of body segments
        
        # Snake animation (for sprite-based rendering)
        self.snake_variant = snake_variant
        self.snake_animation = None
        try:
            from snake_animation import SnakeAnimation
            self.snake_animation = SnakeAnimation(x, y, size=4, palette_row=snake_variant)
        except Exception as e:
            print(f"Warning: Could not load snake animation: {e}")
            self.snake_animation = None
        
    def update(self, keys):
        """Update player position based on keyboard input"""
        # Movement
        dx = 0
        dy = 0
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed
        
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707  # 1/sqrt(2)
            dy *= 0.707
        
        self.x += dx
        self.y += dy
        
        # Update snake animation
        if self.snake_animation:
            self.snake_animation.x = self.x
            self.snake_animation.y = self.y
            # Set animation state based on movement
            if dx != 0 or dy != 0:
                self.snake_animation.is_moving = True
            else:
                self.snake_animation.is_moving = False
            # Update facing direction
            if dx != 0 or dy != 0:
                angle = math.atan2(dy, dx)
                self.snake_animation.set_facing_from_angle(angle)
            # Update animation
            self.snake_animation.update_animation()
        
        # Update body segment positions
        # Only add new position if actually moving (no movement = no trail update)
        if dx != 0 or dy != 0:
            self.last_positions.append((self.x, self.y))
            # Keep enough positions for all segments
            max_positions = self.segment_count * 12
            if len(self.last_positions) > max_positions:
                self.last_positions.pop(0)
        else:
            # When stopped, keep segments at their current positions (no reabsorption)
            # Don't add new positions, but maintain existing ones
            pass
        
        # Calculate body segment positions (evenly spaced along the trail)
        self.body_segments = []
        if len(self.last_positions) > self.segment_count:
            # Calculate spacing to ensure we always have all segments
            step = max(1, (len(self.last_positions) - 1) // (self.segment_count + 1))
            # Get segments from head to tail (excluding current position)
            for i in range(self.segment_count):
                idx = len(self.last_positions) - 2 - (i * step)
                if idx >= 0:
                    self.body_segments.append(self.last_positions[idx])
                else:
                    # If we don't have enough history, use the oldest position we have
                    if len(self.last_positions) > 0:
                        self.body_segments.append(self.last_positions[0])
        elif len(self.last_positions) > 0:
            # If we have some positions but not enough, fill with what we have
            for i in range(min(self.segment_count, len(self.last_positions) - 1)):
                idx = len(self.last_positions) - 2 - i
                if idx >= 0:
                    self.body_segments.append(self.last_positions[idx])
        
        # No boundary restrictions - player can move anywhere
        # Wall collisions are handled in the game update loop
        
        # Update cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1
    
    def shoot(self, target_x, target_y, bullets):
        """Shoot a bullet towards the target"""
        if self.shoot_cooldown > 0:
            return
        
        from bullet import Bullet
        
        # Calculate direction
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            # Normalize direction
            dx /= dist
            dy /= dist
            
            # Update snake animation for attack
            if self.snake_animation:
                angle = math.atan2(dy, dx)
                self.snake_animation.set_facing_from_angle(angle)
                self.snake_animation.start_attack()
            
            if self.quad_shot:
                # Shoot four bullets with spread
                spread = 0.25  # Angle spread in radians
                base_angle = math.atan2(dy, dx)
                # Four bullets in a cross pattern
                for i in range(4):
                    angle = base_angle + (i - 1.5) * spread
                    bullet = Bullet(self.x, self.y, math.cos(angle), math.sin(angle), is_player=True)
                    bullets.append(bullet)
            elif self.triple_shot:
                # Shoot three bullets with spread
                spread = 0.2  # Angle spread in radians
                base_angle = math.atan2(dy, dx)
                # Left bullet
                angle1 = base_angle - spread
                bullet1 = Bullet(self.x, self.y, math.cos(angle1), math.sin(angle1), is_player=True)
                bullets.append(bullet1)
                # Center bullet
                bullet2 = Bullet(self.x, self.y, dx, dy, is_player=True)
                bullets.append(bullet2)
                # Right bullet
                angle3 = base_angle + spread
                bullet3 = Bullet(self.x, self.y, math.cos(angle3), math.sin(angle3), is_player=True)
                bullets.append(bullet3)
            elif self.double_shot:
                # Shoot two bullets with slight spread
                spread = 0.15  # Angle spread in radians
                # First bullet (left)
                angle1 = math.atan2(dy, dx) - spread
                dx1 = math.cos(angle1)
                dy1 = math.sin(angle1)
                bullet1 = Bullet(self.x, self.y, dx1, dy1, is_player=True)
                bullets.append(bullet1)
                
                # Second bullet (right)
                angle2 = math.atan2(dy, dx) + spread
                dx2 = math.cos(angle2)
                dy2 = math.sin(angle2)
                bullet2 = Bullet(self.x, self.y, dx2, dy2, is_player=True)
                bullets.append(bullet2)
            else:
                # Single bullet
                bullet = Bullet(self.x, self.y, dx, dy, is_player=True)
                bullets.append(bullet)
            
            self.shoot_cooldown = self.shoot_delay
    
    def take_damage(self, amount):
        """Take damage and prevent health from going below 0"""
        if self.invincibility_frames > 0:
            return  # Can't take damage while invincible
        self.health = max(0, self.health - amount)
        self.invincibility_frames = self.invincibility_duration  # Start invincibility
        
        # Set defeated animation if health reaches 0
        if self.health <= 0 and self.snake_animation:
            self.snake_animation.set_defeated()
    
    def is_invincible(self):
        """Check if player is currently invincible"""
        return self.invincibility_frames > 0
    
    def draw(self, screen):
        """Draw the snake player with body segments"""
        # Use sprite animation if available
        if self.snake_animation:
            self.snake_animation.draw(screen, grid_cell_size=32, offset_y_adjust=-25)
        else:
            # Fallback to circle-based rendering
            # Flash when invincible (every 5 frames)
            if self.is_invincible() and (self.invincibility_frames // 5) % 2 == 0:
                # Draw brighter when flashing to show invincibility
                head_color = (100, 255, 100)  # Brighter green
                body_color = (100, 200, 100)
            else:
                head_color = (0, 200, 0)  # Green
                body_color = (0, 150, 0)  # Darker green
            
            # Draw body segments (from head to tail, in correct order)
            segment_radius = self.radius - 1  # Body segments are slightly smaller than head
            prev_x, prev_y = self.x, self.y  # Start from head
            
            # Draw connecting line from head to first segment
            if len(self.body_segments) > 0:
                first_seg = self.body_segments[0]
                pygame.draw.line(screen, body_color, 
                               (int(self.x), int(self.y)), 
                               (int(first_seg[0]), int(first_seg[1])), 
                               int(segment_radius * 2))
            
            # Draw segments in order from head to tail - with tapering
            for i, (seg_x, seg_y) in enumerate(self.body_segments):
                # Segments taper (get smaller) towards the tail
                size = segment_radius - (i * 1.0)  # Taper by 1 pixel per segment
                size = max(4, size)  # Minimum size to prevent disappearing
                if size > 2:
                    # Draw connecting line between segments (thickness tapers too)
                    if i > 0:
                        prev_seg = self.body_segments[i-1]
                        prev_size = segment_radius - ((i-1) * 1.0)
                        prev_size = max(4, prev_size)
                        line_thickness = int((size + prev_size))
                        pygame.draw.line(screen, body_color, 
                                       (int(prev_seg[0]), int(prev_seg[1])), 
                                       (int(seg_x), int(seg_y)), 
                                       line_thickness)
                    # Draw segment circle
                    pygame.draw.circle(screen, body_color, (int(seg_x), int(seg_y)), int(size))
                    pygame.draw.circle(screen, (0, 100, 0), (int(seg_x), int(seg_y)), int(size - 1))
            
            # Draw snake head (larger circle, drawn last so it's on top)
            pygame.draw.circle(screen, head_color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, body_color, (int(self.x), int(self.y)), self.radius - 3)
            
            # Draw eyes on head
            eye_offset = 5
            eye_y_offset = -3
            pygame.draw.circle(screen, (255, 255, 255), 
                              (int(self.x - eye_offset), int(self.y + eye_y_offset)), 4)
            pygame.draw.circle(screen, (255, 255, 255), 
                              (int(self.x + eye_offset), int(self.y + eye_y_offset)), 4)
            pygame.draw.circle(screen, (0, 0, 0), 
                              (int(self.x - eye_offset), int(self.y + eye_y_offset)), 2)
            pygame.draw.circle(screen, (0, 0, 0), 
                              (int(self.x + eye_offset), int(self.y + eye_y_offset)), 2)
            
            # Draw tongue (calculate direction from movement)
            if len(self.body_segments) > 0:
                # Use first body segment to determine direction
                first_seg = self.body_segments[0]
                dx = self.x - first_seg[0]
                dy = self.y - first_seg[1]
                dist = math.sqrt(dx*dx + dy*dy) if (dx != 0 or dy != 0) else 1
                if dist > 0:
                    dx /= dist
                    dy /= dist
                    tongue_length = 8
                    tongue_x = int(self.x + dx * (self.radius + tongue_length))
                    tongue_y = int(self.y + dy * (self.radius + tongue_length))
                    pygame.draw.line(screen, (255, 100, 100), 
                                   (int(self.x + dx * self.radius), int(self.y + dy * self.radius)),
                                   (tongue_x, tongue_y), 2)


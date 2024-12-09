"""
Space Shooter Game
Created by: razee4315 (https://github.com/razee4315)
Contact: saqlainrazee@gmail.com
"""

import pygame
import random
import sys
import os
import math
from pygame import mixer

# Initialize Pygame and mixer
pygame.init()
mixer.init()

# Initialize fonts
title_font = pygame.font.Font(None, 74)
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# Set up the game window
WIDTH = 800
HEIGHT = 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 150, 255)
PURPLE = (147, 0, 211)
CYAN = (0, 255, 255)

# Game states
WELCOME = "welcome"
PLAYING = "playing"
GAME_OVER = "game_over"

# Load game assets
def load_image(name):
    return pygame.image.load(os.path.join('assets', name)).convert_alpha()

# Load images
player_img = load_image('spaceship.png')
enemy_img = load_image('enemy.png')
laser_img = load_image('laser.png')
background_img = load_image('background.png')
powerup_img = load_image('powerup.png')
explosion_frames = [load_image(f'explosion_{i}.png') for i in range(8)]

# Player settings
PLAYER_SPEED = 5
player_rect = player_img.get_rect()
player_rect.centerx = WIDTH // 2
player_rect.bottom = HEIGHT - 10

# Game classes
class UIElement:
    def __init__(self, x, y, width, height, text, font, base_color, hover_color, alpha=255):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.alpha = alpha
        self.is_hovered = False
        self.animation_progress = 0
        self.glow_size = 0
    
    def draw(self, surface):
        # Draw button background with glow effect
        glow_rect = self.rect.inflate(self.glow_size, self.glow_size)
        s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        
        # Create gradient glow
        for i in range(10):
            size = i * 2
            r = self.rect.inflate(size, size)
            r.center = glow_rect.width//2, glow_rect.height//2
            color = self.hover_color if self.is_hovered else self.base_color
            color = (*color, 25 - i * 2)
            pygame.draw.rect(s, color, r, border_radius=10)
        
        # Draw main button
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(s, (*color, self.alpha), self.rect.move(-self.rect.x, -self.rect.y), 
                        border_radius=10)
        
        # Draw text with glow
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.move(-self.rect.x, -self.rect.y).center)
        
        # Add text glow
        glow_surf = self.font.render(self.text, True, (*color, 150))
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            s.blit(glow_surf, text_rect.move(dx, dy))
        s.blit(text_surf, text_rect)
        
        # Draw on main surface
        surface.blit(s, glow_rect)
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Update glow animation
        if self.is_hovered and self.glow_size < 20:
            self.glow_size += 2
        elif not self.is_hovered and self.glow_size > 0:
            self.glow_size -= 2
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.is_hovered
        return False

class Laser:
    def __init__(self, x, y, color, speed, damage):
        self.rect = pygame.Rect(x, y, 4, 10)
        self.color = color
        self.speed = speed
        self.damage = damage
    
    def move(self):
        self.rect.y += self.speed
    
    def colliderect(self, other_rect):
        return self.rect.colliderect(other_rect)

class Enemy:
    def __init__(self, x, y, level):
        self.rect = pygame.Rect(x, y, enemy_img.get_width(), enemy_img.get_height())
        self.health = 1 + (level // 3)
        self.speed = 2 + (level * 0.5)
        self.shoot_timer = 0
        self.shoot_delay = 2000
        self.can_shoot = level > 2

class PowerUp:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, powerup_img.get_width(), powerup_img.get_height())
        self.type = random.choice(['health', 'shield', 'rapid_fire', 'double_damage', 'speed_boost'])
        self.duration = 10000
        self.start_time = 0

class Explosion:
    def __init__(self, pos):
        self.pos = pos
        self.frame = 0
        self.animation_speed = 2
        self.counter = 0
    
    def update(self):
        self.counter += 1
        if self.counter >= self.animation_speed:
            self.frame += 1
            self.counter = 0
        return self.frame < len(explosion_frames)
    
    def draw(self, surface):
        if self.frame < len(explosion_frames):
            surface.blit(explosion_frames[self.frame], self.pos)

class Game:
    def __init__(self):
        self.high_score = 0
        self.reset()
    
    def reset(self):
        self.game_state = WELCOME
        self.score = 0
        self.wave_number = 1
        self.level = 1
        self.player_health = 100
        self.player_shield = 3
        self.player_speed = 5
        self.lasers = []
        self.enemy_lasers = []
        self.enemies = []
        self.power_ups = []
        self.explosions = []
        self.last_spawn_time = 0
        self.enemies_killed_in_wave = 0
        self.enemies_per_wave = 10
        self.kills_in_combo = 0
        self.combo_multiplier = 1
        self.combo_timer = 0
        self.rapid_fire = False
        self.rapid_fire_end = 0
        self.double_damage = False
        self.double_damage_end = 0
        self.speed_boost = False
        self.speed_boost_end = 0
        # Update high score when resetting
        self.high_score = max(self.high_score, self.score)

def clamp(value, min_value=0, max_value=255):
    return max(min_value, min(max_value, int(value)))

def update_game_objects():
    # Update laser positions
    for laser in game.lasers[:]:
        laser.move()
        if laser.rect.bottom < 0:
            game.lasers.remove(laser)
    
    for laser in game.enemy_lasers[:]:
        laser.move()
        if laser.rect.top > HEIGHT:
            game.enemy_lasers.remove(laser)
    
    # Update enemy positions
    for enemy in game.enemies[:]:
        # Smoother enemy movement
        enemy.rect.y += enemy.speed
        if enemy.rect.top > HEIGHT:
            if enemy in game.enemies:  # Check if enemy still exists
                game.enemies.remove(enemy)
                game.player_health -= 5  # Reduced penalty for missed enemies
                if game.player_health <= 0:
                    game.game_state = GAME_OVER
    
    # Update power-up positions
    for power_up in game.power_ups[:]:
        power_up.rect.y += 2
        if power_up.rect.top > HEIGHT:
            game.power_ups.remove(power_up)
    
    # Update explosions
    for explosion in game.explosions[:]:
        if explosion.frame >= len(explosion_frames):
            game.explosions.remove(explosion)
    
    # Enemy shooting
    current_time = pygame.time.get_ticks()
    for enemy in game.enemies:
        if game.level >= 3 and random.random() < 0.002:  # Reduced shooting frequency
            laser = Laser(
                enemy.rect.centerx,
                enemy.rect.bottom,
                (255, 0, 0),
                5,
                10
            )
            game.enemy_lasers.append(laser)
    
    # Check for wave completion
    if game.enemies_killed_in_wave >= game.enemies_per_wave and len(game.enemies) == 0:
        game.wave_number += 1
        game.level = (game.wave_number - 1) // 2 + 1
        game.enemies_killed_in_wave = 0
        game.enemies_per_wave = min(10 + game.wave_number * 2, 30)
    
    # Update power-up effects
    current_time = pygame.time.get_ticks()
    if game.rapid_fire and current_time > game.rapid_fire_end:
        game.rapid_fire = False
    if game.double_damage and current_time > game.double_damage_end:
        game.double_damage = False
    if game.speed_boost and current_time > game.speed_boost_end:
        game.speed_boost = False
    
    # Update combo system
    if current_time - game.combo_timer > 2000:
        game.kills_in_combo = 0
        game.combo_multiplier = 1

def spawn_enemy():
    current_time = pygame.time.get_ticks()
    # Only spawn if enough time has passed (based on level)
    spawn_delay = max(2000 - (game.level * 200), 500)  # Decrease delay with level, but not below 500ms
    if current_time - game.last_spawn_time < spawn_delay:
        return
    
    # Limit number of enemies on screen
    max_enemies = min(5 + game.level, 10)  # Maximum 10 enemies at once
    if len(game.enemies) >= max_enemies:
        return
    
    # Only spawn if we haven't reached the wave limit
    if game.enemies_killed_in_wave >= game.enemies_per_wave:
        return
    
    # Spawn enemy with proper spacing
    min_spacing = 60  # Minimum pixels between enemies
    valid_position = False
    max_attempts = 10
    
    while max_attempts > 0 and not valid_position:
        x = random.randint(0, WIDTH - enemy_img.get_width())
        valid_position = True
        
        # Check distance from other enemies
        for enemy in game.enemies:
            if abs(enemy.rect.x - x) < min_spacing:
                valid_position = False
                break
        
        max_attempts -= 1
        if valid_position:
            enemy = Enemy(x, -enemy_img.get_height(), game.level)
            game.enemies.append(enemy)
            game.last_spawn_time = current_time
            break

def check_collisions():
    current_time = pygame.time.get_ticks()
    
    # Player collision with enemy lasers
    player_rect_reduced = player_rect.inflate(-20, -20)  # Smaller hitbox for player
    for laser in game.enemy_lasers[:]:
        if laser in game.enemy_lasers and player_rect_reduced.colliderect(laser.rect):
            game.enemy_lasers.remove(laser)
            if game.player_shield > 0:
                game.player_shield -= 1
            else:
                game.player_health -= 10
                if game.player_health <= 0:
                    game.game_state = GAME_OVER
    
    # Player collision with enemies
    for enemy in game.enemies[:]:
        if enemy in game.enemies and player_rect_reduced.colliderect(enemy.rect):
            if game.player_shield > 0:
                game.player_shield -= 1
                game.enemies.remove(enemy)
            else:
                game.player_health -= 20
                if game.player_health <= 0:
                    game.game_state = GAME_OVER
            if enemy in game.enemies:
                game.enemies.remove(enemy)
    
    # Laser collision with enemies
    for laser in game.lasers[:]:
        for enemy in game.enemies[:]:
            if laser in game.lasers and enemy in game.enemies and laser.colliderect(enemy.rect):
                if laser in game.lasers:
                    game.lasers.remove(laser)
                enemy.health -= laser.damage
                if enemy.health <= 0 and enemy in game.enemies:
                    game.enemies.remove(enemy)
                    game.enemies_killed_in_wave += 1
                    game.score += int(10 * game.level * game.combo_multiplier)
                    
                    # Update combo
                    game.kills_in_combo += 1
                    game.combo_multiplier = min(4, 1 + (game.kills_in_combo // 3))
                    game.combo_timer = current_time
    
    # Player collision with power-ups
    for power_up in game.power_ups[:]:
        if power_up in game.power_ups and player_rect_reduced.colliderect(power_up.rect):
            apply_power_up(power_up)
            game.power_ups.remove(power_up)

def apply_power_up(power_up):
    current_time = pygame.time.get_ticks()
    if power_up.type == 'health':
        game.player_health = min(100, game.player_health + 30)
    elif power_up.type == 'shield':
        game.player_shield = min(3, game.player_shield + 1)
    elif power_up.type == 'rapid_fire':
        game.rapid_fire = True
        game.rapid_fire_end = current_time + power_up.duration
    elif power_up.type == 'double_damage':
        game.double_damage = True
        game.double_damage_end = current_time + power_up.duration
    elif power_up.type == 'speed_boost':
        game.speed_boost = True
        game.speed_boost_end = current_time + power_up.duration

def spawn_power_up():
    if random.random() < 0.001:
        power_up = PowerUp(
            random.randint(0, WIDTH - powerup_img.get_width()),
            -powerup_img.get_height()
        )
        game.power_ups.append(power_up)

def draw_game():
    # Draw background with parallax scrolling
    rel_y = pygame.time.get_ticks() * 0.1 % HEIGHT
    window.blit(background_img, (0, rel_y))
    window.blit(background_img, (0, rel_y - HEIGHT))
    
    if game.game_state == WELCOME:
        draw_welcome_screen()
    elif game.game_state == PLAYING:
        # Draw player with engine effect
        window.blit(player_img, player_rect)
        
        # Draw lasers with color and trail
        for laser in game.lasers:
            pygame.draw.rect(window, laser.color, laser.rect)
        
        # Draw enemy lasers with trail
        for laser in game.enemy_lasers:
            pygame.draw.rect(window, (255, 0, 0), laser.rect)
        
        # Draw enemies
        for enemy in game.enemies:
            window.blit(enemy_img, enemy.rect)
        
        # Draw power-ups with pulsing effect and particles
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 0.2
        for power_up in game.power_ups:
            scaled_powerup = pygame.transform.scale(powerup_img, 
                (int(power_up.rect.width * (1 + pulse)), int(power_up.rect.height * (1 + pulse))))
            power_up_rect = scaled_powerup.get_rect(center=power_up.rect.center)
            window.blit(scaled_powerup, power_up_rect)
        
        # Draw explosions
        for explosion in game.explosions[:]:
            explosion.draw(window)
        
        # Draw HUD
        draw_hud()
        
    elif game.game_state == GAME_OVER:
        draw_game_over_screen()
    
    pygame.display.update()

def draw_hud():
    # Create semi-transparent HUD surface with gradient
    hud_height = 60
    hud_surface = pygame.Surface((WIDTH, hud_height), pygame.SRCALPHA)
    for i in range(hud_height):
        alpha = clamp(128 * (1 - i/hud_height))
        pygame.draw.line(hud_surface, (0, 0, 0, alpha), (0, i), (WIDTH, i))
    window.blit(hud_surface, (0, 0))
    
    # Draw score and wave info
    score_text = font.render(f"SCORE: {game.score}", True, WHITE)
    level_text = font.render(f"WAVE: {game.wave_number}", True, WHITE)
    combo_text = font.render(f"COMBO: x{game.combo_multiplier}", True, YELLOW)
    
    # Draw text with glow effect
    for text, pos, color in [
        (score_text, (20, 10), BLUE),
        (level_text, (WIDTH - 120, 10), GREEN),
        (combo_text, (WIDTH//2 - 50, 10), YELLOW)
    ]:
        # Draw glow
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            window.blit(text, (pos[0] + dx, pos[1] + dy))
        # Draw main text
        window.blit(text, pos)
    
    # Draw health bar
    health_width = 200
    health_height = 10
    health_x = WIDTH//2 - health_width//2
    health_y = 35
    
    # Health bar background
    pygame.draw.rect(window, (50, 50, 50), (health_x, health_y, health_width, health_height))
    
    # Health bar fill with gradient
    health_percent = max(0, game.player_health / 100)
    health_fill = int(health_width * health_percent)
    
    for i in range(health_fill):
        progress = i / health_width
        r = clamp(255 * (1 - health_percent))
        g = clamp(255 * health_percent)
        pygame.draw.line(window, (r, g, 0), 
                        (health_x + i, health_y),
                        (health_x + i, health_y + health_height))
    
    # Draw shield indicators
    for i in range(game.player_shield):
        shield_x = WIDTH - 30 - (i * 25)
        shield_y = 35
        
        # Draw shield glow
        for size in range(3, 0, -1):
            alpha = clamp(128 / size)
            pygame.draw.circle(window, (CYAN[0], CYAN[1], CYAN[2], alpha), 
                             (shield_x, shield_y), 8 + size)
        
        # Draw main shield
        pygame.draw.circle(window, CYAN, (shield_x, shield_y), 8)
    
    # Draw wave progress bar
    progress_width = 150
    progress_height = 10
    progress_x = 20
    progress_y = 35
    
    # Progress bar background
    pygame.draw.rect(window, (50, 50, 50), 
                    (progress_x, progress_y, progress_width, progress_height))
    
    # Progress bar fill
    wave_progress = game.enemies_killed_in_wave / game.enemies_per_wave
    fill_width = int(progress_width * wave_progress)
    
    for i in range(fill_width):
        progress = i / progress_width
        r = 0
        g = clamp(255 * (1 - progress) + 200 * progress)
        b = clamp(255 * progress)
        pygame.draw.line(window, (r, g, b),
                        (progress_x + i, progress_y),
                        (progress_x + i, progress_y + progress_height))
    
    # Draw active power-ups
    power_up_x = WIDTH - 200
    power_up_y = 10
    
    if game.rapid_fire:
        remaining = max(0, (game.rapid_fire_end - pygame.time.get_ticks()) / 1000)
        if remaining > 0:
            text = small_font.render(f"RAPID FIRE {remaining:.1f}s", True, YELLOW)
            window.blit(text, (power_up_x, power_up_y))
    
    if game.double_damage:
        remaining = max(0, (game.double_damage_end - pygame.time.get_ticks()) / 1000)
        if remaining > 0:
            text = small_font.render(f"DOUBLE DMG {remaining:.1f}s", True, RED)
            window.blit(text, (power_up_x, power_up_y + 15))
    
    if game.speed_boost:
        remaining = max(0, (game.speed_boost_end - pygame.time.get_ticks()) / 1000)
        if remaining > 0:
            text = small_font.render(f"SPEED BOOST {remaining:.1f}s", True, GREEN)
            window.blit(text, (power_up_x, power_up_y + 30))

def draw_welcome_screen():
    window.blit(background_img, (0, 0))
    
    # Create a semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 20))
    overlay.set_alpha(128)
    window.blit(overlay, (0, 0))
    
    # Draw title with glow effect
    title_shadow = title_font.render("SPACE SHOOTER", True, (0, 100, 255))
    title_text = title_font.render("SPACE SHOOTER", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//3))
    
    # Add multiple shadows for stronger glow effect
    for offset in range(1, 4):
        shadow_rect = title_rect.copy()
        shadow_rect.x += offset
        shadow_rect.y += offset
        window.blit(title_shadow, shadow_rect)
    
    window.blit(title_text, title_rect)
    
    # Create buttons
    start_button = UIElement(WIDTH//2 - 100, HEIGHT//2, 200, 50, "START GAME", font, (0, 100, 200), (0, 150, 255))
    quit_button = UIElement(WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50, "QUIT", font, (200, 0, 0), (255, 0, 0))
    
    start_button.draw(window)
    quit_button.draw(window)
    
    # Draw controls in a nice box
    controls_surface = pygame.Surface((300, 120))
    controls_surface.fill((0, 0, 40))
    pygame.draw.rect(controls_surface, (0, 100, 200), controls_surface.get_rect(), 2)
    
    controls_title = small_font.render("CONTROLS", True, WHITE)
    move_text = small_font.render("← → Arrow Keys : Move", True, WHITE)
    shoot_text = small_font.render("SPACE : Shoot", True, WHITE)
    
    controls_surface.blit(controls_title, (20, 10))
    controls_surface.blit(move_text, (20, 50))
    controls_surface.blit(shoot_text, (20, 80))
    
    window.blit(controls_surface, (WIDTH//2 - 150, HEIGHT - 150))
    
    if game.high_score > 0:
        high_score_text = font.render(f"HIGH SCORE: {game.high_score}", True, YELLOW)
        high_score_rect = high_score_text.get_rect(center=(WIDTH//2, HEIGHT - 200))
        window.blit(high_score_text, high_score_rect)

def draw_game_over_screen():
    # Keep the game view in the background
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 20))
    overlay.set_alpha(180)
    window.blit(overlay, (0, 0))
    
    # Draw game over message with glow effect
    if game.player_health <= 0:
        text = "GAME OVER"
        color = RED
    else:
        text = "VICTORY!"
        color = GREEN
    
    game_over_text = title_font.render(text, True, color)
    text_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//3))
    
    # Add glow effect
    for offset in range(1, 4):
        shadow = title_font.render(text, True, (*color[:3], 128))
        shadow_rect = text_rect.copy()
        shadow_rect.x += offset
        shadow_rect.y += offset
        window.blit(shadow, shadow_rect)
    
    window.blit(game_over_text, text_rect)
    
    # Create a stats box
    stats_surface = pygame.Surface((300, 200))
    stats_surface.fill((0, 0, 40))
    pygame.draw.rect(stats_surface, (0, 100, 200), stats_surface.get_rect(), 2)
    
    # Draw stats
    score_text = font.render(f"Score: {game.score}", True, WHITE)
    level_text = font.render(f"Level: {game.level}", True, WHITE)
    high_score_text = font.render(f"High Score: {game.high_score}", True, YELLOW)
    
    stats_surface.blit(score_text, (20, 20))
    stats_surface.blit(level_text, (20, 60))
    stats_surface.blit(high_score_text, (20, 100))
    
    window.blit(stats_surface, (WIDTH//2 - 150, HEIGHT//2))
    
    # Create buttons
    restart_button = UIElement(WIDTH//2 - 200, HEIGHT - 100, 180, 50, "PLAY AGAIN", font, (0, 100, 200), (0, 150, 255))
    quit_button = UIElement(WIDTH//2 + 20, HEIGHT - 100, 180, 50, "QUIT", font, (200, 0, 0), (255, 0, 0))
    
    restart_button.draw(window)
    quit_button.draw(window)

def main():
    global game, player_rect, last_shot_time
    
    pygame.init()
    pygame.display.set_caption("Space Shooter")
    
    game = Game()
    player_rect = player_img.get_rect()
    player_rect.centerx = WIDTH // 2
    player_rect.bottom = HEIGHT - 20
    
    last_shot_time = 0
    shot_delay = 250
    
    # Create buttons for menu screens
    start_button = UIElement(WIDTH//2 - 100, HEIGHT//2, 200, 50, "START GAME", font, (0, 100, 200), (0, 150, 255))
    quit_button = UIElement(WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50, "QUIT", font, (200, 0, 0), (255, 0, 0))
    restart_button = UIElement(WIDTH//2 - 200, HEIGHT - 100, 180, 50, "PLAY AGAIN", font, (0, 100, 200), (0, 150, 255))
    game_over_quit_button = UIElement(WIDTH//2 + 20, HEIGHT - 100, 180, 50, "QUIT", font, (200, 0, 0), (255, 0, 0))
    
    clock = pygame.time.Clock()
    
    while True:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            if game.game_state == WELCOME:
                start_button.update()
                quit_button.update()
                if start_button.handle_event(event):
                    game.reset()
                    game.game_state = PLAYING
                elif quit_button.handle_event(event):
                    pygame.quit()
                    return
            
            elif game.game_state == GAME_OVER:
                restart_button.update()
                game_over_quit_button.update()
                if restart_button.handle_event(event):
                    game.reset()
                    game.game_state = PLAYING
                elif game_over_quit_button.handle_event(event):
                    pygame.quit()
                    return
        
        if game.game_state == PLAYING:
            keys = pygame.key.get_pressed()
            
            # Player movement
            if keys[pygame.K_LEFT] and player_rect.left > 0:
                player_rect.x -= game.player_speed * (1.5 if game.speed_boost else 1)
            if keys[pygame.K_RIGHT] and player_rect.right < WIDTH:
                player_rect.x += game.player_speed * (1.5 if game.speed_boost else 1)
            if keys[pygame.K_UP] and player_rect.top > 0:
                player_rect.y -= game.player_speed * (1.5 if game.speed_boost else 1)
            if keys[pygame.K_DOWN] and player_rect.bottom < HEIGHT:
                player_rect.y += game.player_speed * (1.5 if game.speed_boost else 1)
            
            # Shooting
            if keys[pygame.K_SPACE] and current_time - last_shot_time > (shot_delay / 2 if game.rapid_fire else shot_delay):
                laser = Laser(
                    player_rect.centerx - 2,
                    player_rect.top,
                    (0, 255, 0),
                    -10,
                    20 if game.double_damage else 10
                )
                game.lasers.append(laser)
                last_shot_time = current_time
                try:
                    laser_sound.play()
                except:
                    pass
            
            # Spawn enemies and power-ups
            spawn_enemy()
            spawn_power_up()
            
            # Update game state
            update_game_objects()
            check_collisions()
        
        # Draw game
        draw_game()
        
        # Cap the frame rate
        clock.tick(60)

if __name__ == "__main__":
    main()

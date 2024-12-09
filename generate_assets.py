import pygame
import os
import math
import random
from pygame import gfxdraw

# Initialize Pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (30, 144, 255)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)
PURPLE = (147, 0, 211)
ORANGE = (255, 165, 0)

def create_gradient_surface(width, height, start_color, end_color):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        ratio = y / height
        color = [start + (end - start) * ratio for start, end in zip(start_color, end_color)]
        pygame.draw.line(surface, color, (0, y), (width, y))
    return surface

def create_spaceship(size=80):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Create metallic gradient for ship body
    ship_color1 = (50, 150, 255)
    ship_color2 = (20, 60, 200)
    
    # Main body
    points = [
        (size//2, size//4),  # top
        (size//6, size*3//4),  # bottom left
        (size//2, size*2//3),  # bottom middle
        (size*5//6, size*3//4),  # bottom right
    ]
    
    # Draw shadow
    shadow_points = [(x+2, y+2) for x, y in points]
    pygame.draw.polygon(surface, (*BLACK, 128), shadow_points)
    
    # Draw main body with gradient
    pygame.draw.polygon(surface, ship_color1, points)
    
    # Add details
    # Wings
    wing_color = (30, 100, 220)
    pygame.draw.polygon(surface, wing_color, [
        (size//6, size*3//4),
        (0, size*7//8),
        (size//4, size*3//4)
    ])
    pygame.draw.polygon(surface, wing_color, [
        (size*5//6, size*3//4),
        (size, size*7//8),
        (size*3//4, size*3//4)
    ])
    
    # Engine glow
    for i in range(10):
        alpha = 255 - i * 25
        radius = size//8 - i
        if radius > 0:
            gfxdraw.filled_circle(surface, size//2, int(size*0.7), radius, (*ORANGE, alpha))
    
    # Cockpit
    cockpit_color = (200, 230, 255)
    pygame.draw.ellipse(surface, cockpit_color, (size*3//8, size*3//8, size//4, size//4))
    
    # Add highlight
    highlight_color = (255, 255, 255, 100)
    pygame.draw.line(surface, highlight_color, (size//3, size//3), (size*2//3, size//3), 2)
    
    return surface

def create_enemy(size=60):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Create metallic gradient for alien body
    alien_color1 = (180, 50, 180)
    alien_color2 = (100, 0, 100)
    
    # Main body
    body_height = size//2
    body_rect = pygame.Rect(0, size//4, size, body_height)
    
    # Draw shadow
    shadow_rect = body_rect.copy()
    shadow_rect.move_ip(2, 2)
    pygame.draw.ellipse(surface, (*BLACK, 128), shadow_rect)
    
    # Draw main body with gradient
    gradient = create_gradient_surface(size, body_height, alien_color1, alien_color2)
    body_surface = pygame.Surface((size, body_height), pygame.SRCALPHA)
    pygame.draw.ellipse(body_surface, alien_color1, (0, 0, size, body_height))
    body_surface.blit(gradient, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(body_surface, (0, size//4))
    
    # Draw glowing eyes
    eye_color = (255, 50, 50)
    for i in range(5):
        alpha = 255 - i * 50
        radius = size//10 - i
        if radius > 0:
            gfxdraw.filled_circle(surface, size//3, size//2, radius, (*eye_color, alpha))
            gfxdraw.filled_circle(surface, 2*size//3, size//2, radius, (*eye_color, alpha))
    
    # Add tentacles
    tentacle_color = (160, 32, 240)
    for i in range(3):
        start_x = size * (i + 1) // 4
        end_x = start_x + random.randint(-10, 10)
        curve_x = start_x + random.randint(-15, 15)
        
        points = [(start_x, size*3//4),
                 (curve_x, size*7//8),
                 (end_x, size)]
        pygame.draw.lines(surface, tentacle_color, False, points, 3)
    
    return surface

def create_laser(width=8, height=30):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Create energy beam effect
    center_color = (255, 255, 255, 255)
    outer_color = (50, 255, 50, 0)
    
    for i in range(width//2):
        alpha = 255 - (i * 255 // (width//2))
        color = (*GREEN[:3], alpha)
        pygame.draw.line(surface, color, (width//2 - i, 0), (width//2 - i, height))
        pygame.draw.line(surface, color, (width//2 + i, 0), (width//2 + i, height))
    
    # Add glow effect
    for i in range(3):
        alpha = 100 - i * 30
        pygame.draw.line(surface, (*WHITE, alpha), (width//2, 0), (width//2, height), 2-i)
    
    return surface

def create_power_up(size=40):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Create shining orb effect
    for i in range(size//2, 0, -2):
        alpha = 255 if i == size//2 else 128 - (i * 128 // (size//2))
        color = (255, 215, 0, alpha)  # Golden color
        gfxdraw.filled_circle(surface, size//2, size//2, i, color)
    
    # Add star effect
    star_points = []
    for i in range(8):
        angle = i * math.pi / 4
        outer_point = (size//2 + int(math.cos(angle) * size//2),
                      size//2 + int(math.sin(angle) * size//2))
        inner_point = (size//2 + int(math.cos(angle + math.pi/8) * size//4),
                      size//2 + int(math.sin(angle + math.pi/8) * size//4))
        star_points.extend([outer_point, inner_point])
    
    pygame.draw.polygon(surface, (255, 255, 200, 180), star_points)
    
    return surface

def create_star_background(width=800, height=600):
    surface = pygame.Surface((width, height))
    
    # Create space gradient
    gradient = create_gradient_surface(width, height, (0, 0, 40), (0, 0, 20))
    surface.blit(gradient, (0, 0))
    
    # Add stars with different sizes and brightness
    for _ in range(100):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        size = random.randint(1, 3)
        brightness = random.randint(128, 255)
        color = (brightness, brightness, brightness)
        
        # Draw star with glow
        if size > 1:
            pygame.draw.circle(surface, (brightness//2, brightness//2, brightness//2), (x, y), size+1)
        pygame.draw.circle(surface, color, (x, y), size)
    
    # Add some nebula-like effects
    for _ in range(5):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        radius = random.randint(50, 100)
        color = random.choice([(30, 0, 30, 5), (0, 0, 30, 5), (30, 30, 0, 5)])
        
        for i in range(radius, 0, -2):
            alpha = 5 - (i * 5 // radius)
            if alpha > 0:
                gfxdraw.filled_circle(surface, x, y, i, (*color[:3], alpha))
    
    return surface

def create_explosion_frames(size=100, num_frames=8):
    frames = []
    
    for frame in range(num_frames):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        scale = (frame + 1) / num_frames
        
        # Create expanding ring effect
        ring_radius = int(size//2 * scale)
        ring_width = max(2, int(10 * (1 - scale)))
        
        for offset in range(ring_width):
            radius = ring_radius - offset
            if radius > 0:
                alpha = 255 - (frame * 255 // num_frames) - (offset * 255 // ring_width)
                if alpha > 0:
                    color = (255, 200 - (frame * 20), 0, alpha)
                    gfxdraw.filled_circle(surface, size//2, size//2, radius, color)
        
        # Add particles
        num_particles = 20
        for _ in range(num_particles):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(0, ring_radius)
            x = size//2 + int(math.cos(angle) * distance)
            y = size//2 + int(math.sin(angle) * distance)
            particle_size = random.randint(1, 3)
            alpha = 255 - (frame * 255 // num_frames)
            if alpha > 0:
                color = (255, random.randint(100, 200), 0, alpha)
                gfxdraw.filled_circle(surface, x, y, particle_size, color)
        
        frames.append(surface)
    
    return frames

def save_assets():
    # Create assets directory if it doesn't exist
    if not os.path.exists('assets'):
        os.makedirs('assets')
    
    # Generate and save all assets
    pygame.image.save(create_spaceship(), 'assets/spaceship.png')
    pygame.image.save(create_enemy(), 'assets/enemy.png')
    pygame.image.save(create_laser(), 'assets/laser.png')
    pygame.image.save(create_star_background(), 'assets/background.png')
    pygame.image.save(create_power_up(), 'assets/powerup.png')
    
    # Save explosion frames
    explosion_frames = create_explosion_frames()
    for i, frame in enumerate(explosion_frames):
        pygame.image.save(frame, f'assets/explosion_{i}.png')

if __name__ == "__main__":
    save_assets()
    print("Assets generated successfully!")

import pygame

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
MAP_WIDTH, MAP_HEIGHT = 4000, 4000 # Map beaucoup plus grande
FPS = 60
TITLE = "Daft Punk: Extraction Run"

# --- Couleurs ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
NEON_BLUE = (0, 255, 255)
NEON_PINK = (255, 20, 147)
NEON_GREEN = (57, 255, 20)
GOLD_COLOR = (255, 215, 0)

# --- Gameplay ---
ENEMY_SPAWN_INTERVAL_MS = 1500
MAX_ENEMIES = 30

EXTRACT_SIZE = 150
EXTRACT_DELAY_MS = 60000 # 60s
EXTRACT_DURATION_MS = 30000 # 30s

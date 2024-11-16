import pygame
import random
import time
from collections import defaultdict

# Parameters
GRID_WIDTH, GRID_HEIGHT = 1_000_000, 1_000_000  #grid size
CELL_SIZE = 2
VIEWPORT_WIDTH, VIEWPORT_HEIGHT = 500, 400  #size of the viewport in cells
INITIAL_REGION_SIZE = 600  # Size of each region around the viewport to populate with cells
INITIAL_DENSITY = 0.05  # density of alive cells in each region
UPDATE_INTERVAL = 5
GRID_LINE_SPACING = 100
frame_count = 0
first_run = True

pygame.init()
screen = pygame.display.set_mode((VIEWPORT_WIDTH * CELL_SIZE, VIEWPORT_HEIGHT * CELL_SIZE))
pygame.display.set_caption("Conway's Game of Life")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)  
LABEL_COLOR = (150, 150, 150)

pygame.font.init()
font = pygame.font.SysFont(None, 20)

alive_cells = set()
initialized_regions = set()

def draw_fps(screen, clock):
    fps = clock.get_fps()
    fps_text = font.render(f"FPS: {fps}", True, WHITE)
    screen.blit(fps_text, (10, 10))

def initialize_region(center_x, center_y):
    #initialize a region around the center
    region_start_x = center_x - INITIAL_REGION_SIZE // 2
    region_start_y = center_y - INITIAL_REGION_SIZE // 2
    region_end_x = region_start_x + INITIAL_REGION_SIZE
    region_end_y = region_start_y + INITIAL_REGION_SIZE

    total_cells_in_region = INITIAL_REGION_SIZE * INITIAL_REGION_SIZE
    target_alive_cells = int(total_cells_in_region * INITIAL_DENSITY)

    new_cells = set()
    while len(new_cells) < target_alive_cells:
        x = random.randint(region_start_x, region_end_x - 1)
        y = random.randint(region_start_y, region_end_y - 1)
        new_cells.add((x, y))
    
    alive_cells.update(new_cells)

BUFFER_SIZE = 2 * max(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)

recently_removed_regions = set()

def uninitialize_region(center_x, center_y):
    region_start_x = center_x - INITIAL_REGION_SIZE // 2
    region_start_y = center_y - INITIAL_REGION_SIZE // 2
    region_end_x = region_start_x + INITIAL_REGION_SIZE
    region_end_y = region_start_y + INITIAL_REGION_SIZE
    
    cells_to_remove = {(x, y) for x in range(region_start_x, region_end_x)
                               for y in range(region_start_y, region_end_y)}
    alive_cells.difference_update(cells_to_remove)
    recently_removed_regions.add((center_x, center_y))

def update_viewport_cells(viewport_x, viewport_y):
    region_center_x = (viewport_x + VIEWPORT_WIDTH // 2) // INITIAL_REGION_SIZE * INITIAL_REGION_SIZE
    region_center_y = (viewport_y + VIEWPORT_HEIGHT // 2) // INITIAL_REGION_SIZE * INITIAL_REGION_SIZE

    #initialize a 3x3 grid of regions around the viewport center
    for dx in (-INITIAL_REGION_SIZE, 0, INITIAL_REGION_SIZE):
        for dy in (-INITIAL_REGION_SIZE, 0, INITIAL_REGION_SIZE):
            region_pos = (min(region_center_x + dx, GRID_WIDTH - INITIAL_REGION_SIZE // 2), 
                          min(region_center_y + dy, GRID_HEIGHT - INITIAL_REGION_SIZE // 2))
        
            if region_pos not in initialized_regions and region_pos not in recently_removed_regions:
                initialize_region(region_pos[0], region_pos[1])
                initialized_regions.add(region_pos)

    to_remove = []
    for old_region in initialized_regions:
        region_x, region_y = old_region
        if (region_x < viewport_x - BUFFER_SIZE or region_x > viewport_x + VIEWPORT_WIDTH + BUFFER_SIZE or
            region_y < viewport_y - BUFFER_SIZE or region_y > viewport_y + VIEWPORT_HEIGHT + BUFFER_SIZE):
            to_remove.append(old_region)

    for old_region in to_remove:
        if len(initialized_regions) > 6:
            uninitialize_region(old_region[0], old_region[1])
            initialized_regions.remove(old_region)
            print(f"Removed region: {old_region}")
            break

    #periodically clear recently removed regions to allow for reinitialization
    if frame_count % 100 == 0:  # Adjust this interval as needed
        recently_removed_regions.clear()


def update_grid(alive_cells):
    global first_run
    if first_run:
        start_time = time.time()

    neighbor_counts = defaultdict(int)
    for (x, y) in alive_cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx != 0 or dy != 0:
                    neighbor_counts[(x + dx, y + dy)] += 1

    new_alive_cells = set()
    for cell, count in neighbor_counts.items():
        if count == 3 or (count == 2 and cell in alive_cells):
            new_alive_cells.add(cell)

    if first_run:
        end_time = time.time()
        first_run = False
        
    return new_alive_cells

def draw_grid_lines_and_labels(screen, viewport_x, viewport_y):
    start_x = -(viewport_x % GRID_LINE_SPACING)
    start_y = -(viewport_y % GRID_LINE_SPACING)

    for x in range(start_x, VIEWPORT_WIDTH, GRID_LINE_SPACING):
        grid_x = viewport_x + x
        pygame.draw.line(screen, GRAY, (x * CELL_SIZE, 0), (x * CELL_SIZE, VIEWPORT_HEIGHT * CELL_SIZE))
        label = font.render(str(grid_x), True, LABEL_COLOR)
        screen.blit(label, (x * CELL_SIZE + 2, 2))

    for y in range(start_y, VIEWPORT_HEIGHT, GRID_LINE_SPACING):
        grid_y = viewport_y + y
        pygame.draw.line(screen, GRAY, (0, y * CELL_SIZE), (VIEWPORT_WIDTH * CELL_SIZE, y * CELL_SIZE))
        label = font.render(str(grid_y), True, LABEL_COLOR)
        screen.blit(label, (2, y * CELL_SIZE + 2))

def draw_grid(screen, alive_cells, viewport_x, viewport_y):
    screen.fill(BLACK)
    draw_grid_lines_and_labels(screen, viewport_x, viewport_y)
    
    for (x, y) in alive_cells:
        if viewport_x <= x < viewport_x + VIEWPORT_WIDTH and viewport_y <= y < viewport_y + VIEWPORT_HEIGHT:
            screen_x = (x - viewport_x) * CELL_SIZE
            screen_y = (y - viewport_y) * CELL_SIZE
            pygame.draw.rect(screen, WHITE, (screen_x, screen_y, CELL_SIZE, CELL_SIZE))

def main():
    global alive_cells
    global frame_count
    viewport_x, viewport_y = 0, 0
    update_viewport_cells(viewport_x, viewport_y)

    running = True
    clock = pygame.time.Clock()
    frame_count = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    viewport_x = max(0, viewport_x - 1000)
                elif event.key == pygame.K_RIGHT:
                    viewport_x = min(GRID_WIDTH - VIEWPORT_WIDTH, viewport_x + 30)
                elif event.key == pygame.K_UP:
                    viewport_y = max(0, viewport_y - 30)
                elif event.key == pygame.K_DOWN:
                    viewport_y = min(GRID_HEIGHT - VIEWPORT_HEIGHT, viewport_y + 30)

        update_viewport_cells(viewport_x, viewport_y)

        if frame_count % UPDATE_INTERVAL == 0:
            alive_cells = update_grid(alive_cells)

        draw_grid(screen, alive_cells, viewport_x, viewport_y)
        draw_fps(screen, clock)
        pygame.display.flip()
        clock.tick() 
        frame_count += 1
        
    pygame.quit()

if __name__ == "__main__":
    main()
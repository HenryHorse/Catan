


# https://www.redblobgames.com/grids/hexagons/ Very useful source for hexagons



import math
import pygame



class TileVertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.adjacent_tiles = []

    def add_adjacent_tile(self, tile_vertex):
        self.adjacent_tiles.append(tile_vertex)

    def __repr__(self):
        return "Tile Vert: (" + str(self.x) + "," + str(self.y) + ")"

class RoadVertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.adjacent_roads = []
        self.adjacent_tiles = []
        self.harbor = False

    def add_adjacent_tile(self, tile_vertex):
        self.adjacent_tiles.append(tile_vertex)

    def add_adjacent_road(self, road_vertex):
        self.adjacent_roads.append(road_vertex)

    def __repr__(self):
        return "Road Vert: (" + str(self.x) + "," + str(self.y) + ")"
        



# Function to get a hexagon corner (6 possible)
# This is some semi-complicated math, but was thankfully figured out by RedBlobGames already
def hex_corner(center, size, corner):
    angle_deg = 60 * corner - 30
    angle_rad = math.pi / 180 * angle_deg
    return center.x + size * math.cos(angle_rad), center.y + size * math.sin(angle_rad)

def generate_hex_board(center, size):
    hex_centers = [center]
    vertex_positions = set()
    visited_verts = {}

    directions = [
        (math.sqrt(3) * size, 0),                  # Right
        (math.sqrt(3)/2 * size, -1.5 * size),      # Top-right
        (-math.sqrt(3)/2 * size, -1.5 * size),     # Top-left
        (-math.sqrt(3) * size, 0),                 # Left
        (-math.sqrt(3)/2 * size, 1.5 * size),      # Bottom-left
        (math.sqrt(3)/2 * size, 1.5 * size)        # Bottom-right
    ]

    # Generate centers for outer hexagons
    for ring in range(1, 3):
        start = TileVertex(center.x + ring * directions[4][0], center.y + ring * directions[4][1])
        curr = start
        for d in range(6):
            for _ in range(ring):
                curr = TileVertex(curr.x + directions[d][0], curr.y + directions[d][1])
                hex_centers.append(curr)


    for center in hex_centers:
        last = None
        for i in range(6):
            hc = hex_corner(center, size, i)
            rounded_hc = (round(hc[0]), round(hc[1]))
            
            if rounded_hc not in visited_verts:
                visited_verts[rounded_hc] = RoadVertex(hc[0], hc[1])
            else:
                for adj_tile in visited_verts[rounded_hc].adjacent_tiles:
                    adj_tile.add_adjacent_tile(center)
                    center.add_adjacent_tile(adj_tile)
            visited_verts[rounded_hc].add_adjacent_tile(center)


            if (last is not None):
                visited_verts[rounded_hc].add_adjacent_road(last)
                last.add_adjacent_road(visited_verts[rounded_hc])
            last = visited_verts[rounded_hc]
            vertex_positions.add(visited_verts[rounded_hc])
        hc = hex_corner(center, size, 0)
        rounded_hc = (round(hc[0]), round(hc[1]))
        last.add_adjacent_road(visited_verts[rounded_hc])
        visited_verts[rounded_hc].add_adjacent_road(last)
    
    return hex_centers, vertex_positions


def generate_harbors(centers, vertices):
    for vertex in vertices:
        # if len(vertex.adjacent_tiles) == 2:
        #     vertex.harbor = True
        if len(vertex.adjacent_roads) == 2:
            vertex.harbor = True


# Constants
SCREEN_SIZE = (800, 800)
BACKGROUND_COLOR = (0, 0, 255)
TILE_COLOR = (154, 205, 50)
ROAD_COLOR = (0, 0, 0)
CENTER = TileVertex(400, 400)  # Center of the screen
SIZE = 80  # Adjusted for better visualization in the Pygame window

# Screen setup
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption('Hexagonal Grid Visualization')

# Generate board
centers, vertices = generate_hex_board(CENTER, SIZE)
generate_harbors(centers, vertices)

pygame.init()



color_map = {
    'ore': (129, 128, 128),
    'wood': (34, 139, 34),
    'brick': (178, 34, 34),
    'wheat': (218, 165, 32),
    'sheep': (154, 205, 50)
}

def draw_hexagon(surface, fill_color, outline_color, center, size):
    vertices = [hex_corner(center, size, i) for i in range(6)]
    pygame.draw.polygon(surface, fill_color, vertices)
    pygame.draw.polygon(surface, outline_color, vertices, 2)

def draw_grid():
    screen.fill(BACKGROUND_COLOR)
    
    for center in centers:
        draw_hexagon(screen, TILE_COLOR, ROAD_COLOR, center, SIZE)
    
    for vertex in vertices:
        if vertex.harbor:
            pygame.draw.circle(screen, (255, 255, 255), (int(vertex.x), int(vertex.y)), 7)
        else:
            pygame.draw.circle(screen, ROAD_COLOR, (int(vertex.x), int(vertex.y)), 7)
        for adj in vertex.adjacent_roads:
            pygame.draw.line(screen, ROAD_COLOR, (vertex.x, vertex.y), (adj.x, adj.y), 5)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_grid()
    pygame.display.flip()

pygame.quit()



# https://www.redblobgames.com/grids/hexagons/ Very useful source for hexagons



import math
import matplotlib.pyplot as plt


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


# Constants
CENTER = TileVertex(0, 0)
SIZE = 10 

# Generate board
centers, vertices = generate_hex_board(CENTER, SIZE)

# Plotting for visualization
plt.figure(figsize=(8, 8))
for vertex in vertices:
    plt.scatter(vertex.x, vertex.y, c='blue')  # plot vertices
    for adj in vertex.adjacent_tiles:
        plt.plot([vertex.x, adj.x], [vertex.y, adj.y], 'k-', color='blue') 
    for adj in vertex.adjacent_roads:
        plt.plot([vertex.x, adj.x], [vertex.y, adj.y], 'k-', color='red')   
for center in centers:
    plt.scatter(center.x, center.y, c='red') # plot centers
    for adj in center.adjacent_tiles:
        plt.plot([center.x, adj.x], [center.y, adj.y], 'k-')  
plt.gca().set_aspect('equal', adjustable='box')
plt.grid(True)
plt.show()


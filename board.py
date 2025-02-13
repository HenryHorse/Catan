# https://www.redblobgames.com/grids/hexagons/ Very useful source for hexagons

import math
import random

from models import TileVertex, RoadVertex, DrawingPoint


# Function to get a hexagon corner (6 possible)
# This is some semi-complicated math, but was thankfully figured out by RedBlobGames already
def hex_corner(center, size, corner):
    angle_deg = 60 * corner - 30
    angle_rad = math.pi / 180 * angle_deg
    return center.x + size * math.cos(angle_rad), center.y + size * math.sin(angle_rad)


def generate_hex_board(center, size):
    hex_centers = [center]
    vertex_positions = []
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
            center.add_adjacent_road(visited_verts[rounded_hc])


            if (last is not None):
                visited_verts[rounded_hc].add_adjacent_road(last)
                last.add_adjacent_road(visited_verts[rounded_hc])
            last = visited_verts[rounded_hc]
            if visited_verts[rounded_hc] not in vertex_positions:
                vertex_positions.append(visited_verts[rounded_hc])
        hc = hex_corner(center, size, 0)
        rounded_hc = (round(hc[0]), round(hc[1]))
        last.add_adjacent_road(visited_verts[rounded_hc])
        visited_verts[rounded_hc].add_adjacent_road(last)

    return hex_centers, vertex_positions


def choose_harbors(vertices):
    harbor_types = ['3:1 any'] * 4 + ['2:1 ore', '2:1 wood', '2:1 brick', '2:1 grain', '2:1 sheep']
    dist_list = [0, 4, 3, 3, 4, 3, 3, 4, 3]
    potential_harbor_vertices = []
    count = 1
    for vertex in vertices:
        if len(vertex.adjacent_tiles) == 2 or len(vertex.adjacent_roads) == 2:
            potential_harbor_vertices.append(vertex)
            vertex.order = count
            count += 1

    order_verts = [1, 6, 5, 4, 8, 7, 10, 9, 11, 12, 13, 14, 16, 15, 18, 17, 21, 20, 19, 23, 22, 26, 25, 24, 28, 27, 30, 29, 3, 2]
    index_to_vertex = {vertex.order: vertex for vertex in vertices}
    potential_harbor_vertices = [index_to_vertex[idx] for idx in order_verts if idx in index_to_vertex]

    random_start = random.randint(0, len(potential_harbor_vertices) - 1)
    potential_harbor_vertices = potential_harbor_vertices[random_start:] + potential_harbor_vertices[:random_start]

    current_index = random_start
    for dist in dist_list:
        harbor_type = random.choice(harbor_types)
        current_index = (dist + current_index) % (len(potential_harbor_vertices))
        next_index = (current_index + 1) % (len(potential_harbor_vertices))

        current_vertex = potential_harbor_vertices[current_index]
        next_vertex = potential_harbor_vertices[next_index]
        current_vertex.harbor = True
        current_vertex.harbor_type = harbor_type
        next_vertex.harbor = True
        next_vertex.harbor_type = harbor_type

        harbor_types.remove(harbor_type)


def initialize_tiles(centers):
    resources = ['wood', 'grain', 'sheep', 'ore', 'brick', 'desert']
    resource_distribution = {
        'wood': 4,
        'grain': 4,
        'sheep': 4,
        'ore': 3,
        'brick': 3,
        'desert': 1
    }

    numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

    random.shuffle(centers)
    for center in centers:
        if resource_distribution['desert'] > 0:
            center.resource = 'desert'
            center.number = None
            resource_distribution['desert'] -= 1
        else:
            resource = random.choices(resources[:-1], weights=[resource_distribution[r] for r in resources[:-1]])[0]
            center.resource = resource
            resource_distribution[resource] -= 1
            if numbers:
                center.number = numbers.pop()

    return centers



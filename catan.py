


# https://www.redblobgames.com/grids/hexagons/ Very useful source for hexagons



import math
import pygame
from diceroll import *
from game import *

class TileVertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.adjacent_roads = []
        self.adjacent_tiles = []
        self.resource = None
        self.number = None

    def add_adjacent_tile(self, tile_vertex):
        if tile_vertex not in self.adjacent_tiles:
            self.adjacent_tiles.append(tile_vertex)

    def add_adjacent_road(self, road_vertex):
        if road_vertex not in self.adjacent_roads:
            self.adjacent_roads.append(road_vertex)

    def __repr__(self):
        return "Tile Vert: (" + str(self.x) + "," + str(self.y) + ")"

class RoadVertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.adjacent_roads = []
        self.adjacent_tiles = []
        self.harbor = False
        self.harbor_type = None
        self.order = None

    def add_adjacent_tile(self, tile_vertex):
        if tile_vertex not in self.adjacent_tiles:
            self.adjacent_tiles.append(tile_vertex)

    def add_adjacent_road(self, road_vertex):
        if road_vertex not in self.adjacent_roads:
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

        

def initialize_game():
    centers, vertices = generate_hex_board(CENTER, SIZE)
    choose_harbors(vertices)
    initialize_tiles(centers)
    return centers, vertices

    


# Constants
SCREEN_SIZE = (800, 800)
BACKGROUND_COLOR = (0, 160, 255)
TILE_COLOR = (154, 205, 50)
ROAD_COLOR = (0, 0, 0)
CENTER = TileVertex(400, 400)  # Center of the screen
SIZE = 80  # Adjusted for better visualization in the Pygame window

# Screen setup
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption('Hexagonal Grid Visualization')


pygame.init()
pygame.font.init()

tile_font = pygame.font.SysFont('Arial', 24)
harbor_font = pygame.font.SysFont('Arial', 17)



color_map = {
    'ore': (129, 128, 128),
    'wood': (34, 139, 34),
    'brick': (178, 34, 34),
    'grain': (220, 165, 32),
    'sheep': (154, 205, 50),
    'desert': (255, 215, 90),
    'red': (255, 0, 0),
    'blue': (0, 0, 255),
    'white': (255, 255, 255),
    'orange': (255, 102, 0),
    'robber': (102, 51, 0)
}

def draw_hexagon(surface, fill_color, outline_color, center, size):
    vertices = [hex_corner(center, size, i) for i in range(6)]
    pygame.draw.polygon(surface, fill_color, vertices)
    pygame.draw.polygon(surface, outline_color, vertices, 2)

def draw_grid(centers, vertices):
    screen.fill(BACKGROUND_COLOR)

    for center in centers:
        draw_hexagon(screen, color_map[center.resource], ROAD_COLOR, center, SIZE)
        if (center.number):
            text_surface = tile_font.render(str(center.number), True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(center.x, center.y))
            screen.blit(text_surface, text_rect)
    
    for vertex in vertices:
        if vertex.harbor:
            harbor_text = harbor_font.render(vertex.harbor_type, True, (255, 255, 255))
            text_rect = harbor_text.get_rect(center=(int(vertex.x), int(vertex.y)))
            pygame.draw.rect(screen, (101, 67, 33), text_rect.inflate(2, 2))
            screen.blit(harbor_text, text_rect)
            
        else:
            pygame.draw.circle(screen, ROAD_COLOR, (int(vertex.x), int(vertex.y)), 4)

def draw_players(players):
    for player in players:
        for settlement in player.settlements:
            settlement_vertex = settlement.location
            pygame.draw.circle(screen, color_map[player.color], (int(settlement_vertex.x), int(settlement_vertex.y)), 10)
        for city in player.cities:
            city_vertex = city.location
            pygame.draw.circle(screen, color_map[player.color], (int(city_vertex.x), int(city_vertex.y)), 15)
        for road in player.roads:
            rv1 = road.rv1
            rv2 = road.rv2
            pygame.draw.line(screen, color_map[player.color], (int(rv1.x), int(rv1.y)), (int(rv2.x), int(rv2.y)), 3)
            

def draw_robber(game):
    pygame.draw.circle(screen, color_map['robber'], (game.robber.x, game.robber.y), 12)


game = None
players = []
current_player_index = None
winner = None
centers = []
vertices = []

def start():
    global game, players, current_player_index, winner, centers, vertices
    centers, vertices = initialize_game()
    print("--------initializing games and players--------")
    game = Game()
    game.initialize_game(centers, vertices)

    player_red = Player('red')
    game.add_player(player_red)
    player_red.initialize_settlements_roads(game)

    player_blue = Player('blue')
    game.add_player(player_blue)
    player_blue.initialize_settlements_roads(game)

    player_white = Player('white')    
    game.add_player(player_white)
    player_white.initialize_settlements_roads(game)

    player_orange = Player('orange')
    game.add_player(player_orange)
    player_orange.initialize_settlements_roads(game)

    winner = None
    current_player_index = 0
    players = [player_red, player_blue, player_white, player_orange]
    draw_players(players)

def main():
    global game, players, current_player_index, winner, centers, vertices
    start()
    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    start()
                if event.key == pygame.K_SPACE and winner is None:
                    current_player = players[current_player_index]
                    print(f"--------{current_player.color} takes turn--------")
                    print(current_player.resources)
                    if turn(current_player, game):
                        winner = current_player
                    else:
                        current_player_index = (current_player_index + 1) % len(players)
                    if winner is not None:
                        print(f"The winner is {winner.color}")
                if event.key == pygame.K_x:
                    while winner is None:
                        current_player = players[current_player_index]
                        print(f"--------{current_player.color} takes turn--------")
                        print(current_player.resources)
                        if turn(current_player, game):
                            winner = current_player
                        else:
                            current_player_index = (current_player_index + 1) % len(players)
                        if winner is not None:
                            print(f"The winner is {winner.color}")


        draw_grid(centers, vertices)
        draw_players(players)
        draw_robber(game)
        pygame.display.flip()

    pygame.quit()

    

    # while not turn(player_red, game):
    #     pass
    # print("Red player wins!")

    # test getting resources
    # res = key, val = random.choice(list(game.harbors.items()))
    # player_blue.settlements.append((key))

if __name__ == '__main__':
    main()
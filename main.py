from game import *
from models import TileVertex
import pygame
import argparse
import sys

from player import Player
from turn import *
from board import *


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

def start(num_players):
    global game, players, current_player_index, winner, centers, vertices
    centers, vertices = initialize_game()
    print("--------initializing games and players--------")
    game = Game()
    game.initialize_game(centers, vertices)

    player_colors = ['red', 'blue', 'white', 'orange']
    players = []

    for i in range(num_players):  # Only create the requested number of players
        player = Player(player_colors[i])
        game.add_player(player)
        player.initialize_settlements_roads(game)
        players.append(player)

    winner = None
    current_player_index = 0
    draw_players(players)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Hexagonal board game simulation")
    parser.add_argument("--disable-trading", action="store_true", help="Disable trading between players")
    parser.add_argument("--players", type=int, choices=[2,3,4], default=4, help="Number of players (2-4)")
    return parser.parse_args()

def main():
    global game, players, current_player_index, winner, centers, vertices, disable_trading

    args = parse_arguments()
    num_players = args.players
    disable_trading = args.disable_trading

    start(num_players)
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
                    if turn(current_player, game, disable_trading):
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
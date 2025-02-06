from game import *
from models import TileVertex
import pygame
import argparse
import sys

from player import Player
from turn import *
from board import *

from collections import Counter


def initialize_game():
    centers, vertices = generate_hex_board(CENTER, SIZE)
    choose_harbors(vertices)
    initialize_tiles(centers)
    return centers, vertices


# Constants
BOARD_AREA_WIDTH = 800
BOARD_AREA_HEIGHT = 800
STATS_AREA_WIDTH = 220
SCREEN_SIZE = (BOARD_AREA_WIDTH + STATS_AREA_WIDTH, BOARD_AREA_HEIGHT)

BACKGROUND_COLOR = (0, 160, 255)
BOARD_BG_COLOR = (0, 160, 255)
STATS_BG_COLOR = (230, 230, 230)
TILE_COLOR = (154, 205, 50)
ROAD_COLOR = (0, 0, 0)

# Board center and size for hexagons
CENTER = TileVertex(BOARD_AREA_WIDTH // 2, BOARD_AREA_HEIGHT // 2)
SIZE = 80

# Screen setup
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption('Hexagonal Grid Visualization')


pygame.init()
pygame.font.init()

tile_font = pygame.font.SysFont('Arial', 24)
harbor_font = pygame.font.SysFont('Arial', 17)
stats_title_font = pygame.font.SysFont('Arial', 18)
stats_font = pygame.font.SysFont('Arial', 14)

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


def draw_turn_info(turn_number, current_player):
    """Draw turn number and current player's turn in the top left of the board area."""
    info_text = f"Turn {turn_number} - {current_player.color.capitalize()}'s Turn"
    info_surface = stats_title_font.render(info_text, True, (0, 0, 0))
    screen.blit(info_surface, (10, 10))



def draw_player_stats(players):
    """Draw each player's stats in the right-side stats area with resources on the left
    and dev cards on the right. Also, show Longest Road and Largest Army statuses next to the title."""
    # stats background
    stats_rect = pygame.Rect(BOARD_AREA_WIDTH, 0, STATS_AREA_WIDTH, BOARD_AREA_HEIGHT)
    pygame.draw.rect(screen, STATS_BG_COLOR, stats_rect)
    
    num_players = len(players)
    panel_height = BOARD_AREA_HEIGHT // num_players
    panel_padding = 10

    for idx, player in enumerate(players):
        # stat panel position
        panel_x = BOARD_AREA_WIDTH
        panel_y = idx * panel_height
        panel_rect = pygame.Rect(panel_x, panel_y, STATS_AREA_WIDTH, panel_height)
        
        # panel border
        pygame.draw.rect(screen, color_map[player.color], panel_rect, 2)
        
        # Set starting coordinates inside the panel for text
        header_x = panel_x + panel_padding
        header_y = panel_y + panel_padding
        
        # player
        header_text = f"{player.color.capitalize()} Player"
        header_surface = stats_title_font.render(header_text, True, color_map[player.color])
        screen.blit(header_surface, (header_x, header_y))
        
        # longest road and longest army, NOT IMPLEMENTED YET
        lr_has = getattr(player, 'has_longest_road', False)
        la_has = getattr(player, 'has_largest_army', False)
        lr_color = (0, 255, 0) if lr_has else (255, 0, 0)
        la_color = (0, 255, 0) if la_has else (255, 0, 0)
        
        # LR and LA statuses
        status_x = header_x + header_surface.get_width() + 40
        lr_surface = stats_font.render("Longest Road", True, lr_color)
        screen.blit(lr_surface, (status_x, header_y))
        la_surface = stats_font.render("Largest Army", True, la_color)
        screen.blit(la_surface, (status_x, header_y + 20))
        
        header_y += header_surface.get_height() + 5
        
        # victory points
        vp_text = f"VP: {player.victory_points}"
        vp_surface = stats_font.render(vp_text, True, (0, 0, 0))
        screen.blit(vp_surface, (header_x, header_y))
        header_y += vp_surface.get_height() + 10
        
        left_col_x = panel_x + panel_padding
        right_col_x = panel_x + STATS_AREA_WIDTH // 2 + panel_padding
        col_y = header_y
        
        # Left Column: Resources
        res_header = stats_font.render("Resources:", True, (0, 0, 0))
        screen.blit(res_header, (left_col_x, col_y))
        col_y += res_header.get_height() + 2
        
        for res, count in player.resources.items():
            res_text = f"{res.capitalize()}: {count}"
            res_surface = stats_font.render(res_text, True, (0, 0, 0))
            screen.blit(res_surface, (left_col_x + 5, col_y))
            col_y += res_surface.get_height() + 2
        
        # Right Column: Development Cards
        dev_y = header_y
        dev_header = stats_font.render("Dev Cards:", True, (0, 0, 0))
        screen.blit(dev_header, (right_col_x, dev_y))
        dev_y += dev_header.get_height() + 2
        
        # Count development cards for the player
        dev_counts = Counter(card.card_type for card in player.dev_cards)
        if dev_counts:
            for card_type, count in dev_counts.items():
                card_text = f"{card_type.capitalize()}: {count}"
                card_surface = stats_font.render(card_text, True, (0, 0, 0))
                screen.blit(card_surface, (right_col_x + 5, dev_y))
                dev_y += card_surface.get_height() + 2
        else:
            none_surface = stats_font.render("None", True, (0, 0, 0))
            screen.blit(none_surface, (right_col_x + 5, dev_y))
            dev_y += none_surface.get_height() + 2


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
    turn_num = 1
    current_player = players[current_player_index]
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    turn_num = 1
                    start(num_players)
                if event.key == pygame.K_SPACE and winner is None:
                    current_player = players[current_player_index]
                    pygame.display.flip()
                    print(f"--------{current_player.color} takes turn {turn_num} --------")
                    print(current_player.resources)
                    if turn(current_player, game, disable_trading):
                        winner = current_player
                    else:
                        current_player_index = (current_player_index + 1) % len(players)
                        turn_num += 1
                        print(f"--------{current_player.color} ends turn --------")
                    if winner is not None:
                        print(f"The winner is {winner.color}")
                if event.key == pygame.K_x:
                    while winner is None:
                        current_player = players[current_player_index]
                        print(f"--------{current_player.color} takes turn {turn_num} --------")
                        print(current_player.resources)
                        if turn(current_player, game, disable_trading):
                            winner = current_player
                        else:
                            current_player_index = (current_player_index + 1) % len(players)
                            turn_num += 1
                            print(f"--------{current_player.color} ends turn --------")
                        if winner is not None:
                            print(f"The winner is {winner.color}")


        draw_grid(centers, vertices)
        draw_players(players)
        draw_robber(game)
        draw_turn_info(turn_num, players[current_player_index])
        draw_player_stats(players)
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
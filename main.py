from game import *
from models import TileVertex
import pygame
import argparse
import sys

from player import Player
from turn import *
from board import *

from collections import Counter

# ---------------- Helper functions ----------------


def get_vertex_at_pos(pos, vertices, threshold=5):
    """Return a vertex from 'vertices' if the click is within a threshold distance."""
    for vertex in vertices:
        if abs(vertex.x - pos[0]) < threshold and abs(vertex.y - pos[1]) < threshold:
            return vertex
    return None

def get_road_at_pos(mouse_pos, roads, threshold=8):
    for v1, v2 in roads:
        if is_point_near_line(mouse_pos, (v1.x, v1.y), (v2.x, v2.y), threshold):
            return v1, v2
    return None

def is_point_near_line(point, line_start, line_end, threshold):
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end

    line_length_squared = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if line_length_squared == 0:
        return False  # Line is a single point

    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_squared))
    closest_x = x1 + t * (x2 - x1)
    closest_y = y1 + t * (y2 - y1)

    return (px - closest_x) ** 2 + (py - closest_y) ** 2 < threshold ** 2


def initialize_game():
    centers, vertices = generate_hex_board(CENTER, SIZE)
    choose_harbors(vertices)
    initialize_tiles(centers)

    roads = []
    for road_vertex in vertices:
        for neighbor in road_vertex.adjacent_roads:
            road = tuple(sorted((road_vertex, neighbor), key=lambda v: (v.x, v.y)))
            roads.append(road)

    return centers, vertices, roads

def render_game(centers, vertices, roads, players, game, turn_number, current_player, hover_vertex=None, hover_road=None):
    screen.fill(BACKGROUND_COLOR)
    draw_grid(centers, vertices, roads, hover_vertex, hover_road)
    draw_players(players)
    draw_robber(game)
    draw_turn_info(turn_number, current_player)
    draw_player_stats(players)
    draw_action_bar(screen, active=current_player.is_human)
    pygame.display.flip()



pygame.init()
pygame.font.init()

# Screen Size Related
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

ACTION_AREA_HEIGHT = int(SCREEN_HEIGHT * 0.12)
BOARD_AREA_WIDTH = int(SCREEN_WIDTH * 0.75)
BOARD_AREA_HEIGHT = int(SCREEN_HEIGHT * 0.85) - ACTION_AREA_HEIGHT
STATS_AREA_WIDTH = int(SCREEN_WIDTH * 0.25)
STATS_AREA_HEIGHT = BOARD_AREA_HEIGHT + ACTION_AREA_HEIGHT
SCREEN_SIZE = (BOARD_AREA_WIDTH + STATS_AREA_WIDTH, BOARD_AREA_HEIGHT + ACTION_AREA_HEIGHT)

BACKGROUND_COLOR = (0, 160, 255)
BOARD_BG_COLOR = (0, 160, 255)
STATS_BG_COLOR = (230, 230, 230)
TILE_COLOR = (154, 205, 50)
ROAD_COLOR = (0, 0, 0)

# Board center and size for hexagons
CENTER = TileVertex(BOARD_AREA_WIDTH // 2, BOARD_AREA_HEIGHT // 2)
SIZE = min(BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT) // 10

# Screen setup
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption('Settlers of Catan Board')


tile_font = pygame.font.SysFont('Arial', int(SCREEN_HEIGHT * 0.03))
harbor_font = pygame.font.SysFont('Arial', int(SCREEN_HEIGHT * 0.015))
stats_title_font = pygame.font.SysFont('Arial', int(SCREEN_HEIGHT * 0.022))
stats_font = pygame.font.SysFont('Arial', int(SCREEN_HEIGHT * 0.018))

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



def draw_grid(centers, vertices, roads, hover_vertex=None, hover_road=None):
    screen.fill(BACKGROUND_COLOR)

    for center in centers:
        draw_hexagon(screen, color_map[center.resource], ROAD_COLOR, center, SIZE)
        if (center.number):
            text_surface = tile_font.render(str(center.number), True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(center.x, center.y))
            screen.blit(text_surface, text_rect)

    for v1, v2 in roads:
        road_thickness = 5 if hover_road and (v1, v2) == hover_road else 2
        if (v1, v2) == hover_road:
            pygame.draw.line(screen, ROAD_COLOR, (int(v1.x), int(v1.y)), (int(v2.x), int(v2.y)), road_thickness + 4)
            pygame.draw.line(screen, (255, 255, 255), (int(v1.x), int(v1.y)), (int(v2.x), int(v2.y)), road_thickness - 2)
        else:
            pygame.draw.line(screen, ROAD_COLOR, (int(v1.x), int(v1.y)), (int(v2.x), int(v2.y)), road_thickness)

    for vertex in vertices:
        if vertex.harbor:
            harbor_text = harbor_font.render(vertex.harbor_type, True, (255, 255, 255))
            text_rect = harbor_text.get_rect(center=(int(vertex.x), int(vertex.y)))
            pygame.draw.rect(screen, (101, 67, 33), text_rect.inflate(2, 2))
            screen.blit(harbor_text, text_rect)
        else:
            radius = 8 if vertex == hover_vertex else 4
            if vertex == hover_vertex:
                pygame.draw.circle(screen, ROAD_COLOR, (int(vertex.x), int(vertex.y)), radius + 4)
                pygame.draw.circle(screen, (255, 255, 255), (int(vertex.x), int(vertex.y)), radius)
            else:
                pygame.draw.circle(screen, ROAD_COLOR, (int(vertex.x), int(vertex.y)), radius)

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
    stats_rect = pygame.Rect(BOARD_AREA_WIDTH, 0, STATS_AREA_WIDTH, STATS_AREA_HEIGHT)
    pygame.draw.rect(screen, STATS_BG_COLOR, stats_rect)
    
    num_players = len(players)
    panel_height = STATS_AREA_HEIGHT // num_players
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
        
        # VP
        vp_text = f"VP: {player.victory_points}"
        vp_surface = stats_font.render(vp_text, True, (0, 0, 0))
        screen.blit(vp_surface, (header_x, header_y))
        header_y += vp_surface.get_height() + 10
        
        left_col_x = panel_x + panel_padding
        right_col_x = panel_x + STATS_AREA_WIDTH // 2 + panel_padding
        col_y = header_y
        
        # Resources
        res_header = stats_font.render("Resources:", True, (0, 0, 0))
        screen.blit(res_header, (left_col_x, col_y))
        col_y += res_header.get_height() + 2
        
        for res, count in player.resources.items():
            res_text = f"{res.capitalize()}: {count}"
            res_surface = stats_font.render(res_text, True, (0, 0, 0))
            screen.blit(res_surface, (left_col_x + 5, col_y))
            col_y += res_surface.get_height() + 2
        
        # Development Cards
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

def draw_action_bar(screen, active=True):
    """
    Draw only the Build Road and End Turn buttons in the action bar.
    Returns a dict mapping button labels to their pygame.Rect.
    """
    bar_y = BOARD_AREA_HEIGHT
    bar_rect = pygame.Rect(0, bar_y, BOARD_AREA_WIDTH, ACTION_AREA_HEIGHT)
    bg_color = (200, 200, 200) if active else (150, 150, 150)
    pygame.draw.rect(screen, bg_color, bar_rect)

    button_width = 180
    button_height = 50
    button_y = bar_y + (ACTION_AREA_HEIGHT // 3)
    # Only two buttons for human actions.
    buttons = {
        "Build Road": pygame.Rect(50, button_y, button_width, button_height),
        "End Turn": pygame.Rect(BOARD_AREA_WIDTH - button_width - 50, button_y, button_width, button_height)
    }

    for label, rect in buttons.items():
        border_color = (0, 0, 0) if active else (100, 100, 100)
        pygame.draw.rect(screen, border_color, rect, 2)
        text_color = (0, 0, 0) if active else (100, 100, 100)
        text_surface = stats_title_font.render(label, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    return buttons

game = None
players = []
current_player_index = None
winner = None
centers = []
vertices = []

def start(num_players, human_flag=False):
    centers, vertices, roads = initialize_game()
    game = Game()
    game.initialize_game(centers, vertices)

    player_colors = ['red', 'blue', 'white', 'orange']
    players = []
    for i in range(num_players):
        player = Player(player_colors[i])
        if human_flag and i == 0:
            player.is_human = True
        else:
            player.is_human = False
        game.add_player(player)
        players.append(player)

    render_game(centers, vertices, roads, players, game, turn_number=0,current_player=players[0])

    for player in players:
        if player.is_human:
            human_initialize_settlement_and_road(player, centers, vertices, roads, players, game)
            print(player.settlements)
            print(player.roads)
        else:
            player.initialize_settlement_and_road(game)
            render_game(centers, vertices, roads, players, game, turn_number=0, current_player=player)
    for player in players:
        if player.is_human:
            settlement_loc = human_initialize_settlement_and_road(player, centers, vertices, roads, players, game)
            for tile in settlement_loc.adjacent_tiles:
                player.add_resource(tile.resource, 1)
        else:
            settlement_loc = player.initialize_settlement_and_road(game)
            render_game(centers, vertices, roads, players, game, turn_number=0,current_player=player)
            # for all adjacent tiles to the settlement 2, add resource for player
            for tile in settlement_loc.adjacent_tiles:
                player.add_resource(tile.resource, 1)


    return centers, vertices, roads, game, players


def parse_arguments():
    parser = argparse.ArgumentParser(description="Hexagonal board game simulation")
    parser.add_argument("--disable-trading", action="store_true", help="Disable trading between players")
    parser.add_argument("--players", type=int, choices=[2,3,4], default=4, help="Number of players (2-4)")
    parser.add_argument("--human", action="store_true", help="Set first player (red) as human")
    return parser.parse_args()

def main():
    args = parse_arguments()
    num_players = args.players
    disable_trading = args.disable_trading
    human = args.human

    while True:
        centers, vertices, roads, game, players = start(num_players, human)
        winner = None
        turn_num = 1
        current_player_index = 0

        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            hover_vertex = get_vertex_at_pos(mouse_pos, vertices)
            hover_road = None if hover_vertex else get_road_at_pos(mouse_pos, roads)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        running = False
                        break
                    if event.key == pygame.K_SPACE and winner is None:
                        current_player = players[current_player_index]
                        print(f"--------{current_player.color} takes turn {turn_num} --------")
                        print(current_player.resources)
                        if turn(current_player, game, disable_trading):
                            winner = current_player
                        else:
                            current_player_index = (current_player_index + 1) % len(players)
                            turn_num += 1
                            print(f"--------{current_player.color} ends turn --------")
                        if winner:
                            print(f"The winner is {winner.color}")

                    # TODO Fix for human player
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

            current_player = players[current_player_index]
            render_game(centers, vertices, roads, players, game, turn_num, current_player, hover_vertex, hover_road)

def human_initialize_settlement_and_road(player, centers, vertices, roads, players, game):
    running = True
    settlement_loc = None
    road_loc = None

    while running:
        mouse_pos = pygame.mouse.get_pos()
        hover_vertex = get_vertex_at_pos(mouse_pos, game.road_vertices)
        hover_road = None if hover_vertex else get_road_at_pos(mouse_pos, roads)

        render_game(centers, vertices, roads, players, game, turn_number=0, current_player=player,
                    hover_vertex=hover_vertex, hover_road=hover_road)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if settlement_loc is None:
                    settlement_loc = get_vertex_at_pos(mouse_pos, game.road_vertices)
                    if settlement_loc:
                        if game.is_valid_initial_settlement_location(settlement_loc):
                            player.build_settlement(settlement_loc)
                            player.reset_resources()
                            game.occupy_tile(settlement_loc)
                            print(f"{player.color} built settlement at {(settlement_loc.x, settlement_loc.y)}")
                            render_game(centers, vertices, roads, players, game, turn_number=0, current_player=player)
                        else:
                            settlement_loc = None
                elif road_loc is None:
                    road_loc = get_road_at_pos(mouse_pos, roads)
                    if road_loc:
                        if (road_loc[0] == settlement_loc or road_loc[1] == settlement_loc) and game.is_valid_road_location(road_loc[0], road_loc[1], player):
                            player.build_road(road_loc[0], road_loc[1])
                            player.reset_resources()
                            game.occupy_road(road_loc[0], road_loc[1])
                            print(f"{player.color} built road from {(road_loc[0].x, road_loc[0].y)} to {(road_loc[1].x, road_loc[1].y)}")
                            render_game(centers, vertices, roads, players, game, turn_number=0, current_player=player)
                            running = False
                        else:
                            road_loc = None


    print("break out")
    return settlement_loc






if __name__ == '__main__':
    main()
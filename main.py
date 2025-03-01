from collections import Counter

import pygame
import argparse

from catan.board import Board
from catan.player import Player
from catan.agent.random import RandomAgent
from catan.game import Game, PlayerAgent
from catan.util import Point

# Constants
BACKGROUND_COLOR = (0, 160, 255)
BOARD_BG_COLOR = (0, 160, 255)
STATS_BG_COLOR = (230, 230, 230)
TILE_COLOR = (154, 205, 50)
ROAD_COLOR = (0, 0, 0)

COLOR_MAP = {
    'Resource.ORE': (129, 128, 128),
    'Resource.WOOD': (34, 139, 34),
    'Resource.BRICK': (178, 34, 34),
    'Resource.GRAIN': (220, 165, 32),
    'Resource.SHEEP': (154, 205, 50),
    'desert': (255, 215, 90),
    'red': (255, 0, 0),
    'blue': (0, 0, 255),
    'white': (255, 255, 255),
    'orange': (255, 102, 0),
    'robber': (102, 51, 0)
}

def draw_tile(
        surface: pygame.Surface,
        fill_color: tuple[int, int, int],
        outline_color: tuple[int, int, int],
        vertices: list[Point]):
    number_pairs = [point.to_int_tuple() for point in vertices]
    pygame.draw.polygon(surface, fill_color, number_pairs)
    pygame.draw.polygon(surface, outline_color, number_pairs, 2)

def draw_grid(
        screen: pygame.Surface,
        tile_font: pygame.font.Font,
        harbor_font: pygame.font.Font,
        board: Board,
        hexagon_size: float,
        displacement: Point = Point(0, 0)):
    
    screen.fill(BACKGROUND_COLOR)

    for tile in board.tiles.values():
        center = tile.get_screen_position(hexagon_size) + displacement
        vertices = [rv.get_screen_position(hexagon_size) + displacement for rv in tile.adjacent_road_vertices]
        color = COLOR_MAP[str(tile.resource)] if tile.resource else COLOR_MAP['desert']
        draw_tile(screen, color, ROAD_COLOR, vertices)
        if tile.number:
            text_surface = tile_font.render(str(tile.number), True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(center.to_int_tuple()))
            screen.blit(text_surface, text_rect)
    
    for road_vertex in board.road_vertices:
        pos = road_vertex.get_screen_position(hexagon_size) + displacement
        if road_vertex.harbor is not None:
            harbor_text = harbor_font.render(str(road_vertex.harbor), True, (255, 255, 255))
            text_rect = harbor_text.get_rect(center=pos.to_int_tuple())
            pygame.draw.rect(screen, (101, 67, 33), text_rect.inflate(2, 2))
            screen.blit(harbor_text, text_rect)
        else:
            pygame.draw.circle(screen, ROAD_COLOR, pos.to_int_tuple(), 4)

def draw_players(
        screen: pygame.Surface,
        players: list[Player],
        hexagon_size: float,
        displacement: Point = Point(0, 0)):
    for player in players:
        for settlement in player.settlements:
            pos = settlement.get_screen_position(hexagon_size) + displacement
            pygame.draw.circle(screen, player.color, pos.to_int_tuple(), 10)
        for city in player.cities:
            pos = city.get_screen_position(hexagon_size) + displacement
            pygame.draw.circle(screen, player.color, pos.to_int_tuple(), 15)
        for road in player.roads:
            start_pos = road.endpoints[0].get_screen_position(hexagon_size) + displacement
            end_pos = road.endpoints[1].get_screen_position(hexagon_size) + displacement
            pygame.draw.line(screen, player.color, start_pos.to_int_tuple(), end_pos.to_int_tuple(), 3)
            

def draw_robber(
        screen: pygame.Surface,
        board: Board,
        hexagon_size: float,
        displacement: Point = Point(0, 0)):
    if (robber_tile := board.get_robber_tile()) is not None:
        pos = robber_tile.get_screen_position(hexagon_size) + displacement
        pygame.draw.circle(screen, COLOR_MAP['robber'], pos.to_int_tuple(), 12)


def draw_turn_info(
        screen: pygame.Surface,
        stats_title_font: pygame.font.Font,
        game: Game):
    """Draw turn number and current player's turn in the top left of the board area."""
    info_text = f"Turn {game.main_turns_elapsed + 1} - Player {game.player_turn_index + 1}'s Turn"
    info_surface = stats_title_font.render(info_text, True, (0, 0, 0))
    screen.blit(info_surface, (10, 10))

def draw_player_stats(
        screen: pygame.Surface,
        stats_rect: pygame.Rect,
        stats_title_font: pygame.font.Font,
        stats_font: pygame.font.Font,
        players: list[Player]):
    """Draw each player's stats in the right-side stats area with resources on the left
    and dev cards on the right. Also, show Longest Road and Largest Army statuses next to the title."""
    # stats background
    pygame.draw.rect(screen, STATS_BG_COLOR, stats_rect)
    
    num_players = len(players)
    panel_height = stats_rect.height // num_players
    panel_padding = 10

    for idx, player in enumerate(players):
        # stat panel position
        panel_x = stats_rect.left
        panel_y = idx * panel_height
        panel_rect = pygame.Rect(panel_x, panel_y, stats_rect.width, panel_height)
        
        # panel border
        pygame.draw.rect(screen, player.color, panel_rect, 2)
        
        # Set starting coordinates inside the panel for text
        header_x = panel_x + panel_padding
        header_y = panel_y + panel_padding
        
        # player
        header_text = f"Player {idx + 1}"
        header_surface = stats_title_font.render(header_text, True, player.color)
        screen.blit(header_surface, (header_x, header_y))
        
        # longest road and longest army, NOT IMPLEMENTED YET
        lr_has = player.has_longest_road
        la_has = player.has_largest_army
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
        right_col_x = panel_x + stats_rect.width // 2 + panel_padding
        col_y = header_y
        
        # Left Column: Resources
        res_header = stats_font.render("Resources:", True, (0, 0, 0))
        screen.blit(res_header, (left_col_x, col_y))
        col_y += res_header.get_height() + 2
        
        for res, count in player.resources.items():
            res_text = f"{res}: {count}"
            res_surface = stats_font.render(res_text, True, (0, 0, 0))
            screen.blit(res_surface, (left_col_x + 5, col_y))
            col_y += res_surface.get_height() + 2
        
        # Right Column: Development Cards
        dev_y = header_y
        dev_header = stats_font.render("Dev Cards:", True, (0, 0, 0))
        screen.blit(dev_header, (right_col_x, dev_y))
        dev_y += dev_header.get_height() + 2
        
        # Count development cards for the player
        dev_counts = Counter(str(card) for card in player.unplayed_dev_cards)
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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Settlers of Catan board visualizer")
    parser.add_argument("--board-size", type=int, default=3, help="Size of the board (default: 3)")
    # TODO: make this do something?
    parser.add_argument("--num-players", type=int, default=4, help="Number of players (default: 4)")
    return parser.parse_args()

def create_game(board_size: int) -> Game:
    board = Board(3)

    player_1 = Player(0, (255, 0, 0))
    agent_1 = RandomAgent(board, player_1)
    player_2 = Player(1, (0, 0, 255))
    agent_2 = RandomAgent(board, player_2)
    player_3 = Player(2, (255, 255, 255))
    agent_3 = RandomAgent(board, player_3)
    player_4 = Player(3, (255, 102, 0))
    agent_4 = RandomAgent(board, player_4)

    return Game(board, [
        PlayerAgent(player_1, agent_1),
        PlayerAgent(player_2, agent_2),
        PlayerAgent(player_3, agent_3),
        PlayerAgent(player_4, agent_4)])

def handle_event(event: pygame.event.Event, game: Game):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE and game.winning_player_index is None:
            print(f'-------- Player {game.player_turn_index + 1} takes turn {game.main_turns_elapsed + 1} --------')
            game.do_full_turn()
            if game.winning_player_index is not None:
                print(f"Player {game.winning_player_index + 1} wins!")
        elif event.key == pygame.K_x:
            while game.winning_player_index is None:
                print(f'-------- Player {game.player_turn_index + 1} takes turn {game.main_turns_elapsed + 1} --------')
                game.do_full_turn()
            print(f"Player {game.winning_player_index + 1} wins!")

def main():
    pygame.init()
    pygame.font.init()

    info = pygame.display.Info()
    SCREEN_WIDTH = info.current_w
    SCREEN_HEIGHT = info.current_h

    BOARD_AREA_WIDTH = int(SCREEN_WIDTH * 0.75)
    BOARD_AREA_HEIGHT = int(SCREEN_HEIGHT * 0.85)
    STATS_AREA_WIDTH = int(SCREEN_WIDTH * 0.25)
    SCREEN_SIZE = (BOARD_AREA_WIDTH + STATS_AREA_WIDTH, BOARD_AREA_HEIGHT)

    # Board center and size for hexagons
    HEXAGON_SIZE = min(BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT) // 10

    # Screen setup
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Settlers of Catan Board")

    tile_font = pygame.font.SysFont('Arial', int(SCREEN_HEIGHT * 0.03))
    harbor_font = pygame.font.SysFont('Arial', int(SCREEN_HEIGHT * 0.015))
    stats_title_font = pygame.font.SysFont('Arial', int(SCREEN_HEIGHT * 0.022))
    stats_font = pygame.font.SysFont('Arial', int(SCREEN_HEIGHT * 0.018))

    game = create_game(3)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # TODO: more elegant reset
                game = create_game(3)
            else:
                handle_event(event, game)
        
        players: list[Player] = [pa.player for pa in game.player_agents]
        grid_displacement = Point(BOARD_AREA_WIDTH // 2, BOARD_AREA_HEIGHT // 2)
        draw_grid(screen, tile_font, harbor_font, game.board, HEXAGON_SIZE, grid_displacement)
        draw_players(screen, players, HEXAGON_SIZE, grid_displacement)
        draw_robber(screen, game.board, HEXAGON_SIZE, grid_displacement)
        draw_turn_info(screen, stats_title_font, game)
        draw_player_stats(screen, pygame.Rect(BOARD_AREA_WIDTH, 0, STATS_AREA_WIDTH, SCREEN_HEIGHT), stats_title_font, stats_font, players)
        pygame.display.flip()
    
    pygame.quit()


if __name__ == '__main__':
    main()

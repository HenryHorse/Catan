from collections import Counter
from typing import Callable

import pygame

from catan.game import Game
from catan.util import Point
from catan.constants import *
from catan.serialization import BrickRepresentation

class CatanUI:
    game: Game | None
    game_generator: Callable[[], Game]
    screen: pygame.Surface | None

    screen_width: int
    screen_height: int

    board_area_width: int
    board_area_height: int
    stats_area_width: int
    screen_size: tuple[int, int]
    hexagon_size: int

    tile_font: pygame.font.Font
    harbor_font: pygame.font.Font
    stats_title_font: pygame.font.Font
    stats_font: pygame.font.Font

    def __init__(self, game_generator: Callable[[], Game], serialization: BrickRepresentation):
        self.game = None
        self.game_generator = game_generator
        self.screen = None
        self.serialization = serialization

    def draw_tile(
            self,
            fill_color: tuple[int, int, int],
            outline_color: tuple[int, int, int],
            vertices: list[Point]):
        number_pairs = [point.to_int_tuple() for point in vertices]
        pygame.draw.polygon(self.screen, fill_color, number_pairs)
        pygame.draw.polygon(self.screen, outline_color, number_pairs, 2)

    def draw_grid(self, displacement: Point = Point(0, 0)):
        self.screen.fill(BACKGROUND_COLOR)

        if self.screen is None or self.game is None:
            return

        for tile in self.game.board.tiles.values():
            center = tile.get_screen_position(self.hexagon_size) + displacement
            vertices = [rv.get_screen_position(self.hexagon_size) + displacement for rv in tile.adjacent_road_vertices]
            color = RESOURCE_COLORS[tile.resource.name] if tile.resource else DESERT_COLOR
            self.draw_tile(color, ROAD_COLOR, vertices)
            if tile.number:
                text_surface = self.tile_font.render(str(tile.number), True, WHITE)
                text_rect = text_surface.get_rect(center=(center.to_int_tuple()))
                self.screen.blit(text_surface, text_rect)
        
        for road_vertex in self.game.board.road_vertices:
            pos = road_vertex.get_screen_position(self.hexagon_size) + displacement
            if road_vertex.harbor is not None:
                harbor_text = self.harbor_font.render(str(road_vertex.harbor), True, WHITE)
                text_rect = harbor_text.get_rect(center=pos.to_int_tuple())
                pygame.draw.rect(self.screen, BROWN, text_rect.inflate(2, 2))
                self.screen.blit(harbor_text, text_rect)
            else:
                pygame.draw.circle(self.screen, ROAD_COLOR, pos.to_int_tuple(), 4)

    def draw_players(self, displacement: Point = Point(0, 0)):
        if self.screen is None or self.game is None:
            return
        
        for player_agent in self.game.player_agents:
            player = player_agent.player
            for settlement in player.settlements:
                pos = settlement.get_screen_position(self.hexagon_size) + displacement
                pygame.draw.circle(self.screen, player.color, pos.to_int_tuple(), 10)
            for city in player.cities:
                pos = city.get_screen_position(self.hexagon_size) + displacement
                pygame.draw.circle(self.screen, player.color, pos.to_int_tuple(), 15)
            for road in player.roads:
                start_pos = road.endpoints[0].get_screen_position(self.hexagon_size) + displacement
                end_pos = road.endpoints[1].get_screen_position(self.hexagon_size) + displacement
                pygame.draw.line(self.screen, player.color, start_pos.to_int_tuple(), end_pos.to_int_tuple(), 3)
                

    def draw_robber(self, displacement: Point = Point(0, 0)):
        if self.screen is None or self.game is None:
            return
        
        if (robber_tile := self.game.board.get_robber_tile()) is not None:
            pos = robber_tile.get_screen_position(self.hexagon_size) + displacement
            pygame.draw.circle(self.screen, BROWN, pos.to_int_tuple(), 12)


    def draw_turn_info(self):
        """Draw turn number and current player's turn in the top left of the board area."""
        if self.screen is None or self.game is None:
            return
        
        info_text = f"Turn {self.game.main_turns_elapsed + 1} - Player {self.game.player_turn_index + 1}'s Turn"
        info_surface = self.stats_title_font.render(info_text, True, BLACK)
        self.screen.blit(info_surface, (10, 10))

    def draw_player_stats(self, stats_rect: pygame.Rect):
        """Draw each player's stats in the right-side stats area with resources on the left
        and dev cards on the right. Also, show Longest Road and Largest Army statuses next
        to the title."""
        if self.screen is None or self.game is None:
            return
        
        # stats background
        pygame.draw.rect(self.screen, STATS_BG_COLOR, stats_rect)
        
        num_players = len(self.game.player_agents)
        panel_height = stats_rect.height // num_players
        panel_padding = 10

        for idx, player in enumerate(player_agent.player for player_agent in self.game.player_agents):
            # stat panel position
            panel_x = stats_rect.left
            panel_y = idx * panel_height
            panel_rect = pygame.Rect(panel_x, panel_y, stats_rect.width, panel_height)
            
            # panel border
            pygame.draw.rect(self.screen, player.color, panel_rect, 2)
            
            # Set starting coordinates inside the panel for text
            header_x = panel_x + panel_padding
            header_y = panel_y + panel_padding
            
            # player
            header_text = f"Player {idx + 1}"
            header_surface = self.stats_title_font.render(header_text, True, player.color)
            self.screen.blit(header_surface, (header_x, header_y))
            
            # longest road and longest army, NOT IMPLEMENTED YET
            lr_has = player.has_longest_road
            la_has = player.has_largest_army
            lr_color = GREEN if lr_has else RED
            la_color = GREEN if la_has else RED
            
            # LR and LA statuses
            status_x = header_x + header_surface.get_width() + 40
            lr_surface = self.stats_font.render("Longest Road", True, lr_color)
            self.screen.blit(lr_surface, (status_x, header_y))
            la_surface = self.stats_font.render("Largest Army", True, la_color)
            self.screen.blit(la_surface, (status_x, header_y + 20))
            
            header_y += header_surface.get_height() + 5
            
            # victory points
            vp_text = f"VP: {player.get_victory_points()}"
            vp_surface = self.stats_font.render(vp_text, True, BLACK)
            self.screen.blit(vp_surface, (header_x, header_y))
            header_y += vp_surface.get_height() + 10
            
            left_col_x = panel_x + panel_padding
            right_col_x = panel_x + stats_rect.width // 2 + panel_padding
            col_y = header_y
            
            # Left Column: Resources
            res_header = self.stats_font.render("Resources:", True, BLACK)
            self.screen.blit(res_header, (left_col_x, col_y))
            col_y += res_header.get_height() + 2
            
            for res, count in player.resources.items():
                res_text = f"{res}: {count}"
                res_surface = self.stats_font.render(res_text, True, BLACK)
                self.screen.blit(res_surface, (left_col_x + 5, col_y))
                col_y += res_surface.get_height() + 2
            
            # Right Column: Development Cards
            dev_y = header_y
            dev_header = self.stats_font.render("Dev Cards:", True, BLACK)
            self.screen.blit(dev_header, (right_col_x, dev_y))
            dev_y += dev_header.get_height() + 2
            
            # Count development cards for the player
            dev_counts = Counter(str(card) for card in player.unplayed_dev_cards)
            if dev_counts:
                for card_type, count in dev_counts.items():
                    card_text = f"{card_type.capitalize()}: {count}"
                    card_surface = self.stats_font.render(card_text, True, BLACK)
                    self.screen.blit(card_surface, (right_col_x + 5, dev_y))
                    dev_y += card_surface.get_height() + 2
            else:
                none_surface = self.stats_font.render("None", True, BLACK)
                self.screen.blit(none_surface, (right_col_x + 5, dev_y))
                dev_y += none_surface.get_height() + 2

    def handle_event(self, event: pygame.event.Event):
        if self.game is None:
            return
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.game.winning_player_index is None:
                print(f'-------- Player {self.game.player_turn_index + 1} takes turn {self.game.main_turns_elapsed + 1} --------')
                self.game.do_full_turn()
                self.serialization.encode_player_states(self.game, self.game.player_agents[1])
                print("Player States (Playr 2) :", self.serialization.player_states)
                self.serialization.recursive_serialize(self.game, self.game.board.center_tile, None, None)
                print("Player 2 Board State: ", self.serialization.board[1])
                if self.game.winning_player_index is not None:
                    print(f"Player {self.game.winning_player_index + 1} wins!")
            elif event.key == pygame.K_x:
                while self.game.winning_player_index is None:
                    print(f'-------- Player {self.game.player_turn_index + 1} takes turn {self.game.main_turns_elapsed + 1} --------')
                    self.game.do_full_turn()
                print(f"Player {self.game.winning_player_index + 1} wins!")

    def calculate_sizes(self):
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h

        self.board_area_width = int(self.screen_width * 0.75)
        self.board_area_height = int(self.screen_height * 0.85)
        self.stats_area_width = int(self.screen_width * 0.25)
        self.screen_size = (self.board_area_width + self.stats_area_width, self.board_area_height)

        # Board center and size for hexagons
        self.hexagon_size = min(self.board_area_width, self.board_area_height) // 10

    def calculate_fonts(self):
        self.tile_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.03))
        self.harbor_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.015))
        self.stats_title_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.022))
        self.stats_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.018))

    def open_and_loop(self):
        pygame.init()
        pygame.font.init()
        
        self.calculate_sizes()
        self.calculate_fonts()

        # Screen setup
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Settlers of Catan Board")
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    # TODO: more elegant reset
                    self.game = self.game_generator()
                else:
                    self.handle_event(event)
            
            grid_displacement = Point(self.board_area_width // 2, self.board_area_height // 2)
            stats_rect = pygame.Rect(self.board_area_width, 0, self.stats_area_width, self.screen_height)
            self.draw_grid(grid_displacement)
            self.draw_players(grid_displacement)
            self.draw_robber(grid_displacement)
            self.draw_turn_info()
            self.draw_player_stats(stats_rect)
            pygame.display.flip()
        
        pygame.quit()


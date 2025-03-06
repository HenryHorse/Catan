from collections import Counter
from typing import Callable

import pygame

from catan.agent.random import RandomAgent
from catan.agent.human import HumanAgent

from catan.board import Harbor, RoadVertex
from catan.game import Game
from catan.util import Point
from catan.constants import *
from catan.game import GamePhase

class CatanUI:
    game: Game | None
    game_generator: Callable[[], Game]
    screen: pygame.Surface | None

    screen_width: int
    screen_height: int

    board_area_width: int
    board_area_height: int
    stats_area_width: int
    stats_area_height: int
    screen_size: tuple[int, int]
    hexagon_size: int
    displacement: Point

    tile_font: pygame.font.Font
    harbor_font: pygame.font.Font
    stats_title_font: pygame.font.Font
    stats_font: pygame.font.Font

    def __init__(self, game_generator: Callable[[], Game]):
        self.game = None
        self.game_generator = game_generator
        self.screen = None

        self.trade_resource_out = None
        self.trade_resource_in = None
        self.trade_ratio = 4 # default 4

    def attempt_trade(self):
        # Get the current human player (assuming there's one)
        human_pa = next(pa for pa in self.game.player_agents if isinstance(pa.agent, HumanAgent))
        player = human_pa.player

        # Make sure all trade selections are made.
        if self.trade_resource_in is None or self.trade_resource_out is None:
            print("Trade selection incomplete!")
            return

        # Check if the player has enough resources.
        if player.resources[self.trade_resource_in] < self.trade_ratio:
            print("Not enough resources to trade!")
            return

        # Check harbor requirements:
        # 4:1 is always allowed.
        # 3:1 requires a generic 3:1 harbor.
        # 2:1 requires a specific harbor.
        if self.trade_ratio == 2:
            if not player.has_harbor(self.trade_resource_in):
                print("You do not have the required 2:1 harbor for that resource!")
                return
        elif self.trade_ratio == 3:
            if not player.has_harbor(Harbor.THREE_TO_ONE):
                print("You do not have a 3:1 harbor!")
                return

        # Perform the trade:
        player.resources[self.trade_resource_in] -= self.trade_ratio
        player.resources[self.trade_resource_out] += 1
        print(f"Traded {self.trade_ratio} {self.trade_resource_in} for 1 {self.trade_resource_out}.")

        # Reset trade selections.
        self.trade_resource_in = None
        self.trade_resource_out = None
        self.trade_ratio = 4

    def draw_tile(
            self,
            fill_color: tuple[int, int, int],
            outline_color: tuple[int, int, int],
            vertices: list[Point]):
        number_pairs = [point.to_int_tuple() for point in vertices]
        pygame.draw.polygon(self.screen, fill_color, number_pairs)
        pygame.draw.polygon(self.screen, outline_color, number_pairs, 2)

    def draw_grid(self, hover_vertex, hover_road):
        self.screen.fill(BACKGROUND_COLOR)

        if self.screen is None or self.game is None:
            return

        for tile in self.game.board.tiles.values():
            center = tile.get_screen_position(self.hexagon_size) + self.displacement
            vertices = [rv.get_screen_position(self.hexagon_size) + self.displacement for rv in tile.adjacent_road_vertices]
            color = RESOURCE_COLORS[tile.resource.name] if tile.resource else DESERT_COLOR
            self.draw_tile(color, ROAD_COLOR, vertices)
            if tile.number:
                text_surface = self.tile_font.render(str(tile.number), True, WHITE)
                text_rect = text_surface.get_rect(center=(center.to_int_tuple()))
                self.screen.blit(text_surface, text_rect)
        
        for road_vertex in self.game.board.road_vertices:
            pos = road_vertex.get_screen_position(self.hexagon_size) + self.displacement
            if road_vertex.harbor is not None:
                harbor_text = self.harbor_font.render(str(road_vertex.harbor), True, WHITE)
                text_rect = harbor_text.get_rect(center=pos.to_int_tuple())
                if road_vertex == hover_vertex:
                    pygame.draw.rect(self.screen, BLACK, text_rect.inflate(8, 8))
                pygame.draw.rect(self.screen, BROWN, text_rect.inflate(2, 2))
                self.screen.blit(harbor_text, text_rect)
            else:
                radius = 8 if road_vertex == hover_vertex else 4
                if road_vertex == hover_vertex:
                    pygame.draw.circle(self.screen, ROAD_COLOR, pos.to_int_tuple(), radius + 4)
                    pygame.draw.circle(self.screen, HOVER_COLOR, pos.to_int_tuple(), radius)
                else:
                    pygame.draw.circle(self.screen, ROAD_COLOR, pos.to_int_tuple(), radius)

        for road in self.game.board.roads:
            v1, v2 = road.endpoints
            # Compute the screen positions for each endpoint, including the displacement offset.
            v1_screen = v1.get_screen_position(self.hexagon_size) + self.displacement
            v2_screen = v2.get_screen_position(self.hexagon_size) + self.displacement

            # Determine if this road is hovered.
            is_hovered = hover_road and v1 == hover_road.endpoints[0] and v2 == hover_road.endpoints[1]
            road_thickness = 5 if is_hovered else 2

            if is_hovered:
                pygame.draw.line(self.screen, ROAD_COLOR, v1_screen.to_int_tuple(), v2_screen.to_int_tuple(), road_thickness + 4)
                pygame.draw.line(self.screen, HOVER_COLOR, v1_screen.to_int_tuple(), v2_screen.to_int_tuple(), road_thickness - 2)
            else:
                pygame.draw.line(self.screen, ROAD_COLOR, v1_screen.to_int_tuple(), v2_screen.to_int_tuple(), road_thickness)

    def draw_players(self):
        if self.screen is None or self.game is None:
            return
        
        for player_agent in self.game.player_agents:
            player = player_agent.player
            for settlement in player.settlements:
                pos = settlement.get_screen_position(self.hexagon_size) + self.displacement
                pygame.draw.circle(self.screen, player.color, pos.to_int_tuple(), 10)
            for city in player.cities:
                pos = city.get_screen_position(self.hexagon_size) + self.displacement
                pygame.draw.circle(self.screen, player.color, pos.to_int_tuple(), 15)
            for road in player.roads:
                start_pos = road.endpoints[0].get_screen_position(self.hexagon_size) + self.displacement
                end_pos = road.endpoints[1].get_screen_position(self.hexagon_size) + self.displacement
                pygame.draw.line(self.screen, player.color, start_pos.to_int_tuple(), end_pos.to_int_tuple(), 3)
                

    def draw_robber(self):
        if self.screen is None or self.game is None:
            return
        
        if (robber_tile := self.game.board.get_robber_tile()) is not None:
            pos = robber_tile.get_screen_position(self.hexagon_size) + self.displacement
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
        and dev cards on the right. For a human player, also draw the trade panel in the right half.
        Also, show Longest Road and Largest Army statuses next to the title."""
        if self.screen is None or self.game is None:
            return
        
        # Draw the stats area background.
        pygame.draw.rect(self.screen, STATS_BG_COLOR, stats_rect)
        
        num_players = len(self.game.player_agents)
        panel_height = self.stats_area_height // num_players
        panel_padding = 5

        # Loop over players with index so we can check the agent type.
        for idx, pa in enumerate(self.game.player_agents):
            player = pa.player
            # Compute this player's panel rectangle.
            panel_x = stats_rect.left
            panel_y = idx * panel_height
            panel_rect = pygame.Rect(panel_x, panel_y, stats_rect.width, panel_height)
            
            # Draw the panel border.
            pygame.draw.rect(self.screen, player.color, panel_rect, 2)
            
            # Set starting coordinates inside the panel.
            header_x = panel_x + panel_padding
            header_y = panel_y + panel_padding
            
            # Player header.
            header_text = f"Player {idx + 1}"
            header_surface = self.stats_title_font.render(header_text, True, player.color)
            self.screen.blit(header_surface, (header_x, header_y))
            
            # Draw Longest Road and Largest Army statuses.
            lr_has = player.has_longest_road
            la_has = player.has_largest_army
            lr_color = GREEN if lr_has else RED
            la_color = GREEN if la_has else RED
            status_x = header_x + header_surface.get_width() + 15
            lr_surface = self.stats_font.render("Longest Road", True, lr_color)
            self.screen.blit(lr_surface, (status_x, header_y))
            la_surface = self.stats_font.render("Largest Army", True, la_color)
            self.screen.blit(la_surface, (status_x, header_y + 20))
            
            header_y += header_surface.get_height() + 5
            
            # Victory points.
            vp_text = f"VP: {player.victory_points}"
            vp_surface = self.stats_font.render(vp_text, True, BLACK)
            self.screen.blit(vp_surface, (header_x, header_y))
            header_y += vp_surface.get_height() + 10
            
            # Left Column: Resources.
            left_col_x = panel_x + panel_padding
            res_y = header_y
            res_header = self.stats_font.render("Resources:", True, BLACK)
            self.screen.blit(res_header, (left_col_x, res_y))
            res_y += res_header.get_height() + 2
            
            for res, count in player.resources.items():
                res_text = f"{res}: {count}"
                res_surface = self.stats_font.render(res_text, True, BLACK)
                self.screen.blit(res_surface, (left_col_x + 5, res_y))
                res_y += res_surface.get_height() + 2

            # Right Column: Development Cards.
            right_col_x = panel_x + stats_rect.width // 4 + panel_padding
            dev_y = header_y
            dev_header = self.stats_font.render("Dev Cards:", True, BLACK)
            self.screen.blit(dev_header, (right_col_x, dev_y))
            dev_y += dev_header.get_height() + 2
            
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

            if isinstance(pa.agent, HumanAgent):
                trade_panel_rect = pygame.Rect(panel_rect.x + panel_rect.width // 2,
                                            panel_rect.y,
                                            panel_rect.width // 2,
                                            panel_rect.height)
                self.draw_trade_panel(trade_panel_rect)

    def draw_trade_panel(self, panel_rect: pygame.Rect):
        """
        Draw a trade panel in the given rectangle. The panel is divided into 5 rows:
        1. Buy Dev button.
        2. Trade Out (resource to give) row.
        3. Trade In (resource to receive) row.
        4. Trade Ratio row (2, 3, or 4).
        5. Submit Trade button.
        The currently selected option (if any) is outlined with a thicker border.
        """
        num_rows = 5
        margin = 5
        row_height = panel_rect.height / num_rows

        self.trade_rect = panel_rect

        buy_dev_rect = pygame.Rect(
            panel_rect.x + margin,
            panel_rect.y + margin,
            panel_rect.width - 2 * margin,
            row_height - 2 * margin
        )
        pygame.draw.rect(self.screen, WHITE, buy_dev_rect)
        pygame.draw.rect(self.screen, BLACK, buy_dev_rect, 2)
        buy_dev_text = self.stats_font.render("Buy Dev", True, BLACK)
        self.screen.blit(buy_dev_text, (buy_dev_rect.x + 5, buy_dev_rect.y + 5))
        self.buy_dev_rect = buy_dev_rect

        resources = [Resource.WOOD, Resource.GRAIN, Resource.SHEEP, Resource.ORE, Resource.BRICK]
        num_options = len(resources)
        
        row1_y = panel_rect.y + row_height
        trade_out_rect = pygame.Rect(
            panel_rect.x + margin,
            row1_y + margin,
            panel_rect.width - 2 * margin,
            row_height - 2 * margin
        )
        gap = margin
        option_width = (trade_out_rect.width - (num_options - 1) * gap) / num_options
        self.trade_out_buttons = []
        for i, res in enumerate(resources):
            btn_rect = pygame.Rect(
                trade_out_rect.x + i * (option_width + gap),
                trade_out_rect.y,
                option_width,
                trade_out_rect.height
            )
            pygame.draw.rect(self.screen, RESOURCE_COLORS[res.name], btn_rect)
            if self.trade_resource_in == res:
                pygame.draw.rect(self.screen, BLACK, btn_rect, 3)
            else:
                pygame.draw.rect(self.screen, BLACK, btn_rect, 1)
            label = self.stats_font.render(str(res)[:1], True, BLACK)
            label_rect = label.get_rect(center=btn_rect.center)
            self.screen.blit(label, label_rect)
            self.trade_out_buttons.append((btn_rect, res))

        row2_y = panel_rect.y + 2 * row_height
        trade_in_rect = pygame.Rect(
            panel_rect.x + margin,
            row2_y + margin,
            panel_rect.width - 2 * margin,
            row_height - 2 * margin
        )
        self.trade_in_buttons = []
        for i, res in enumerate(resources):
            btn_rect = pygame.Rect(
                trade_in_rect.x + i * (option_width + gap),
                trade_in_rect.y,
                option_width,
                trade_in_rect.height
            )
            pygame.draw.rect(self.screen, RESOURCE_COLORS[res.name], btn_rect)
            if self.trade_resource_out == res:
                pygame.draw.rect(self.screen, BLACK, btn_rect, 3)
            else:
                pygame.draw.rect(self.screen, BLACK, btn_rect, 1)
            label = self.stats_font.render(str(res)[:1], True, BLACK)
            label_rect = label.get_rect(center=btn_rect.center)
            self.screen.blit(label, label_rect)
            self.trade_in_buttons.append((btn_rect, res))

        row3_y = panel_rect.y + 3 * row_height
        trade_ratio_rect = pygame.Rect(
            panel_rect.x + margin,
            row3_y + margin,
            panel_rect.width - 2 * margin,
            row_height - 2 * margin
        )
        ratio_options = [2, 3, 4]
        num_ratios = len(ratio_options)
        option_width_ratio = (trade_ratio_rect.width - (num_ratios - 1) * gap) / num_ratios
        self.trade_ratio_buttons = []
        for i, ratio in enumerate(ratio_options):
            btn_rect = pygame.Rect(
                trade_ratio_rect.x + i * (option_width_ratio + gap),
                trade_ratio_rect.y,
                option_width_ratio,
                trade_ratio_rect.height
            )
            pygame.draw.rect(self.screen, WHITE, btn_rect)
            if self.trade_ratio == ratio:
                pygame.draw.rect(self.screen, BLACK, btn_rect, 3)
            else:
                pygame.draw.rect(self.screen, BLACK, btn_rect, 1)
            ratio_label = self.stats_font.render(str(ratio), True, BLACK)
            label_rect = ratio_label.get_rect(center=btn_rect.center)
            self.screen.blit(ratio_label, label_rect)
            self.trade_ratio_buttons.append((btn_rect, ratio))

        row4_y = panel_rect.y + 4 * row_height
        submit_rect = pygame.Rect(
            panel_rect.x + margin,
            row4_y + margin,
            panel_rect.width - 2 * margin,
            row_height - 2 * margin
        )
        pygame.draw.rect(self.screen, WHITE, submit_rect)
        pygame.draw.rect(self.screen, BLACK, submit_rect, 2)
        submit_label = self.stats_font.render("Submit Trade", True, BLACK)
        submit_label_rect = submit_label.get_rect(center=submit_rect.center)
        self.screen.blit(submit_label, submit_label_rect)
        self.submit_trade_rect = submit_rect



    def handle_event(self, event: pygame.event.Event, hover_vertex: RoadVertex = None, hover_road = None, current_player = None):
        if self.game is None:
            return

        current_player = self.game.player_agents[self.game.player_turn_index]
        
        mouse_pos = pygame.mouse.get_pos()

        if isinstance(current_player.agent, HumanAgent):
            if self.game.game_phase == GamePhase.SETUP:
                if event.type == pygame.MOUSEBUTTONDOWN and hover_vertex is not None:
                    if current_player.player.is_valid_settlement_location(hover_vertex, False) and not hover_vertex.has_settlement:
                        current_player.player.build_settlement(hover_vertex, False)
                elif event.type == pygame.MOUSEBUTTONDOWN and hover_road is not None:
                    if current_player.player.is_valid_road_location(hover_road, True):
                        current_player.player.build_road(hover_road, self.game, False)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                    print("-------- Human setup turn complete --------")
                    self.game.advance_player_turn()
                    self.game.setup_turn_counter += 1
                    human_index = next(i for i, pa in enumerate(self.game.player_agents)
                                        if isinstance(pa.agent, HumanAgent))
                    bot_indices = [i for i, pa in enumerate(self.game.player_agents)
                                if not isinstance(pa.agent, HumanAgent)]
                    total_order = [human_index] + bot_indices + bot_indices[::-1] + [human_index]
                    if self.game.setup_turn_counter >= len(total_order):
                        self.game.game_phase = GamePhase.MAIN
                        self.game.player_turn_index = 0
                    else:
                        self.game.player_turn_index = total_order[self.game.setup_turn_counter]
            else:
                # MAIN phase for human.
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if hasattr(self, "trade_rect") and self.trade_rect.collidepoint(mouse_pos):
                        if self.buy_dev_rect.collidepoint(mouse_pos):
                            try:
                                current_player.player.buy_development_card(self.game.board)
                                print("Bought a development card.")
                            except Exception as e:
                                print(e)
                        for rect, res in self.trade_out_buttons:
                            if rect.collidepoint(mouse_pos):
                                self.trade_resource_in = res
                                print(f"Selected to trade out: {res}")
                        for rect, res in self.trade_in_buttons:
                            if rect.collidepoint(mouse_pos):
                                self.trade_resource_out = res
                                print(f"Selected to trade in: {res}")
                        for rect, ratio in self.trade_ratio_buttons:
                            if rect.collidepoint(mouse_pos):
                                self.trade_ratio = ratio
                                print(f"Selected trade ratio: {ratio}")
                        if self.submit_trade_rect.collidepoint(mouse_pos):
                            print("Submit Trade clicked.")
                            self.attempt_trade()
                        return
                    else:
                        if hover_road is not None:
                            if current_player.player.is_valid_road_location(hover_road):
                                current_player.player.build_road(hover_road, self.game, True)
                        elif hover_vertex is not None:
                            if current_player.player.is_valid_settlement_location(hover_vertex) and not hover_vertex.has_settlement:
                                current_player.player.build_settlement(hover_vertex, True)
                            elif current_player.player.is_valid_city_location(hover_vertex) and not hover_vertex.has_city:
                                current_player.player.build_city(hover_vertex, True)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_c and self.game.winning_player_index is None:
                    print(f'-------- Human Player {self.game.player_turn_index + 1} ends turn {self.game.main_turns_elapsed + 1} --------')
                    self.game.human_dice_rolled = False
                    self.game.advance_player_turn()
        elif event.type == pygame.KEYDOWN and not self.game.has_human:
            if event.key == pygame.K_SPACE and self.game.winning_player_index is None:
                print(f'-------- Player {self.game.player_turn_index + 1} takes turn {self.game.main_turns_elapsed + 1} --------')
                self.game.do_full_turn()
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

        self.board_area_width = int(self.screen_width * 0.60)
        self.board_area_height = int(self.screen_height * 0.70)
        self.stats_area_width = int(self.screen_width * 0.20)
        self.stats_area_height = int(self.screen_height * 0.70)
        self.screen_size = (self.board_area_width + self.stats_area_width, self.board_area_height)

        # Board center and size for hexagons
        self.hexagon_size = min(self.board_area_width, self.board_area_height) // 10
        self.displacement = Point(self.board_area_width // 2, self.board_area_height // 2)

    def calculate_fonts(self):
        self.tile_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.03))
        self.harbor_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.015))
        self.stats_title_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.022))
        self.stats_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.014))

    def open_and_loop(self):
        pygame.init()
        pygame.font.init()
        
        self.calculate_sizes()
        self.calculate_fonts()

        # Screen setup
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Settlers of Catan Board")
        
        self.game = self.game_generator()

        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            hover_vertex = self.game.board.get_vertex_at_pos(mouse_pos, self.hexagon_size, self.displacement)
            hover_road = self.game.board.get_road_at_pos(mouse_pos, self.hexagon_size, self.displacement)
            if hover_vertex:
                hover_road = None
            if self.game.has_human and self.game.player_turn_index != 0:
                if self.game.winning_player_index is None:
                    print(f'-------- Player {self.game.player_turn_index + 1} takes turn {self.game.main_turns_elapsed + 1} --------')
                    self.game.do_full_turn()
                    if self.game.winning_player_index is not None:
                        print(f"Player {self.game.winning_player_index + 1} wins!")
            elif self.game.has_human and self.game.human_dice_rolled == False and self.game.game_phase == GamePhase.MAIN:
                if self.game.winning_player_index is None:
                    print(f'-------- Human Player starts turn {self.game.main_turns_elapsed + 1} --------')
                    self.game.human_dice_roll()
                    self.game.human_dice_rolled = True
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    # TODO: more elegant reset
                    self.game = self.game_generator()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_event(event, hover_vertex, hover_road)
                else:
                    self.handle_event(event, None, None)
    
            stats_rect = pygame.Rect(self.board_area_width, 0, self.stats_area_width, self.screen_height)
            self.draw_grid(hover_vertex, hover_road)
            self.draw_players()
            self.draw_robber()
            self.draw_turn_info()
            self.draw_player_stats(stats_rect)
            pygame.display.flip()
        
        pygame.quit()


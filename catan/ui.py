from collections import Counter
from typing import Callable
import pygame
import math
import numpy as np
import torch

from catan.agent.random import RandomAgent
from catan.agent.human import HumanAgent
from catan.board import DevelopmentCard, Harbor, RoadVertex
from catan.game import Game
from catan.game import GamePhase
from catan.util import Point
from catan.constants import *
from catan.game import GamePhase

from globals import DEV_MODE
from globals import NUM_GAMES

# List of resources in fixed order for modal overlays.
RESOURCE_ORDER = [Resource.WOOD, Resource.GRAIN, Resource.SHEEP, Resource.ORE, Resource.BRICK]
from catan.serialization import BrickRepresentation
from catan.agent.rl_agent import RLAgent
from catan.player import Player

import copy


class CatanUI:
    game: Game | None
    game_generator: Callable[[], Game]
    screen: pygame.Surface | None
    rl_agent: RLAgent | None
    model_path: str | None

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

    def __init__(self, game_generator: Callable[[], Game], serialization: BrickRepresentation, rl_agent: RLAgent = None, model_path: str = None):
        self.game = None
        self.game_generator = game_generator
        self.screen = None
        self.serialization = serialization
        self.rl_agent = rl_agent
        self.model_path = model_path

        self.trade_resource_out = None
        self.trade_resource_in = None
        self.trade_ratio = 4  # default 4

        self.human_setup_settlement_placed = False
        self.human_setup_road_placed = False

        # NEW: Pending development card action state.
        # It can be one of: "KNIGHT", "KNIGHT_STEAL", "ROAD_BUILDER", "MONOPOLY", "YEAR_OF_PLENTY"
        self.pending_dev_action = None
        self.pending_dev_data = {}

    def attempt_trade(self):
        human_pa = next(pa for pa in self.game.player_agents if isinstance(pa.agent, HumanAgent))
        player = human_pa.player

        if self.trade_resource_in is None or self.trade_resource_out is None:
            if DEV_MODE:
                print("Trade selection incomplete!")
            return

        if player.resources[self.trade_resource_in] < self.trade_ratio:
            if DEV_MODE:
                print("Not enough resources to trade!")
            return

        if self.trade_ratio == 2:
            if not player.has_harbor(self.trade_resource_in):
                if DEV_MODE:
                    print("You do not have the required 2:1 harbor for that resource!")
                return
        elif self.trade_ratio == 3:
            if not player.has_harbor(Harbor.THREE_TO_ONE):
                if DEV_MODE:
                    print("You do not have a 3:1 harbor!")
                return

        player.resources[self.trade_resource_in] -= self.trade_ratio
        player.resources[self.trade_resource_out] += 1
        if DEV_MODE:
            print(f"Traded {self.trade_ratio} {self.trade_resource_in} for 1 {self.trade_resource_out}.")

        self.trade_resource_in = None
        self.trade_resource_out = None
        self.trade_ratio = 4


    def draw_tile(self, fill_color: tuple[int, int, int], outline_color: tuple[int, int, int], vertices: list[Point]):
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
            v1_screen = v1.get_screen_position(self.hexagon_size) + self.displacement
            v2_screen = v2.get_screen_position(self.hexagon_size) + self.displacement

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
        if self.screen is None or self.game is None:
            return
        info_text = f"Turn {self.game.main_turns_elapsed + 1} - Player {self.game.player_turn_index + 1}'s Turn"
        info_surface = self.stats_title_font.render(info_text, True, BLACK)
        self.screen.blit(info_surface, (10, 10))

    def draw_player_stats(self, stats_rect: pygame.Rect):
        if self.screen is None or self.game is None:
            return

        pygame.draw.rect(self.screen, STATS_BG_COLOR, stats_rect)
        num_players = len(self.game.player_agents)
        panel_height = self.stats_area_height // num_players
        panel_padding = 5

        for idx, pa in enumerate(self.game.player_agents):
            player = pa.player
            panel_x = stats_rect.left
            panel_y = idx * panel_height
            panel_rect = pygame.Rect(panel_x, panel_y, stats_rect.width, panel_height)
            pygame.draw.rect(self.screen, player.color, panel_rect, 2)

            header_x = panel_x + panel_padding
            header_y = panel_y + panel_padding

            header_text = f"Player {idx + 1}"
            header_surface = self.stats_title_font.render(header_text, True, player.color)
            self.screen.blit(header_surface, (header_x, header_y))

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

            vp_text = f"VP: {player.get_victory_points()}"
            vp_surface = self.stats_font.render(vp_text, True, BLACK)
            self.screen.blit(vp_surface, (header_x, header_y))
            header_y += vp_surface.get_height() + 10

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

            right_col_x = panel_x + stats_rect.width // 4 + panel_padding
            dev_y = header_y
            dev_header = self.stats_font.render("Dev Cards:", True, BLACK)
            self.screen.blit(dev_header, (right_col_x, dev_y))
            dev_y += dev_header.get_height() + 5

            ordered_dev_cards = [
                DevelopmentCard.VICTORY_POINT,
                DevelopmentCard.KNIGHT,
                DevelopmentCard.ROAD_BUILDING,
                DevelopmentCard.YEAR_OF_PLENTY,
                DevelopmentCard.MONOPOLY,
            ]

            if isinstance(pa.agent, HumanAgent):
                self.dev_card_buttons = {}
                for card in ordered_dev_cards:
                    count = sum(1 for c in player.unplayed_dev_cards if c == card)
                    card_name = str(card)
                    if card_name == "Year Of Plenty":
                        card_name = "YoP"
                    if card_name == "Road Building":
                        card_name = "RB"
                    if card_name == "Monopoly":
                        card_name = "Mono"
                    card_text = f"{card_name}: {count}"
                    card_surface = self.stats_font.render(card_text, True, BLACK)
                    text_y = dev_y

                    if card == DevelopmentCard.VICTORY_POINT:
                        self.screen.blit(card_surface, (right_col_x, text_y))
                        dev_y += card_surface.get_height() + 5
                    else:
                        button_text = "Use"
                        button_surface = self.stats_font.render(button_text, True, BLACK)
                        button_width = button_surface.get_width() + 10
                        button_height = button_surface.get_height() + 4
                        button_rect = pygame.Rect(right_col_x, text_y, button_width, button_height)

                        if count > 0:
                            button_color = WHITE
                            active = True
                        else:
                            button_color = (200, 200, 200)
                            active = False

                        pygame.draw.rect(self.screen, button_color, button_rect)
                        pygame.draw.rect(self.screen, BLACK, button_rect, 2)
                        self.screen.blit(button_surface, (button_rect.x + 5, button_rect.y + 2))
                        self.dev_card_buttons[card] = (button_rect, active)

                        text_x = button_rect.right + 10
                        self.screen.blit(card_surface, (text_x, text_y))
                        dev_y += max(button_height, card_surface.get_height()) + 5
            else:
                for card in ordered_dev_cards:
                    count = sum(1 for c in player.unplayed_dev_cards if c == card)
                    card_name = str(card)
                    if card_name == "Year Of Plenty":
                        card_name = "YoP"
                    if card_name == "Road Building":
                        card_name = "RB"
                    if card_name == "Monopoly":
                        card_name = "Mono"
                    card_text = f"{card_name}: {count}"
                    card_surface = self.stats_font.render(card_text, True, BLACK)
                    self.screen.blit(card_surface, (right_col_x, dev_y))
                    dev_y += card_surface.get_height() + 5

            if isinstance(pa.agent, HumanAgent):
                trade_panel_rect = pygame.Rect(panel_rect.x + panel_rect.width // 2,
                                               panel_rect.y,
                                               panel_rect.width // 2,
                                               panel_rect.height)
                self.draw_trade_panel(trade_panel_rect)
        # If a pending special dev card action is active (MONOPOLY or YEAR_OF_PLENTY), draw the modal overlay.
        if self.pending_dev_action in ("MONOPOLY", "YEAR_OF_PLENTY"):
            self.draw_modal_overlay()

    def draw_trade_panel(self, panel_rect: pygame.Rect):
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

    def draw_modal_overlay(self):
        # Draw a semi-transparent gray overlay over the entire screen.
        overlay = pygame.Surface(self.screen_size)
        overlay.set_alpha(180)
        overlay.fill((100, 100, 100))
        self.screen.blit(overlay, (0, 0))
        # Draw 5 colored squares for resource selection in the center.
        modal_width = self.board_area_height * 0.5
        modal_height = 100
        modal_x = (self.board_area_width - modal_width) / 2
        modal_y = (self.board_area_height - modal_height) / 2
        gap = 10
        num_options = 5
        option_width = (modal_width - (num_options - 1) * gap) / num_options
        for i, res in enumerate(RESOURCE_ORDER):
            rect = pygame.Rect(modal_x + i * (option_width + gap), modal_y, option_width, modal_height)
            pygame.draw.rect(self.screen, RESOURCE_COLORS[res.name], rect)
            # Draw resource label (first letter)
            label = self.stats_font.render(str(res)[:1], True, BLACK)
            label_rect = label.get_rect(center=rect.center)
            self.screen.blit(label, label_rect)
        # Save the modal rectangle positions for use in click detection.
        self.modal_rects = [pygame.Rect(modal_x + i * (option_width + gap), modal_y, option_width, modal_height) for i in range(num_options)]

    def get_resource_from_modal(self, pos) -> Resource | None:
        # Check if the click position is inside any modal rect.
        for rect, res in zip(self.modal_rects, RESOURCE_ORDER):
            if rect.collidepoint(pos):
                return res
        return None

    def advance_setup_turn(self):
        if DEV_MODE:
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
        self.human_setup_settlement_placed = False
        self.human_setup_road_placed = False

    def handle_event(self, event: pygame.event.Event, hover_vertex: RoadVertex = None, hover_road = None, current_player = None):
        if self.game is None:
            return

        current_player = self.game.player_agents[self.game.player_turn_index]
        mouse_pos = pygame.mouse.get_pos()

        # ***** First, check for a pending dev card action *****
        if self.pending_dev_action is not None:
            if self.pending_dev_action == "KNIGHT":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    tile = self.game.board.get_tile_at_pos(mouse_pos, self.hexagon_size, self.displacement)
                    if tile is not None:
                        self.game.board.move_robber(tile)
                        if DEV_MODE:
                            print("Robber moved. Now select a settlement/city on that tile to steal from.")
                        self.pending_dev_action = "KNIGHT_STEAL"
                return

            elif self.pending_dev_action == "KNIGHT_STEAL":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Here, assume get_building_at_pos returns the settlement/city clicked on.
                    target = self.game.board.get_building_at_pos(mouse_pos, self.hexagon_size, self.displacement)
                    if target is not None and target.owner is not None and target.owner != current_player.player.index:
                        try:
                            stolen = self.game.player_agents[target.owner].player.take_random_resources(1)
                            current_player.player.give_resource(stolen[0])
                            if DEV_MODE:
                                print(f"Stolen resource: {stolen[0]}")
                        except Exception as e:
                            if DEV_MODE:
                                print(f"Error during steal: {e}")
                        self.pending_dev_action = None
                return

            elif self.pending_dev_action == "ROAD_BUILDER":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    road = self.game.board.get_road_at_pos(mouse_pos, self.hexagon_size, self.displacement)
                    if road is not None and current_player.player.is_valid_road_location(road):
                        try:
                            current_player.player.build_road(road, self.game, False)
                            self.pending_dev_data["roads_built"] += 1
                            if DEV_MODE:
                                print(f"Built free road ({self.pending_dev_data['roads_built']}/2).")
                        except Exception as e:
                            if DEV_MODE:
                                print(f"Cannot build road: {e}")
                        if self.pending_dev_data["roads_built"] >= 2:
                            self.pending_dev_action = None
                            self.pending_dev_data = {}
                return

            elif self.pending_dev_action == "MONOPOLY":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    res = self.get_resource_from_modal(mouse_pos)
                    if res is not None:
                        # Call a method on your game to process monopoly.
                        self.game.select_and_steal_all_resources(current_player.player.index, res)
                        if DEV_MODE:
                            print(f"Monopoly applied for {res}.")
                        self.pending_dev_action = None
                return

            elif self.pending_dev_action == "YEAR_OF_PLENTY":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    res = self.get_resource_from_modal(mouse_pos)
                    if res is not None:
                        current_player.player.give_resource(res)
                        self.pending_dev_data["clicks"] += 1
                        if DEV_MODE:
                            print(f"Received 1 {res} (Year of Plenty).")
                        if self.pending_dev_data["clicks"] >= 2:
                            self.pending_dev_action = None
                            self.pending_dev_data = {}
                return
        # ***** End pending action processing *****

        # Normal event handling.
        if isinstance(current_player.agent, HumanAgent):
            if self.game.game_phase == GamePhase.SETUP:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.human_setup_settlement_placed and hover_vertex is not None:
                        if current_player.player.is_valid_settlement_location(hover_vertex, False) and not hover_vertex.has_settlement:
                            current_player.player.build_settlement(hover_vertex, False)
                            self.human_setup_settlement_placed = True
                    if self.human_setup_settlement_placed and not self.human_setup_road_placed and hover_road is not None:
                        if current_player.player.is_valid_road_location(hover_road, True):
                            current_player.player.build_road(hover_road, self.game, False)
                            self.human_setup_road_placed = True

                    if self.human_setup_settlement_placed and self.human_setup_road_placed:
                        self.advance_setup_turn()
            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # First, check dev card buttons.
                    if hasattr(self, "dev_card_buttons"):
                        for card, (btn_rect, active) in self.dev_card_buttons.items():
                            if btn_rect.collidepoint(mouse_pos):
                                if active:
                                    try:
                                        # Instead of immediately playing the card, set pending state.
                                        if card == DevelopmentCard.KNIGHT:
                                            self.pending_dev_action = "KNIGHT"
                                            if DEV_MODE:
                                                print("Knight card activated. Click a tile to move the robber.")
                                        elif card == DevelopmentCard.ROAD_BUILDING:
                                            self.pending_dev_action = "ROAD_BUILDER"
                                            self.pending_dev_data = {"roads_built": 0}
                                            if DEV_MODE:
                                                print("Road Builder activated. Build 2 free roads by clicking valid locations.")
                                        elif card == DevelopmentCard.MONOPOLY:
                                            self.pending_dev_action = "MONOPOLY"
                                            if DEV_MODE:
                                                print("Monopoly activated. Click on a resource square (modal) to steal all of that resource.")
                                        elif card == DevelopmentCard.YEAR_OF_PLENTY:
                                            self.pending_dev_action = "YEAR_OF_PLENTY"
                                            self.pending_dev_data = {"clicks": 0}
                                            if DEV_MODE:
                                                print("Year of Plenty activated. Click twice on resource squares to gain 2 resources.")
                                    except Exception as e:
                                        if DEV_MODE:
                                            print(e)
                                else:
                                    if DEV_MODE:
                                        print(f"{card} is not playable.")
                                return
                    # Then check trade panel.
                    if hasattr(self, "trade_rect") and self.trade_rect.collidepoint(mouse_pos):
                        if self.buy_dev_rect.collidepoint(mouse_pos):
                            try:
                                current_player.player.buy_development_card(self.game.board)
                                if DEV_MODE:
                                    print("Bought a development card.")
                            except Exception as e:
                                if DEV_MODE:
                                    print(e)
                        for rect, res in self.trade_out_buttons:
                            if rect.collidepoint(mouse_pos):
                                self.trade_resource_in = res
                                if DEV_MODE:
                                    print(f"Selected to trade out: {res}")
                        for rect, res in self.trade_in_buttons:
                            if rect.collidepoint(mouse_pos):
                                self.trade_resource_out = res
                                if DEV_MODE:
                                    print(f"Selected to trade in: {res}")
                        for rect, ratio in self.trade_ratio_buttons:
                            if rect.collidepoint(mouse_pos):
                                self.trade_ratio = ratio
                                if DEV_MODE:
                                    print(f"Selected trade ratio: {ratio}")
                        if self.submit_trade_rect.collidepoint(mouse_pos):
                            if DEV_MODE:
                                print("Submit Trade clicked.")
                            self.attempt_trade()
                        return
                    else:
                        if hover_road is not None:
                            if current_player.player.is_valid_road_location(hover_road):
                                try:
                                    current_player.player.build_road(hover_road, self.game, True)
                                except Exception as e:
                                    if DEV_MODE:
                                        print(e)
                        elif hover_vertex is not None:
                            if current_player.player.is_valid_settlement_location(hover_vertex) and not hover_vertex.has_settlement:
                                try:
                                    current_player.player.build_settlement(hover_vertex, True)
                                except Exception as e:
                                    if DEV_MODE:
                                        print(e)
                            elif current_player.player.is_valid_city_location(hover_vertex) and not hover_vertex.has_city:
                                try:
                                    current_player.player.build_city(hover_vertex, True)
                                except Exception as e:
                                    if DEV_MODE:
                                        print(e)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_c and self.game.winning_player_index is None:
                    if DEV_MODE:
                        print(f'-------- Human Player {self.game.player_turn_index + 1} ends turn {self.game.main_turns_elapsed + 1} --------')
                    self.game.human_dice_rolled = False
                    self.game.recompute_longest_road()
                    self.game.recompute_largest_army()
                    self.game.advance_player_turn()
        elif event.type == pygame.KEYDOWN and not self.game.has_human:
            if event.key == pygame.K_SPACE and self.game.winning_player_index is None:
                if DEV_MODE:
                    print(f'-------- Player {self.game.player_turn_index + 1} takes turn {self.game.main_turns_elapsed + 1} --------')
                self.game.do_full_turn()
                self.serialization.encode_player_states(self.game, self.game.player_agents[1].player)
                if DEV_MODE:
                    print("Player States (Player 2):", self.serialization.player_states)
                self.serialization.recursive_serialize(self.game, self.game.board.center_tile, None, None)
                if DEV_MODE:
                    print("Player 2 Board State:", self.serialization.board[1])

                # Store experience and train RL agent
                if self.rl_agent:
                    if DEV_MODE:
                        print(f'-------- RL AGENT  --------')
                    # Convert board state to tensor
                    board_state = torch.tensor(self.serialization.board, dtype=torch.float32)

                    # Flatten player_states and convert to tensor
                    player_state = self.serialization.flatten_nested_list(self.serialization.player_states)
                    player_state = torch.tensor(player_state, dtype=torch.float32)

                    # Ensure player_state has the correct shape (batch_size, player_state_dim)
                    player_state = player_state.unsqueeze(0)  # Add batch dimension

                    state = (board_state, player_state)

                    current_player_agent = self.game.player_agents[self.game.player_turn_index]
                    possible_actions = current_player_agent.player._get_all_possible_actions_normal(self.game.board)
                    action = self.rl_agent.get_action(self.game, current_player_agent.player, possible_actions)
                    reward = self.calculate_reward(current_player_agent.player)

                    # Convert next states to tensors
                    next_board_state = torch.tensor(self.serialization.board, dtype=torch.float32)
                    next_player_state = torch.tensor(player_state, dtype=torch.float32)  # Reuse flattened player_state
                    next_state = (next_board_state, next_player_state)

                    done = self.game.winning_player_index is not None

                    self.rl_agent.store_experience(state, action, reward, next_state, done)

                    self.rl_agent.train()
                    # Save the model
                    if self.rl_agent and self.model_path:
                        torch.save(self.rl_agent.model.state_dict(), self.model_path)
                        if DEV_MODE:
                            print(f"Model saved to {self.model_path}")

                if self.game.winning_player_index is not None:
                    if DEV_MODE:
                        print(f"Player {self.game.winning_player_index + 1} wins!")
                    # Save the model after each game
                    if self.rl_agent and self.model_path:
                        torch.save(self.rl_agent.model.state_dict(), self.model_path)
                        if DEV_MODE:
                            print(f"Model saved to {self.model_path}")
            elif event.key == pygame.K_x:
                while self.game.winning_player_index is None:
                    if DEV_MODE:
                        print(f'-------- Player {self.game.player_turn_index + 1} takes turn {self.game.main_turns_elapsed + 1} --------')
                    self.game.do_full_turn()

                    self.serialization.encode_player_states(self.game, self.game.player_agents[1].player)
                    if DEV_MODE:
                        print("Player States (Player 2):", self.serialization.player_states)
                    self.serialization.recursive_serialize(self.game, self.game.board.center_tile, None, None)
                    if DEV_MODE:
                        print("Player 2 Board State:", self.serialization.board[1])

                    # Store experience and train RL agent
                    if self.rl_agent:
                        # Convert board state to tensor
                        board_state = torch.tensor(self.serialization.board, dtype=torch.float32)

                        # Flatten player_states and convert to tensor
                        player_state = self.serialization.flatten_nested_list(self.serialization.player_states)
                        player_state = torch.tensor(player_state, dtype=torch.float32)

                        # Ensure player_state has the correct shape (batch_size, player_state_dim)
                        player_state = player_state.unsqueeze(0)  # Add batch dimension

                        state = (board_state, player_state)

                        current_player_agent = self.game.player_agents[self.game.player_turn_index]
                        possible_actions = current_player_agent.player._get_all_possible_actions_normal(self.game.board)
                        action = self.rl_agent.get_action(self.game, current_player_agent.player, possible_actions)
                        reward = self.calculate_reward(current_player_agent.player)

                        # Convert next states to tensors
                        next_board_state = torch.tensor(self.serialization.board, dtype=torch.float32)
                        next_player_state = torch.tensor(player_state, dtype=torch.float32)  # Reuse flattened player_state
                        next_state = (next_board_state, next_player_state)

                        done = self.game.winning_player_index is not None

                        self.rl_agent.store_experience(state, action, reward, next_state, done)
                        self.rl_agent.train()
                if DEV_MODE:
                    print(f"Player {self.game.winning_player_index + 1} wins!")
                if self.rl_agent and self.model_path:
                    torch.save(self.rl_agent.model.state_dict(), self.model_path)
                    if DEV_MODE:
                        print(f"Model saved to {self.model_path}")

    def calculate_reward(self, player: Player) -> float:
        """Calculate reward based on player's progress, with higher rewards for wheat and ore."""
        reward = 0

        # Reward for victory points
        reward += player.get_victory_points() * 5  # Reward for victory points

        # Reward for resources, with higher weights for wheat and ore
        resource_weights = {
            Resource.GRAIN: .3,
            Resource.ORE: .3,
            Resource.BRICK: .1,
            Resource.WOOD: .1,
            Resource.SHEEP: .1,
        }
        # Calculate weighted sum of resources
        for resource, amount in player.resources.items():
            reward += amount * resource_weights.get(resource, 1)  # Use weight if defined, otherwise default to 1

        return reward

    def calculate_sizes(self):
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.board_area_width = int(self.screen_width * 0.60)
        self.board_area_height = int(self.screen_height * 0.80)
        self.stats_area_width = int(self.screen_width * 0.25)
        self.stats_area_height = int(self.screen_height * 0.80)
        self.screen_size = (self.board_area_width + self.stats_area_width, self.board_area_height)
        self.hexagon_size = min(self.board_area_width, self.board_area_height) // 10
        self.displacement = Point(self.board_area_width // 2, self.board_area_height // 2)

    def calculate_fonts(self):
        self.tile_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.03))
        self.harbor_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.015))
        self.stats_title_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.022))
        self.stats_font = pygame.font.SysFont('Arial', int(self.screen_height * 0.014))

    def open_and_loop(self, doSimulate, train):
        if doSimulate:
            num_games = NUM_GAMES
            total_turns = 0
            win_counts = {}
            self.game = self.game_generator()
            self.initial_game_state = copy.deepcopy(self.game)
            print("Starting simulation of", num_games, "games...")
            if train == 1:
                print("Training enabled")
            for i in range(num_games):
                print("Game ", i)
                while self.game.winning_player_index is None:
                    self.game.do_full_turn()

                    if train == 1:
                        self.serialization.encode_player_states(self.game, self.game.player_agents[1].player)
                        self.serialization.recursive_serialize(self.game, self.game.board.center_tile, None, None)
                        board_state = torch.tensor(self.serialization.board, dtype=torch.float32)
                        player_state = self.serialization.flatten_nested_list(self.serialization.player_states)
                        player_state = torch.tensor(player_state, dtype=torch.float32)
                        player_state = player_state.unsqueeze(0)  # Add batch dimension
                        state = (board_state, player_state)
                        
                        current_player_agent = self.game.player_agents[self.game.player_turn_index]
                        possible_actions = current_player_agent.player._get_all_possible_actions_normal(self.game.board)
                        action = self.rl_agent.get_action(self.game, current_player_agent.player, possible_actions)
                        reward = self.calculate_reward(current_player_agent.player)
                        
                        next_board_state = torch.tensor(self.serialization.board, dtype=torch.float32)
                        next_player_state = torch.tensor(player_state, dtype=torch.float32)
                        next_state = (next_board_state, next_player_state)
                        
                        done = self.game.winning_player_index is not None
                        self.rl_agent.store_experience(state, action, reward, next_state, done)
                        self.rl_agent.train()

                turns = self.game.main_turns_elapsed + 1
                total_turns += turns
                winner = self.game.winning_player_index
                win_counts[winner] = win_counts.get(winner, 0) + 1
                if DEV_MODE:
                    print(f"Game {i+1} finished in {turns} turns. Winner: Player {winner + 1}")
                self.game = self.game_generator()
                self.game = copy.deepcopy(self.initial_game_state)
            avg_turns = total_turns / num_games
            print("\nSimulation complete")
            print(f"Average number of turns: {avg_turns:.2f}")
            for player in sorted(win_counts.keys()):
                print(f"Player {player + 1}: {win_counts[player]} wins")
            if train == 1 and self.rl_agent and self.model_path:
                torch.save(self.rl_agent.model.state_dict(), self.model_path)
                print(f"Model saved to {self.model_path}")
            return

        # Interactive mode
        pygame.init()
        pygame.font.init()
        self.calculate_sizes()
        self.calculate_fonts()
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Settlers of Catan Board")

        self.game = self.game_generator()
        self.initial_game_state = copy.deepcopy(self.game)

        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            hover_vertex = self.game.board.get_vertex_at_pos(mouse_pos, self.hexagon_size, self.displacement)
            hover_road = self.game.board.get_road_at_pos(mouse_pos, self.hexagon_size, self.displacement)
            if hover_vertex:
                hover_road = None
            if self.game.has_human and self.game.player_turn_index != 0:
                if self.game.winning_player_index is None:
                    if DEV_MODE:
                        print(f'-------- Player {self.game.player_turn_index + 1} takes turn {self.game.main_turns_elapsed + 1} --------')
                    self.game.do_full_turn()
                    if self.game.winning_player_index is not None:
                        if DEV_MODE:
                            print(f"Player {self.game.winning_player_index + 1} wins!")
            elif self.game.has_human and not self.game.human_dice_rolled and self.game.game_phase == GamePhase.MAIN:
                if self.game.winning_player_index is None:
                    if DEV_MODE:
                        print(f'-------- Human Player starts turn {self.game.main_turns_elapsed + 1} --------')
                    self.game.human_dice_roll()
                    self.game.human_dice_rolled = True
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.game = self.game_generator()
                    self.game = copy.deepcopy(self.initial_game_state)
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

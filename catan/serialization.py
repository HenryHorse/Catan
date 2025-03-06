from dataclasses import dataclass
import numpy as np
from catan.game import Game
from catan.board import TileVertex, RoadVertex
from catan.player import Player
from catan.player import EndTurnAction, BuildSettlementAction, BuildCityAction, BuildRoadAction, BuyDevelopmentCardAction, UseDevelopmentCardAction, TradeAction

# Mapping Resources & Harbors to Numeric Values
RESOURCE_MAP = {
    None: 0, 'desert': 0, 'wood': 1, 'grain': 2, 'sheep': 3, 'ore': 4, 'brick': 5,
}

HARBOR_MAP = {
    None: 0, '3:1 any': 1, '2:1 ore': 2, '2:1 wood': 3, '2:1 brick': 4, '2:1 grain': 5, '2:1 sheep': 6
}

ACTION_MAP = {
    EndTurnAction: 1,
    BuildSettlementAction: 2,
    BuildCityAction: 3,
    BuildRoadAction: 4,
    BuyDevelopmentCardAction: 5,
    UseDevelopmentCardAction: 6,
    TradeAction: 7,
}


@dataclass(init=False)
class BrickRepresentation:
    size: int
    width: int
    height: int
    board: list[list[list[int]]]

    def __init__(self, size: int, num_players: int):
        self.size = size
        self.width = 4 * size + 1
        self.height = 2 * size + 1
        self.num_players = num_players
        # added chnanels for (0-numplayers-1 : player settlements, cities roads, -2: possible actions, -3: player stats (vps, army size, longest road), -4: current dev cards, -5: current resource count of player)
        self.board = np.zeros((num_players + 6, self.height, self.width), dtype=np.int32)

    def to_1d(self):
        return self.board.flatten()

    def board_state(self):
        return self.board[-1]

    def recursive_serialize(self, game: Game, center_tile: TileVertex, center: tuple[int, int] = None, visited=None):
        if visited is None:
            visited = set()
        if center is None:
            center = (2 * self.size, self.size)

        if center in visited:
            return
        visited.add(center)

        self.serialize_tile(game, center_tile, center)
        for neighbor in center_tile.adjacent_tiles:
            dx, dy = self.get_tile_displacement(center_tile, neighbor)
            self.recursive_serialize(game, neighbor, (center[0] + dx, center[1] + dy), visited)

    def serialize_tile(self, game: Game, tile: TileVertex, center: tuple[int, int]):
        x, y = center
        self.board[-6][y][x] = tile.number or 0  # Dice roll number
        self.board[-6][y][x - 1] = RESOURCE_MAP[tile.resource]  # Resource type
        self.board[-6][y][x + 1] = 1 if game.board.get_robber_tile() == tile else 0  # Robber presence

        for index, road_vertex in enumerate(tile.adjacent_road_vertices):
            next_vertex = tile.adjacent_road_vertices[(index + 1) % len(tile.adjacent_road_vertices)]
            int_dx, int_dy = self.get_intersection_displacement(tile, road_vertex)
            self.serialize_intersection(game, road_vertex, (x + int_dx, y + int_dy))

            road_dx, road_dy = self.get_road_displacement(tile, road_vertex)
            self.serialize_road(game, road_vertex, next_vertex, (x + road_dx, y + road_dy))

            if road_vertex.harbor:
                harbor_value = HARBOR_MAP.get(road_vertex.harbor_type, 0)
                self.board[-6][y + int_dy][x + int_dx] = harbor_value

    def serialize_intersection(self, game: Game, intersection: RoadVertex, position: tuple[int, int]):
        x, y = position
        for player_index, player_agent in enumerate(game.player_agents):
            player = player_agent.player
            for settlement in player.settlements:
                if settlement.location == intersection:
                    self.board[player_index][y][x] = 1  # Settlement placement
                    return
            for city in player.cities:
                if city.location == intersection:
                    self.board[player_index][y][x] = 2  # City placement
                    return

    def serialize_road(self, game: Game, intersection_1: RoadVertex, intersection_2: RoadVertex, position: tuple[int, int]):
        x, y = position
        for player_index, player_agent in enumerate(game.player_agents):
            player = player_agent.player
            for road in player.roads:
                if {road.rv1, road.rv2} == {intersection_1, intersection_2}:
                    self.board[player_index][y][x] = 1  # Road placement
                    return

    def serialize_player_info(self, game: Game):
        current_player_index = game.player_turn_index
        current_player = game.player_agents[current_player_index].player

        for player_index, player_agent in enumerate(game.player_agents):
            player = player_agent.player

            # 🔥 Resources
            for resource, count in player.resources.items():
                self.board[-5][0][RESOURCE_MAP[resource]] = count  # Store at fixed position

            # 🔥 Development Cards
            for card in player.unplayed_dev_cards:
                self.board[-4][0][card.value] += 1  # Store in Dev Card channel

            # 🔥 Player Stats
            self.board[-3][0][0] = player.victory_points
            self.board[-3][0][1] = player.army_size
            self.board[-3][0][2] = 1 if player.has_largest_army else 0
            self.board[-3][0][3] = player.longest_road_size
            self.board[-3][0][4] = 1 if player.has_longest_road else 0

            # 🔥 Available Actions
            available_actions = current_player.get_all_possible_actions(game.board, game.game_phase == GamePhase.SETUP)
            for action in available_actions:
                action_code = ACTION_MAP.get(type(action), 0)  
                self.board[-2][0][action_code] = 1  # Encode available actions

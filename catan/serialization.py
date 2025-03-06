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
        #3n+1 channels (3 per player (structures, resources, dev cards) + 1 for board state)
        self.board = np.zeros((3 * num_players + 1, self.height, self.width), dtype=np.int32)

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

        #Encode tile resources, dice numbers, and robber
        self.board[-1][y][x] = tile.number or 0  # Dice roll number
        self.board[-1][y][x - 1] = RESOURCE_MAP[tile.resource]  # Resource type
        self.board[-1][y][x + 1] = 1 if game.board.get_robber_tile() == tile else 0  # Robber

        for index, road_vertex in enumerate(tile.adjacent_road_vertices):
            next_vertex = tile.adjacent_road_vertices[(index + 1) % len(tile.adjacent_road_vertices)]
            int_dx, int_dy = self.get_intersection_displacement(tile, road_vertex)
            self.serialize_intersection(game, road_vertex, (x + int_dx, y + int_dy))

            road_dx, road_dy = self.get_road_displacement(tile, road_vertex)
            self.serialize_road(game, road_vertex, next_vertex, (x + road_dx, y + road_dy))

            if road_vertex.harbor:
                harbor_value = HARBOR_MAP.get(road_vertex.harbor_type, 0)
                self.board[-1][y + int_dy][x + int_dx] = harbor_value

    def serialize_intersection(self, game: Game, intersection: RoadVertex, position: tuple[int, int]):
        x, y = position
        for player_index, player_agent in enumerate(game.player_agents):
            player = player_agent.player
            player_channel = player_index  # Structures channel
            for settlement in player.settlements:
                if settlement.location == intersection:
                    self.board[player_channel][y][x] = 1  # Settlement placement
                    return
            for city in player.cities:
                if city.location == intersection:
                    self.board[player_channel][y][x] = 2  # City placement
                    return

    def serialize_road(self, game: Game, intersection_1: RoadVertex, intersection_2: RoadVertex, position: tuple[int, int]):
        x, y = position
        for player_index, player_agent in enumerate(game.player_agents):
            player = player_agent.player
            player_channel = player_index  # Structures channel
            for road in player.roads:
                if {road.rv1, road.rv2} == {intersection_1, intersection_2}:
                    self.board[player_channel][y][x] = 3  # Road placement
                    return

    def serialize_player_info(self, game: Game):
        for player_index, player_agent in enumerate(game.player_agents):
            player = player_agent.player
            resources_channel = self.num_players + player_index  # Resource channel
            dev_cards_channel = 2 * self.num_players + player_index  # Development cards channel

            # Encode resources
            for resource, count in player.resources.items():
                self.board[resources_channel][0][RESOURCE_MAP[resource]] = count  # Store at fixed position

            # Encode development cards
            for card in player.unplayed_dev_cards:
                self.board[dev_cards_channel][0][card.value] += 1  # Store in Dev Card channel

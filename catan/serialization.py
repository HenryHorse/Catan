from dataclasses import dataclass

from catan.board import Tile, Road, Resource, DevelopmentCard, RoadVertex, Harbor
from catan.game import Game, PlayerAgent
from catan.player import Player, EndTurnAction, BuildSettlementAction, BuildCityAction, BuildRoadAction, BuyDevelopmentCardAction, UseDevelopmentCardAction, TradeAction

BOARD_SIZE = 5

RESOURCE_MAP = {
    None: 0,
    Resource.WOOD: 1,
    Resource.GRAIN: 2,
    Resource.SHEEP: 3,
    Resource.ORE: 4,
    Resource.BRICK: 5,
}

HARBOR_MAP = {
    None: 0, '3:1 any': 1, '2:1 ore': 2, '2:1 wood': 3, '2:1 brick': 4, '2:1 grain': 5, '2:1 sheep': 6
}

BRICK_TILE_DISPLACEMENTS = [(2, 2), (4, 0), (2, -2), (-2, -2), (-4, 0), (-2, 2)]
BRICK_ROAD_VERTEX_DISPLACEMENTS = [(0, 1), (2, 1), (2, -1), (0, -1), (-2, -1), (-2, 1)]
BRICK_ROAD_DISPLACEMENTS = [(1, 1), (2, 0), (1, -1), (-1, -1), (-2, 0), (-1, 1)]



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
        self.board = [[[0 for _ in range(self.width)] for _ in range(self.height)] for _ in range(num_players + 1)]
        self.player_states = [
            [0] * 12, # Actions for current player (Fix Later) 7 + 5 + 5 * (Board Brick Size)
            *[[[0] * 13 for _ in range(num_players)]], # Resources for each player (Wood, Grain, Sheep, Ore, Brick) + 
                                                    # Rem Roads + Rem Cit + Rem Sett + Vict Points + If Long Road + Length Long Road + If Larg Arm + Size Arm
            [0] * 5 # Array of dev cards of player at given time
        ]
        

    def to_1d(self):
        return [cell for row in self.board for cell in row]
    
    def encode_player_states(self, game: Game, given_player: PlayerAgent):
        # Get action space for player (reset to all 0s first for every turn)

        self.player_states = [
            [0] * (7 + 5),  # Actions for the current player
            *[[[0] * 13 for _ in range(self.num_players)]],  # Resources for each player
            [0] * 5  # Development cards of the current player
        ]   

        actions = given_player.player._get_all_possible_actions_normal(game.board)
        for act in actions:
            if isinstance(act, EndTurnAction):
                self.player_states[0][0] = 1
            elif isinstance(act, BuildSettlementAction):
                self.player_states[0][1] = 1
            elif isinstance(act, BuildCityAction):
                self.player_states[0][2] = 1
            elif isinstance(act, BuildRoadAction):
                self.player_states[0][3] = 1
            elif isinstance(act, BuyDevelopmentCardAction):
                self.player_states[0][4] = 1
            elif isinstance(act, UseDevelopmentCardAction):
                self.player_states[0][5] = 1
            elif isinstance(act, TradeAction):
                self.player_states[0][6] = 1
                # Only encode 4:1 trades
                for resource in act.giving:
                    if act.giving.count(resource) == 4:  # Only consider 4:1 trades
                        resource_index = resource.value  # Get the enum index of the resource (order is )
                        self.player_states[0][7 + resource_index] = 1  # Mark that a 4:1 trade is possible
                #TODO: Add all possible road/settlement/city/knight options dependent on player
        # Get all info for each indiv player
        player_index = 0
        for player in game.player_agents:
            self.player_states[1][player_index][0] = player.player.resources[Resource.WOOD]
            self.player_states[1][player_index][1] = player.player.resources[Resource.GRAIN]
            self.player_states[1][player_index][2] = player.player.resources[Resource.SHEEP]
            self.player_states[1][player_index][3] = player.player.resources[Resource.ORE]
            self.player_states[1][player_index][4] = player.player.resources[Resource.BRICK]
            self.player_states[1][player_index][5] = player.player.free_roads_remaining
            self.player_states[1][player_index][6] = player.player.available_cities
            self.player_states[1][player_index][7] = player.player.available_settlements
            self.player_states[1][player_index][8] = player.player.get_victory_points()
            self.player_states[1][player_index][9] = 1 if player.player.has_longest_road else 0
            self.player_states[1][player_index][10] = player.player.longest_road_size
            self.player_states[1][player_index][11] = 1 if player.player.has_largest_army else 0
            self.player_states[1][player_index][12] = player.player.army_size
            player_index += 1
        # Given player's current Dev Cards
        for dev_card in given_player.player.unplayed_dev_cards:
            self.player_states[2][dev_card.value] += 1
    
    # Last channel in the matrix
    def board_state(self):
        return self.board[-1]
    
    def recursive_serialize(
            self,
            game: Game,
            center_tile: Tile | None = None,
            center: tuple[int, int] | None = None,
            visited: set[tuple[int, int]] | None = None):
        center_tile = center_tile or game.board.center_tile
        center = center or (2 * self.size, self.size)
        visited = visited or set()
        if center in visited: return
        visited.add(center)

        self.serialize_tile(game, center_tile, center)
        for i, neighbor in enumerate(center_tile.adjacent_tiles):
            if neighbor is None: continue
            dx, dy = BRICK_TILE_DISPLACEMENTS[i]
            self.recursive_serialize(game, neighbor, (center[0] + dx, center[1] + dy), visited)
    
    def serialize_tile(self, game: Game, tile: Tile, center: tuple[int, int]):
        x, y = center
        
        # Last channel for board state
        self.board[-1][y][x] = tile.number
        # Must be desert
        if (tile.resource == None):
            self.board[-1][y][x - 1] = 0
        else:
            self.board[-1][y][x - 1] = tile.resource.value + 1
        self.board[-1][y][x + 1] = 1 if tile.has_robber else 0

        for i, road_vertex in enumerate(tile.adjacent_road_vertices):
            if road_vertex is None: continue
            dx, dy = BRICK_ROAD_VERTEX_DISPLACEMENTS[i]
            self.serialize_road_vertex(game, road_vertex, (x + dx, y + dy))

            # stores harbor info
            harbor_value = 0
            if (road_vertex.harbor != None):
                harbor_value = road_vertex.harbor.value + 1
                self.board[-1][y+dy][x+dx] = harbor_value 
        
        for i, road in enumerate(tile.adjacent_roads):
            if road is None: continue
            dx, dy = BRICK_ROAD_DISPLACEMENTS[i]
            self.serialize_road(game, road, (x + dx, y + dy))
    
    def serialize_road_vertex(self, game: Game, intersection: RoadVertex, position: tuple[int, int]):
        x, y = position
        if intersection.owner is not None:
            self.board[intersection.owner][y][x] = 2 if intersection.has_city else 1
    
    def serialize_road(self, game: Game, road: Road, position: tuple[int, int]):
        x, y = position
        if road.owner is not None:
            self.board[road.owner][y][x] = 1
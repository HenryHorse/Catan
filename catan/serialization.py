from dataclasses import dataclass

from catan.board import Tile, Road, Resource, DevelopmentCard, RoadVertex, Harbor
from catan.game import Game, PlayerAgent
from catan.player import Player, EndTurnAction, BuildSettlementAction, BuildCityAction, BuildRoadAction, BuyDevelopmentCardAction, UseDevelopmentCardAction, TradeAction

BOARD_SIZE = 5

BRICK_TILE_DISPLACEMENTS = [(2, 2), (4, 0), (2, -2), (-2, -2), (-4, 0), (-2, 2)]
BRICK_ROAD_VERTEX_DISPLACEMENTS = [(0, 1), (2, 1), (2, -1), (0, -1), (-2, -1), (-2, 1)]
BRICK_ROAD_DISPLACEMENTS = [(1, 1), (2, 0), (1, -1), (-1, -1), (-2, 0), (-1, 1)]



@dataclass(init=False)
class BrickRepresentation:
    size: int
    width: int
    height: int
    board: list[list[list[int]]]

    def __init__(self, size: int, num_players: int, game: Game, agent_player_num: int):
        self.size = size
        self.width = 4 * size + 1
        self.height = 2 * size + 1
        self.num_players = num_players
        self.game = game
        self.agent_player_num = agent_player_num
        self.board = [[[0 for _ in range(self.width)] for _ in range(self.height)] for _ in range(num_players + 1)]
        self.player_states = [
            [0, 0, [[0 for _ in range(self.width)] for _ in range(self.height)], 0, [[0 for _ in range(self.width)] for _ in range(self.height)],
            0, [[0 for _ in range(self.width)] for _ in range(self.height)], 0, 0, [[0 for _ in range(self.width)] for _ in range(self.height)],
            0, [0, 0, 0, 0, 0], [[0 for _ in range(self.width)] for _ in range(self.height)]], # Actions for current player 
            *[[[0] * 13 for _ in range(self.num_players)]], # Resources for each player (Wood, Grain, Sheep, Ore, Brick) + 
                                                    # Rem Roads + Rem Cit + Rem Sett + Vict Points + If Long Road + Length Long Road + If Larg Arm + Size Arm
            [0] * 5 # Array of dev cards of player at given time
        ]

    def flatten_nested_list(self, nested_list):
        """Recursively flatten a nested list into a 1D list."""
        flat_list = []
        for item in nested_list:
            if isinstance(item, list):
                flat_list.extend(self.flatten_nested_list(item))
            else:
                flat_list.append(item)
        return flat_list
    
    def reinitialize(self):
        self.player_states = self.player_states = [
            [0, 0, [[0 for _ in range(self.width)] for _ in range(self.height)], 0, [[0 for _ in range(self.width)] for _ in range(self.height)],
            0, [[0 for _ in range(self.width)] for _ in range(self.height)], 0, 0, [[0 for _ in range(self.width)] for _ in range(self.height)],
            0, [0, 0, 0, 0, 0], [[0 for _ in range(self.width)] for _ in range(self.height)]], 
            *[[[0] * 13 for _ in range(self.num_players)]], 
            [0] * 5]
        
    def recursive_serialize_for_player_states(
            self,
            game: Game,
            center_tile: Tile | None = None,
            center: tuple[int, int] | None = None,
            visited: set[tuple[int, int]] | None = None):

        if self.player_states[0][1] == 1:
            self.recursive_serialize()

    def to_1d(self):
        return [cell for row in self.board for cell in row]
    
    def encode_player_states(self, game: Game, given_player: Player):
        # Reset the board and player states
        self.reinitialize()

        # Get action space for player
        actions = given_player._get_all_possible_actions_normal(game.board)
        print(f"Possible actions: {actions}")

        # Encode actions into player_states
        for act in actions:
            if isinstance(act, EndTurnAction):
                self.player_states[0][0] = 1
            elif isinstance(act, BuildSettlementAction): # 0/1 and whole map copy
                self.player_states[0][1] = 1
            elif isinstance(act, BuildCityAction): # 0/1 and whole map copy
                self.player_states[0][3] = 1
            elif isinstance(act, BuildRoadAction): # 0/1 and whole map copy
                self.player_states[0][5] = 1
            elif isinstance(act, BuyDevelopmentCardAction): # Just 0/1
                self.player_states[0][7] = 1
            elif isinstance(act, UseDevelopmentCardAction):
                self.player_states[0][8] = 1
            elif isinstance(act, TradeAction):
                self.player_states[0][10] = 1
                # Only encode 4:1 trades (I could be wrong on this)
                for resource in act.giving:
                    if act.giving.count(resource) == 4:  # Only consider 4:1 trades
                        resource_index = resource.value  # Get the enum index of the resource 
                        self.player_states[0][11][resource_index] = 1  # Mark that a 4:1 trade is possible
        
        self.recursive_serialize(self.game, self.game.board.center_tile, None, None, True, actions)

        # Encode player states
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
        for dev_card in given_player.unplayed_dev_cards:
            self.player_states[2][dev_card.value] += 1

        self.player_states = self.flatten_nested_list(self.player_states)

        
    # Last channel in the matrix
    def board_state(self):
        return self.board[-1]
    
    def recursive_serialize(
            self,
            game: Game,
            center_tile: Tile | None = None,
            center: tuple[int, int] | None = None,
            visited: set[tuple[int, int]] | None = None,
            action_flag: bool = False,
            actions: list = []):
        center_tile = center_tile or game.board.center_tile
        center = center or (self.width // 2, self.height // 2)
        visited = visited or set()
        if center in visited:
            return
        visited.add(center)

        print(f"Serializing tile at center: {center}")
        self.serialize_tile(game, center_tile, center, action_flag, actions)
        for i, neighbor in enumerate(center_tile.adjacent_tiles):
            if neighbor is None:
                continue
            dx, dy = BRICK_TILE_DISPLACEMENTS[i]
            new_center = (center[0] + dx, center[1] + dy)
            print(f"Moving to neighbor at: {new_center}")
            self.recursive_serialize(game, neighbor, new_center, visited, action_flag, actions)
        
    def serialize_tile(self, game: Game, tile: Tile, center: tuple[int, int], action_flag: bool, actions):
        x, y = center

        # Validate coordinates
        if not (0 <= x < self.width and 0 <= y < self.height):
            print(f"Warning: Invalid coordinates (x={x}, y={y}) for board of size {self.width}x{self.height}")
            return

        # Last channel for board state
        self.board[-1][y][x] = tile.number

        # Validate x - 1 before accessing
        if x - 1 >= 0:
            if tile.resource is None:
                self.board[-1][y][x - 1] = 0
            else:
                self.board[-1][y][x - 1] = tile.resource.value + 1

        # Validate x + 1 before accessing
        if x + 1 < self.width:
            self.board[-1][y][x + 1] = 1 if tile.has_robber else 0

        # Serialize road vertices and roads
        for i, road_vertex in enumerate(tile.adjacent_road_vertices):
            if road_vertex is None:
                continue
            dx, dy = BRICK_ROAD_VERTEX_DISPLACEMENTS[i]
            new_x, new_y = x + dx, y + dy

            # Validate new coordinates
            if 0 <= new_x < self.width and 0 <= new_y < self.height:
                self.serialize_road_vertex(game, road_vertex, (new_x, new_y), action_flag, actions)

                # Store harbor info
                harbor_value = 0
                if road_vertex.harbor is not None:
                    harbor_value = road_vertex.harbor.value + 1
                    self.board[-1][new_y][new_x] = harbor_value
                    if action_flag and road_vertex.owner == self.agent_player_num:
                        self.player_states[0][12][new_y][new_x] = harbor_value

        for i, road in enumerate(tile.adjacent_roads):
            if road is None:
                continue
            dx, dy = BRICK_ROAD_DISPLACEMENTS[i]
            new_x, new_y = x + dx, y + dy

            # Validate new coordinates
            if 0 <= new_x < self.width and 0 <= new_y < self.height:
                self.serialize_road(game, road, (new_x, new_y), action_flag, actions)
    
    def serialize_road_vertex(self, game: Game, intersection: RoadVertex, position: tuple[int, int], action_flag: bool, actions):
        x, y = position
        if intersection.owner is not None:
            self.board[intersection.owner][y][x] = 2 if intersection.has_city else 1
        if action_flag:
            for action in actions:
                if isinstance(action, BuildCityAction) and action.road_vertex == intersection:
                    self.player_states[0][4][y][x] = 1
                elif isinstance(action, BuildSettlementAction) and action.road_vertex == intersection:
                    self.player_states[0][2][y][x] = 1            
    
    def serialize_road(self, game: Game, road: Road, position: tuple[int, int], action_flag, actions):
        x, y = position
        if road.owner is not None:
            self.board[road.owner][y][x] = 1
        if action_flag:
            for action in actions:
                if isinstance(action, BuildRoadAction) and action.road == road:
                    self.player_states[0][6][y][x] = 1
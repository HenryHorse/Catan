from dataclasses import dataclass

from catan.board import Tile, Road, Resource, DevelopmentCard, RoadVertex, Harbor
from catan.game import Game, PlayerAgent
from catan.player import Player, EndTurnAction, BuildSettlementAction, BuildCityAction, BuildRoadAction, BuyDevelopmentCardAction, UseDevelopmentCardAction, TradeAction

from globals import DEV_MODE

BOARD_SIZE = 5


@dataclass(init=False)
class BrickRepresentation:
    size: int
    width: int
    height: int
    center: tuple[int, int]
    num_players: int
    game: Game
    agent_player_num: int
    board: list[list[list[int]]]
    player_states: list

    def __init__(self, size: int, num_players: int, game: Game, agent_player_num: int):
        self.size = size
        self.width = 4 * size + 1
        self.height = 2 * size + 1
        self.center = self.width // 2, self.height // 2
        self.num_players = num_players
        self.game = game
        self.agent_player_num = agent_player_num
        self.board = [[[0 for _ in range(self.width)] for _ in range(self.height)] for _ in range(num_players + 1)]
        self.reinitialize()
    
    def get_tile_brick_coords(self, tile: Tile) -> tuple[int, int]:
        cube = tile.cube_coords
        return (cube.q * 2) + self.center[0], (-cube.r * 4 - cube.q * 2) + self.center[1]

    def get_road_vertex_brick_coords(self, road_vertex: RoadVertex) -> tuple[int, int]:
        cube = road_vertex.cube_coords
        return (cube.q * 2) + self.center[0], (((cube.r - cube.s) // 3) * -2 - 1) + self.center[1]

    def get_road_brick_coords(self, road: Road) -> tuple[int, int]:
        vertex_1 = self.get_road_vertex_brick_coords(road.endpoints[0])
        vertex_2 = self.get_road_vertex_brick_coords(road.endpoints[1])
        return (vertex_1[0] + vertex_2[0]) // 2, (vertex_1[1] + vertex_2[1]) // 2

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
        self.player_states = [
        [0], # end turn
        [0], # buy dev card
        [0], # road building card
        [0], # year of plenty
        [0], # monopoly card
        [0,0,0,0,0], # 4:1 bank trade 1 option per resouce
        [0,0,0,0,0], # 3:1 harbor trade 1 option per resouce
        [0,0,0,0,0], # 2:1 harbor trade 1 option per resouce
        [[[0, #Road 
           0, #settlment
           0, #city
           0, #dev card: Knight card
           ] for _ in range(self.width)] for _ in range(self.height)],
        [[0] * 13 for _ in range(self.num_players)],
        # Resources for each player (Wood, Grain, Sheep, Ore, Brick) + 
                                                # Rem Roads + Rem Cit + Rem Sett + Vict Points + If Long Road + Length Long Road + If Larg Arm + Size Arm
        [0, 0, 0, 0, 0] # Unplayed dev cards: Knight, Road Building, Year of Plenty, Monopoly, Victory Point
        ]

    def to_1d(self):
        return [cell for row in self.board for cell in row]
    
    def encode_player_states(self, game: Game, given_player: Player):
        # Reset the board and player states
        self.reinitialize()

        # Get action space for player
        actions = given_player._get_all_possible_actions_normal(game.board)
        if DEV_MODE:
            print(f"Possible actions: {actions}")

        # Encode actions into player_states
        for act in actions:
            if isinstance(act, EndTurnAction):
                self.player_states[0] = 1
            elif isinstance(act, BuildSettlementAction): 
                coords = self.get_road_vertex_brick_coords(act.road_vertex)
                self.player_states[8][coords[1]][coords[0]][1] = 1
            elif isinstance(act, BuildCityAction): # 0/1 and whole map copy
                coords = self.get_road_vertex_brick_coords(act.road_vertex)
                self.player_states[8][coords[1]][coords[0]][2] = 1
            elif isinstance(act, BuildRoadAction): # 0/1 and whole map copy
                coords = self.get_road_brick_coords(act.road)
                self.player_states[8][coords[1]][coords[0]][0] = 1
            elif isinstance(act, BuyDevelopmentCardAction): # Just 0/1
                self.player_states[1] = 1
            elif isinstance(act, UseDevelopmentCardAction):
                dev_card_type = act.card
                match dev_card_type:
                    case DevelopmentCard.KNIGHT:
                        for tile in game.board.tiles.values():
                            if tile.has_robber:
                                continue
                            coords = self.get_tile_brick_coords(tile.cube_coords)
                            self.player_states[8][coords[1]][coords[0]][3] = 1
                        break
                    case DevelopmentCard.ROAD_BUILDING:
                        self.player_states[2] = 1
                        break
                    case DevelopmentCard.YEAR_OF_PLENTY:
                        self.player_states[3] = 1
                        break
                    case DevelopmentCard.MONOPOLY:
                        self.player_states[4] = 1
                        break
            elif isinstance(act, TradeAction):
                # Only encode 4:1 trades (I could be wrong on this)
                for resource in act.giving:
                    resource_index = resource.value  # Get the enum index of the resource
                    if act.giving.count(resource) == 4:  # Only consider 4:1 trades
                        self.player_states[5][resource_index] = 1  # Mark that a 4:1 trade is possible
                    elif act.giving.count(resource) == 3:  # Only consider 4:1 trades
                        self.player_states[6][resource_index] = 1  # Mark that a 4:1 trade is possible
                    elif act.giving.count(resource) == 2:  # Only consider 4:1 trades
                        self.player_states[7][resource_index] = 1  # Mark that a 4:1 trade is possible

        # Encode player states
        for player_index, player in enumerate(game.player_agents):
            self.player_states[9][player_index][0] = player.player.resources[Resource.WOOD]
            self.player_states[9][player_index][1] = player.player.resources[Resource.GRAIN]
            self.player_states[9][player_index][2] = player.player.resources[Resource.SHEEP]
            self.player_states[9][player_index][3] = player.player.resources[Resource.ORE]
            self.player_states[9][player_index][4] = player.player.resources[Resource.BRICK]
            self.player_states[9][player_index][5] = player.player.free_roads_remaining
            self.player_states[9][player_index][6] = player.player.available_cities
            self.player_states[9][player_index][7] = player.player.available_settlements
            self.player_states[9][player_index][8] = player.player.get_victory_points()
            self.player_states[9][player_index][9] = 1 if player.player.has_longest_road else 0
            self.player_states[9][player_index][10] = player.player.longest_road_size
            self.player_states[9][player_index][11] = 1 if player.player.has_largest_army else 0
            self.player_states[9][player_index][12] = player.player.army_size
        
        # Given player's current Dev Cards
        for dev_card in given_player.unplayed_dev_cards:
            self.player_states[2][dev_card.card_type.value] += 1

        self.player_states = self.flatten_nested_list(self.player_states)

        
    # Last channel in the matrix
    def board_state(self):
        return self.board[-1]
    
    def encode_board_recursive(
            self,
            game: Game,
            tile: Tile | None = None,
            visited: set[tuple[int, int]] | None = None):
        tile = tile or game.board.center_tile
        visited = visited or set()
        brick_coords = self.get_tile_brick_coords(tile)
        if brick_coords in visited:
            return
        visited.add(brick_coords)

        self.serialize_tile(game, tile)
        for neighbor in tile.adjacent_tiles:
            self.encode_board_recursive(game, neighbor, visited)

    def serialize_tile(self, game: Game, tile: Tile):
        x, y = self.get_tile_brick_coords(tile)
        if tile.resource is not None:
            self.board[-1][y][x - 1] = tile.resource.value + 1
        self.board[-1][y][x] = tile.number
        self.board[-1][y][x + 1] = 1 if tile.has_robber else 0
        for vertex in tile.adjacent_road_vertices:
            self.serialize_road_vertex(vertex)
        for road in tile.adjacent_roads:
            self.serialize_road(road)
    
    def serialize_road_vertex(self, intersection: RoadVertex):
        x, y = self.get_road_vertex_brick_coords(intersection)
        if intersection.owner is not None:
            self.board[intersection.owner][y][x] = 2 if intersection.has_city else 1
        if intersection.harbor is not None:
            self.board[-1][y][x] = intersection.harbor.value + 1
    
    def serialize_road(self, road: Road):
        x, y = self.get_road_brick_coords(road)
        if road.owner is not None:
            self.board[road.owner][y][x] = 1
    
    def encode_all(self, given_player: Player):
        self.encode_board_recursive(self.game)
        self.encode_player_states(self.game, given_player)

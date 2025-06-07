from dataclasses import dataclass
from typing import TypeVar, Union
from collections import Counter

import numpy as np

from catan.board import Board, Tile, Road, Resource, DevelopmentCardType, RoadVertex
from catan.game import Game, GamePhase
from catan.player import Player, Action, EndTurnAction, BuildSettlementAction, \
    BuildCityAction, BuildRoadAction, BuyDevelopmentCardAction, UseDevelopmentCardAction, \
    TradeAction
from catan.util import CubeCoordinates, print_debug

from globals import ACTION_DIM

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
        return (cube.q * 2) + self.center[0], ((cube.s - cube.r) // 3) * 2 + self.center[1]

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
        actions = given_player.get_all_possible_actions(game.board, game.game_phase == GamePhase.SETUP)
        print_debug(f"Possible actions: {actions}")

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
                    case DevelopmentCardType.KNIGHT:
                        for tile in game.board.tiles.values():
                            if tile.has_robber:
                                continue
                            coords = self.get_tile_brick_coords(tile.cube_coords)
                            self.player_states[8][coords[1]][coords[0]][3] = 1
                        break
                    case DevelopmentCardType.ROAD_BUILDING:
                        self.player_states[2] = 1
                        break
                    case DevelopmentCardType.YEAR_OF_PLENTY:
                        self.player_states[3] = 1
                        break
                    case DevelopmentCardType.MONOPOLY:
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

        self.serialize_tile(tile)
        for neighbor in tile.adjacent_tiles:
            self.encode_board_recursive(game, neighbor, visited)

    def serialize_tile(self, tile: Tile):
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


# Neutral actions carry no information about the player or game state. They are used to
# represent actions in a neutral context so that they can be used in a shared action space.

@dataclass(frozen=True)
class NeutralEndTurnAction:
    pass

@dataclass(frozen=True)
class NeutralBuildSettlementAction:
    road_vertex_coords: CubeCoordinates

@dataclass(frozen=True)
class NeutralBuildCityAction:
    road_vertex_coords: CubeCoordinates

@dataclass(frozen=True)
class NeutralBuildRoadAction:
    endpoint_coords: tuple[CubeCoordinates, CubeCoordinates]

@dataclass(frozen=True)
class NeutralBuyDevelopmentCardAction:
    pass

@dataclass(frozen=True)
class NeutralUseDevelopmentCardAction:
    card_type: DevelopmentCardType

@dataclass(frozen=True)
class NeutralTradeAction:
    giving: tuple[Resource]
    receiving: tuple[Resource]

    def simple_trade_options(giving: Resource, count: int) -> list['NeutralTradeAction']:
        return [NeutralTradeAction((giving,) * count, (resource,)) for resource in Resource if resource != giving]


NeutralAction = Union[
    NeutralEndTurnAction,
    NeutralBuildSettlementAction,
    NeutralBuildCityAction,
    NeutralBuildRoadAction,
    NeutralBuyDevelopmentCardAction,
    NeutralUseDevelopmentCardAction,
    NeutralTradeAction
]

def action_to_neutral_action(action: Action) -> NeutralAction:
    """Convert a Catan action to a neutral action."""
    if isinstance(action, EndTurnAction):
        return NeutralEndTurnAction()
    elif isinstance(action, BuildSettlementAction):
        return NeutralBuildSettlementAction(action.road_vertex.cube_coords)
    elif isinstance(action, BuildCityAction):
        return NeutralBuildCityAction(action.road_vertex.cube_coords)
    elif isinstance(action, BuildRoadAction):
        return NeutralBuildRoadAction((action.road.endpoints[0].cube_coords, action.road.endpoints[1].cube_coords))
    elif isinstance(action, BuyDevelopmentCardAction):
        return NeutralBuyDevelopmentCardAction()
    elif isinstance(action, UseDevelopmentCardAction):
        return NeutralUseDevelopmentCardAction(action.card.card_type)
    elif isinstance(action, TradeAction):
        return NeutralTradeAction(tuple(action.giving), tuple(action.receiving))
    else:
        raise ValueError(f"Unknown action type: {type(action)}")

# TODO: more verbose errors if the action is not found in the possible actions
def neutral_action_to_action(neutral_action: NeutralAction, possible_actions: list[Action]) -> Action:
    """Convert a neutral action back to a Catan action."""
    if isinstance(neutral_action, NeutralEndTurnAction):
        return EndTurnAction()
    elif isinstance(neutral_action, NeutralBuildSettlementAction):
        for action in possible_actions:
            if isinstance(action, BuildSettlementAction) and \
                    action.road_vertex.cube_coords == neutral_action.road_vertex_coords:
                return action
    elif isinstance(neutral_action, NeutralBuildCityAction):
        for action in possible_actions:
            if isinstance(action, BuildCityAction) and \
                    action.road_vertex.cube_coords == neutral_action.road_vertex_coords:
                return action
    elif isinstance(neutral_action, NeutralBuildRoadAction):
        for action in possible_actions:
            if isinstance(action, BuildRoadAction) and \
                    (action.road.endpoints[0].cube_coords == neutral_action.endpoint_coords[0] and
                     action.road.endpoints[1].cube_coords == neutral_action.endpoint_coords[1]):
                return action
    elif isinstance(neutral_action, NeutralBuyDevelopmentCardAction):
        return BuyDevelopmentCardAction()
    elif isinstance(neutral_action, NeutralUseDevelopmentCardAction):
        for action in possible_actions:
            if isinstance(action, UseDevelopmentCardAction) and \
                    action.card.card_type == neutral_action.card_type:
                return action
    elif isinstance(neutral_action, NeutralTradeAction):
        for action in possible_actions:
            if isinstance(action, TradeAction) and \
                    (Counter(action.giving) == Counter(neutral_action.giving) and
                     Counter(action.receiving) == Counter(neutral_action.receiving)):
                return action
    raise ValueError(f"Unknown neutral action type: {type(neutral_action)}")

T = TypeVar('T')

class ActionSpace:
    actions: list[NeutralAction]
    action_to_idx: dict[NeutralAction, int]

    def __init__(self, board: Board):
        actions: list[NeutralAction] = [NeutralEndTurnAction()]
        actions.extend(NeutralBuildSettlementAction(road_vertex.cube_coords) for road_vertex in board.road_vertices.values())
        actions.extend(NeutralBuildCityAction(road_vertex.cube_coords) for road_vertex in board.road_vertices.values())
        actions.extend(NeutralBuildRoadAction((road.endpoints[0].cube_coords, road.endpoints[1].cube_coords)) for road in board.roads)
        actions.append(NeutralBuyDevelopmentCardAction())
        actions.extend(NeutralUseDevelopmentCardAction(card_type) for card_type in DevelopmentCardType if card_type != DevelopmentCardType.VICTORY_POINT)
        for resource in Resource:
            actions.extend(NeutralTradeAction.simple_trade_options(resource, 4))
            actions.extend(NeutralTradeAction.simple_trade_options(resource, 3))
            actions.extend(NeutralTradeAction.simple_trade_options(resource, 2))
        
        if len(actions) != ACTION_DIM:
            print_debug(f'Warning: Expected {ACTION_DIM} actions, got {len(actions)}')

        self.actions = actions
        self.action_to_idx = {action: idx for idx, action in enumerate(actions)}
    
    def __len__(self) -> int:
        """Return the number of actions in the action space."""
        return len(self.actions)
    
    def get_action_index(self, action: NeutralAction) -> int:
        """Convert a Catan action to an index"""
        if action not in self.action_to_idx:
            print_debug(f"Warning: Action {action} not found in action space.")
        return self.action_to_idx[action]
    
    def filter_list_from_possible_actions(self, possible_actions: list[NeutralAction], original_list: list[T]) -> list[T]:
        """Filter a list of any arbitrary type based on the possible actions"""
        if len(original_list) != len(self.actions):
            print_debug(f"Warning: Original list length {len(original_list)} does not match actions length {len(self.actions)}")
        return [item for item, action in zip(original_list, self.actions) if action in possible_actions]
    
    def filter_array_from_possible_actions(self, possible_actions: list[NeutralAction], original_array: np.ndarray) -> np.ndarray:
        """Filter a numpy array based on the possible actions"""
        filtered_list = self.filter_list_from_possible_actions(possible_actions, original_array.tolist())
        return np.array(filtered_list)
    
    def sort_actions(self, possible_actions: list[NeutralAction]) -> list[NeutralAction]:
        """Sort the actions based on the order in the action space"""
        return [action for action in self.actions if action in possible_actions]
    
    def debug_actions(self):
        """Logs all actions in the action space as debug information."""
        for idx, action in enumerate(self.actions):
            print_debug(f"Action {idx}: {action}")
        print_debug(f"Total actions: {len(self.actions)}")

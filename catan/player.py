from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Union, TYPE_CHECKING
import random

from catan.board import Board, DevelopmentCardType, Resource, RoadVertex, Road, Harbor, DevelopmentCard
from catan.error import CatanException
from catan.constants import *
if TYPE_CHECKING:
    from catan.game import Game

from catan.util import print_debug

from globals import ACTION_DIM


@dataclass
class EndTurnAction:
    pass

@dataclass
class BuildSettlementAction:
    road_vertex: RoadVertex
    pay_for: bool = True

@dataclass
class BuildCityAction:
    road_vertex: RoadVertex
    pay_for: bool = True

@dataclass
class BuildRoadAction:
    road: Road
    pay_for: bool = True

@dataclass
class BuyDevelopmentCardAction:
    pass

@dataclass
class UseDevelopmentCardAction:
    card: DevelopmentCard

@dataclass
class TradeAction:
    giving: list[Resource]
    receiving: list[Resource]

    def simple_trade_options(giving: Resource, count: int) -> list['TradeAction']:
        return [TradeAction([giving] * count, [resource]) for resource in Resource if resource != giving]

Action = Union[
    EndTurnAction,
    BuildSettlementAction,
    BuildCityAction,
    BuildRoadAction,
    BuyDevelopmentCardAction,
    UseDevelopmentCardAction,
    TradeAction
]


class Player:
    index: int
    color: tuple[int, int, int]

    resources: dict[Resource, int]
    unplayed_dev_cards: list[DevelopmentCard]
    played_dev_cards: list[DevelopmentCard]

    # for the road building development card
    free_roads_remaining: int
    # for the setup phase
    setup_last_settlement: RoadVertex | None

    available_settlements: int
    settlements: list[RoadVertex]
    available_cities: int
    cities: list[RoadVertex]
    available_roads: int
    roads: list[Road]
    
    longest_road_size: int
    longest_road_path: list[Road]
    has_longest_road: bool
    army_size: int
    has_largest_army: bool

    def __init__(self, index: int, color: tuple[int, int, int]):
        self.index = index
        self.color = color
        
        self.resources = {resource: 0 for resource in Resource}
        self.unplayed_dev_cards = []
        self.played_dev_cards = []
        
        self.free_roads_remaining = 0
        self.setup_last_settlement = None

        self.available_settlements = 5
        self.settlements = []
        self.available_cities = 4
        self.cities = []
        self.available_roads = 15
        self.roads = []

        self.longest_road_size = 0
        self.longest_road_path = []
        self.has_longest_road = False
        self.army_size = 0
        self.has_largest_army = False

        self.pending_settlement_for_road = None
    
    def get_victory_points(self) -> int:
        return (len(self.settlements) + len(self.cities) +
            sum(1 for card in self.played_dev_cards if card.card_type == DevelopmentCardType.VICTORY_POINT) +
            sum(1 for card in self.unplayed_dev_cards if card.card_type == DevelopmentCardType.VICTORY_POINT) +
            (2 if self.has_longest_road else 0) +
            (2 if self.has_largest_army else 0))
    
    def get_resources_array(self) -> list[Resource]:
        return [resource for resource, count in self.resources.items() for _ in range(count)]
    
    def get_resource_count(self) -> int:
        return sum(self.resources.values())
    
    def can_afford(self, cost: list[Resource]) -> bool:
        cost_dict = Counter(cost)
        return all(self.resources[resource] >= cost_dict[resource] for resource in cost_dict)
    
    def pay_for(self, cost: list[Resource]):
        cost_dict = Counter(cost)
        for resource in cost_dict:
            self.resources[resource] -= cost_dict[resource]
    
    def give_resource(self, resource: Resource, count: int = 1):
        self.resources[resource] += count
    
    def take_random_resources(self, count: int) -> list[Resource]:
        array = self.get_resources_array()
        if len(array) < count:
            raise CatanException('Not enough resources')
        resources = random.sample(array, count)
        for resource in resources:
            self.resources[resource] -= 1
        return resources
    
    def build_settlement(self, road_vertex: RoadVertex, pay_for: bool = True):
        if road_vertex.has_settlement:
            raise CatanException('Settlement already built here')
        if self.available_settlements == 0:
            raise CatanException('No available settlements')
        if pay_for and not self.can_afford(SETTLEMENT_COST):
            raise CatanException('Cannot afford settlement')

        self.settlements.append(road_vertex)
        road_vertex.owner = self.index
        road_vertex.has_settlement = True

        self.available_settlements -= 1
        if pay_for:
            self.pay_for(SETTLEMENT_COST)

        self.pending_settlement_for_road = road_vertex
    
    def build_city(self, road_vertex: RoadVertex, pay_for: bool = True):
        if road_vertex.has_city:
            raise CatanException('City already built here')
        if not road_vertex.has_settlement:
            raise CatanException('No settlement here')
        if road_vertex.owner != self.index:
            raise CatanException('Not your settlement')
        if self.available_cities == 0:
            raise CatanException('No available cities')
        if pay_for and not self.can_afford(CITY_COST):
            raise CatanException('Cannot afford city')
        
        self.cities.append(road_vertex)
        road_vertex.has_city = True

        self.available_cities -= 1
        if pay_for:
            self.pay_for(CITY_COST)
    
    def build_road(self, road: Road, game, pay_for: bool = True):
        if road.owner is not None:
            raise CatanException('Road already built here')
        if self.available_roads == 0:
            raise CatanException('No available roads')
        if pay_for and not self.can_afford(ROAD_COST):
            raise CatanException('Cannot afford road')
        
        self.roads.append(road)
        road.owner = self.index

        self.available_roads -= 1
        if pay_for:
            self.pay_for(ROAD_COST)
    
    def buy_development_card(self, board: Board):
        if not self.can_afford(DEVELOPMENT_CARD_COST):
            raise CatanException('Cannot afford development card')
        
        card = board.development_card_deck.draw()
        self.unplayed_dev_cards.append(card)
        self.pay_for(DEVELOPMENT_CARD_COST)

    def find_longest_road_size(self) -> int:
        vertices_to_check: set[RoadVertex] = set()
        for road in self.roads:
            for vertex in road.endpoints:
                vertices_to_check.add(vertex)

        max_length = 0
        best_path = []

        def dfs(vertex: RoadVertex, visited_roads: set[Road], current_length: int, current_path: list[Road]):
            nonlocal max_length, best_path
            if current_length > max_length:
                max_length = current_length
                best_path = current_path.copy() 
            # Opposing player settlements break up road chains
            if vertex.owner != self.index and vertex.owner is not None:
                return

            for road in vertex.adjacent_roads:
                if road.owner == self.index and road not in visited_roads:
                    visited_roads.add(road)
                    next_vertex = road.endpoints[0] if road.endpoints[0] != vertex else road.endpoints[1]
                    current_path.append(road)
                    dfs(next_vertex, visited_roads, current_length + 1, current_path)
                    current_path.pop()
                    visited_roads.remove(road)

        for vertex in vertices_to_check:
            dfs(vertex, set(), 0, [])

        self.longest_road_size = max_length
        self.longest_road_path = best_path
        return max_length
    
    def is_valid_settlement_location(self, road_vertex: RoadVertex, needs_road: bool = True) -> bool:
        if road_vertex.owner is not None:
            return False
        if needs_road and not any(road.owner == self.index for road in road_vertex.adjacent_roads):
            return False
        for neighbor in road_vertex.adjacent_road_vertices:
            if neighbor.has_settlement:
                return False
        return True
    
    def is_valid_city_location(self, road_vertex: RoadVertex) -> bool:
        return road_vertex.has_settlement and not road_vertex.has_city and road_vertex.owner == self.index

    def is_valid_road_location(self, road: Road, is_setup: bool = False) -> bool:
        if road.owner is not None:
            return False

        if is_setup:
            if self.pending_settlement_for_road is not None:
                if self.pending_settlement_for_road in road.endpoints:
                    return True
                else:
                    return False

        for road_vertex in road.endpoints:
            if road_vertex.owner == self.index:
                return True
            elif road_vertex.owner is None:
                for connected_road in road_vertex.adjacent_roads:
                    if connected_road.owner == self.index:
                        return True
        return False
    
    def get_available_roads_around(self, road_vertex: RoadVertex) -> list[Road]:
        return [road for road in road_vertex.adjacent_roads if road.owner == None]
    
    def has_harbor(self, harbor_or_resource: Harbor | Resource) -> bool:
        if isinstance(harbor_or_resource, Harbor):
            return any(settlement.harbor == harbor_or_resource for settlement in self.settlements)
        resource = harbor_or_resource
        if resource == Resource.WOOD:
            return self.has_harbor(Harbor.WOOD)
        elif resource == Resource.GRAIN:
            return self.has_harbor(Harbor.GRAIN)
        elif resource == Resource.SHEEP:
            return self.has_harbor(Harbor.SHEEP)
        elif resource == Resource.ORE:
            return self.has_harbor(Harbor.ORE)
        elif resource == Resource.BRICK:
            return self.has_harbor(Harbor.BRICK)
        return False
    
    def can_trade_4_to_1(self, with_resource: Resource) -> bool:
        return self.can_afford([with_resource] * 4)
    
    def can_trade_3_to_1(self, with_resource: Resource | None = None) -> bool:
        has_harbor = self.has_harbor(Harbor.THREE_TO_ONE)
        if has_harbor and with_resource is not None:
            return self.can_afford([with_resource] * 3)
        return has_harbor
    
    def can_trade_2_to_1(self, resource: Resource, check_count: bool = False) -> bool:
        return self.has_harbor(resource) and (not check_count or self.resources[resource] >= 2)
    
    def get_all_possible_actions(self, board: Board, is_setup: bool) -> list[Action]:
        if self.free_roads_remaining > 0:
            self.free_roads_remaining -= 1
            return [BuildRoadAction(road, False) for road in board.roads if self.is_valid_road_location(road)]
        if is_setup:
            return self._get_all_possible_actions_placing(board)
        return self._get_all_possible_actions_normal(board)

    def _get_all_possible_actions_placing(self, board: Board) -> list[Action]:
        actions: list[Action] = []
        if self.setup_last_settlement is None:
            for cube_coord, road_vertex in board.road_vertices.items():
                if self.is_valid_settlement_location(road_vertex, needs_road=False):
                    actions.append(BuildSettlementAction(road_vertex, False))
        else:
            for road in self.get_available_roads_around(self.setup_last_settlement):
                actions.append(BuildRoadAction(road, False))
        return actions

    def _get_all_possible_actions_normal(self, board: Board) -> list[Action]:
        actions: list[Action] = [EndTurnAction()]
        if self.available_settlements > 0:
            for cube_coord, road_vertex in board.road_vertices.items():
                if self.is_valid_settlement_location(road_vertex) and self.can_afford(SETTLEMENT_COST):
                    actions.append(BuildSettlementAction(road_vertex))
        if self.available_cities > 0:
            for road_vertex in self.settlements:
                if self.is_valid_city_location(road_vertex) and self.can_afford(CITY_COST):
                    actions.append(BuildCityAction(road_vertex))
        if self.available_roads > 0:
            for road in board.roads:
                if self.is_valid_road_location(road) and self.can_afford(ROAD_COST):
                    actions.append(BuildRoadAction(road))
        if board.development_card_deck.remaining_cards() > 0 and self.can_afford(DEVELOPMENT_CARD_COST):
            actions.append(BuyDevelopmentCardAction())
        unique_cards = {}
        for card in self.unplayed_dev_cards:
            if card.card_type != DevelopmentCardType.VICTORY_POINT and not card.on_cooldown:
                if card.card_type not in unique_cards:
                    unique_cards[card.card_type] = card
        for unique_card in unique_cards.values():
            actions.append(UseDevelopmentCardAction(unique_card))
        for resource in Resource:
            if self.can_trade_2_to_1(resource, True):
                actions.extend(TradeAction.simple_trade_options(resource, 2))
            elif self.can_trade_3_to_1(resource):
                actions.extend(TradeAction.simple_trade_options(resource, 3))
            elif self.can_trade_4_to_1(resource):
                actions.extend(TradeAction.simple_trade_options(resource, 4))
        return actions
    
    # returns whether the player has ended their turn
    def perform_action(self, action: Action, board: Board, game: 'Game') -> Action:
        print_debug(f'Player {self.index + 1} performs action {action}')
        if isinstance(action, EndTurnAction):
            for card in self.unplayed_dev_cards:
                if card.card_type != DevelopmentCardType.VICTORY_POINT and card.on_cooldown:
                    card.on_cooldown = False
            return action
        elif isinstance(action, BuildSettlementAction):
            self.build_settlement(action.road_vertex, action.pay_for)
            self.setup_last_settlement = action.road_vertex
        elif isinstance(action, BuildCityAction):
            self.build_city(action.road_vertex, action.pay_for)
        elif isinstance(action, BuildRoadAction):
            self.build_road(action.road, game, action.pay_for)
            self.setup_last_settlement = None
        elif isinstance(action, BuyDevelopmentCardAction):
            self.buy_development_card(board)
        elif isinstance(action, UseDevelopmentCardAction):
            self.unplayed_dev_cards.remove(action.card)
            self.played_dev_cards.append(action.card)
            if action.card.card_type == DevelopmentCardType.KNIGHT:
                game.move_robber_and_steal(self.index)
                self.army_size += 1
            elif action.card.card_type == DevelopmentCardType.ROAD_BUILDING:
                self.free_roads_remaining += min(2, self.available_roads)
            elif action.card.card_type == DevelopmentCardType.YEAR_OF_PLENTY:
                for _ in range(2):
                    game.select_and_give_resource(self.index)
            elif action.card.card_type == DevelopmentCardType.MONOPOLY:
                game.select_and_steal_all_resources(self.index)
        elif isinstance(action, TradeAction):
            if not self.can_afford(action.giving):
                raise CatanException('Cannot afford trade')
            self.pay_for(action.giving)
            for resource in action.receiving:
                self.give_resource(resource)
        else:
            raise CatanException('Invalid action')
        return action

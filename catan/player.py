from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Union

from catan.board import Board, Resource, RoadVertex, Road
from catan.error import CatanException
from catan.constants import *


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

Action = Union[BuildSettlementAction, BuildCityAction, BuildRoadAction]


class Player:
    index: int
    color: tuple[int, int, int]
    resources: dict[Resource, int]
    dev_cards: list

    available_settlements: int
    settlements: list[RoadVertex]
    available_cities: int
    cities: list[RoadVertex]
    available_roads: int
    roads: list[Road]

    victory_points: int
    longest_road_size: int
    has_longest_road: bool
    army_size: int
    has_largest_army: bool

    def __init__(self, index: int, color: tuple[int, int, int]):
        self.index = index
        self.color = color
        self.resources = {resource: 0 for resource in Resource}
        self.dev_cards = []

        self.available_settlements = 5
        self.settlements = []
        self.available_cities = 4
        self.cities = []
        self.available_roads = 15
        self.roads = []

        self.victory_points = 0
        self.longest_road_size = 0
        self.has_longest_road = False
        self.army_size = 0
        self.has_largest_army = False
    
    def can_afford(self, cost: list[Resource]) -> bool:
        cost_dict = Counter(cost)
        return all(self.resources[resource] >= cost_dict[resource] for resource in cost_dict)
    
    def pay_for(self, cost: list[Resource]):
        cost_dict = Counter(cost)
        for resource in cost_dict:
            self.resources[resource] -= cost_dict[resource]
    
    def give_resource(self, resource: Resource, count: int = 1):
        self.resources[resource] += count
    
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
        self.victory_points += 1
        if pay_for:
            self.pay_for(SETTLEMENT_COST)
    
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
        self.victory_points += 1
        if pay_for:
            self.pay_for(CITY_COST)
    
    def build_road(self, road: Road, pay_for: bool = True):
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

    def find_longest_road_size(self) -> int:
        # TODO: implement well
        return 0
        # graph = defaultdict(list)
        # for road in self.roads:
        #     graph[road.rv1].append(road)
        #     graph[road.rv2].append(road)

        # max_length = 0
        # best_path = []

        # def dfs(vertex, visited_roads, current_length, current_path):
        #     nonlocal max_length, best_path
        #     if current_length > max_length:
        #         max_length = current_length
        #         best_path = current_path.copy()

        #     for road in graph.get(vertex, []):
        #         if road not in visited_roads:
        #             visited_roads.add(road)
        #             next_vertex = road.rv2 if road.rv1 == vertex else road.rv1
        #             current_path.append(road)
        #             dfs(next_vertex, visited_roads, current_length + 1, current_path)
        #             current_path.pop()
        #             visited_roads.remove(road)

        # for vertex in graph:
        #     dfs(vertex, set(), 0, [])

        # self.longest_road_size = max_length
        # self.longest_road_path = best_path
        # return max_length
    
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

    def is_valid_road_location(self, road: Road) -> bool:
        if road.owner is not None:
            return False
        for road_vertex in road.endpoints:
            if road_vertex.owner == self.index:
                return True
            for connected_road in road_vertex.adjacent_roads:
                if connected_road.owner == self.index:
                    return True
    
    def get_all_possible_actions(self, board: Board) -> list[tuple[str, tuple]]:
        if len(self.settlements) < 2 and len(self.roads) < 2:
            return self._get_all_possible_actions_placing(board)
        return self._get_all_possible_actions_normal(board)
    
    def _get_all_possible_actions_placing(self, board: Board) -> list[tuple[str, tuple]]:
        actions = []
        if len(self.settlements) <= len(self.roads):
            for road_vertex in board.road_vertices:
                if self.is_valid_settlement_location(road_vertex, needs_road=False):
                    actions.append(('build_settlement', (road_vertex, False)))
        else:
            for road in board.roads:
                if self.is_valid_road_location(road):
                    actions.append(('build_road', (road,)))
        return actions

    def _get_all_possible_actions_normal(self, board: Board) -> list[Action]:
        actions: list[Action] = []
        for road_vertex in board.road_vertices:
            if self.is_valid_settlement_location(road_vertex) and self.can_afford(SETTLEMENT_COST):
                actions.append(BuildSettlementAction(road_vertex))
            if self.is_valid_city_location(road_vertex) and self.can_afford(CITY_COST):
                actions.append(BuildCityAction(road_vertex))
        for road in board.roads:
            if self.is_valid_road_location(road) and self.can_afford(ROAD_COST):
                actions.append(BuildRoadAction(road))
        return actions
    
    def perform_action(self, action: Action):
        if isinstance(action, BuildSettlementAction):
            self.build_settlement(action.road_vertex, action.pay_for)
        elif isinstance(action, BuildCityAction):
            self.build_city(action.road_vertex, action.pay_for)
        elif isinstance(action, BuildRoadAction):
            self.build_road(action.road, action.pay_for)
        else:
            raise CatanException('Invalid action')

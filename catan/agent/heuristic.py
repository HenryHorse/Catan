from typing import TYPE_CHECKING
import random

from catan.board import Board, Resource, RoadVertex, Road
from catan.player import Player, Action, BuildSettlementAction, BuildCityAction, BuildRoadAction, \
    BuyDevelopmentCardAction, TradeAction, UseDevelopmentCardAction, EndTurnAction
from catan.util import CubeCoordinates
from catan.agent import Agent
from catan.game import GamePhase

if TYPE_CHECKING:
    from catan.game import Game



class HeuristicAgent(Agent):
    def __init__(self, board: Board, player: Player):
        super().__init__(board, player)

    def get_action(self, game: 'Game', possible_actions: list[Action]) -> Action:
        # The logic is straightforward: prioritize certain types of actions first, try others next. If it can't do anything, just end the turn
        # You can try swapping the order of the isinstance statements to see if one performs better than the other (i.e. prioritizing using dev cards early on)
        best_settlement_action = None
        best_settlement_score = -1
        for action in possible_actions:
            if isinstance(action, BuildSettlementAction):
                settlement_score = self.evaluate_settlement_location(action.road_vertex, game)
                if settlement_score > best_settlement_score:
                    best_settlement_action = action
                    best_settlement_score = settlement_score
        if best_settlement_action:
            return best_settlement_action

        for action in possible_actions:
            if isinstance(action, BuildCityAction):
                return action

        best_road_action = None
        best_road_score = -1
        for action in possible_actions:
            if isinstance(action, BuildRoadAction):
                road_score = self.evaluate_road_location(action.road, game)
                if road_score > best_road_score:
                    best_road_action = action
                    best_road_score = road_score
        if best_road_action:
            return best_road_action

        # TODO Think of a heuristic for this
        for action in possible_actions:
            if isinstance(action, UseDevelopmentCardAction):
                return action

        for action in possible_actions:
            if isinstance(action, BuyDevelopmentCardAction):
                return action


        # TODO Evaluate TradeAction by looking for most needed resource
        for action in possible_actions:
            if isinstance(action, TradeAction):
                return action

        return EndTurnAction()

    def evaluate_settlement_location(self, road_vertex: RoadVertex, game: 'Game') -> int:
        score = 0
        resource_types = set()
        dice_probability = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

        for tile in road_vertex.adjacent_tiles:
            if tile and tile.resource:
                score += dice_probability[tile.number]
                resource_types.add(tile.resource)

        # the more resource types there are adjacent to this road_vertex, the bigger the score
        score += len(resource_types)

        num_available_roads = 0
        for road in road_vertex.adjacent_roads:
            if road.owner is None:
                num_available_roads += 1
        score += num_available_roads

        return score

    def evaluate_city_location(self, road_vertex: RoadVertex, game: 'Game') -> int:
        score = 0
        resource_types = set()
        dice_probability = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

        for tile in road_vertex.adjacent_tiles:
            if tile and tile.resource:
                score += dice_probability[tile.number]
                resource_types.add(tile.resource)

        # the more resource types there are adjacent to this road_vertex, the bigger the score
        score += len(resource_types)

        return score

    def evaluate_road_location(self, road: Road, game: 'Game') -> int:
        score = 0
        current_player = game.player_agents[self.player.index].player

        for vertex in road.endpoints:
            if current_player.is_valid_settlement_location(vertex):
                score += self.evaluate_settlement_location(vertex, game)
        return score

    def get_most_needed_resource(self, game: 'Game') -> Resource:
        needed_resources = {
            BuildSettlementAction: [Resource.BRICK, Resource.WOOD, Resource.GRAIN, Resource.SHEEP],
            BuildCityAction: [Resource.ORE, Resource.ORE, Resource.ORE, Resource.GRAIN, Resource.GRAIN],
            BuildRoadAction: [Resource.BRICK, Resource.WOOD]
        }

        # Given the order of iteration, this will prioritize settlements, then cities, then roads if we have 0 of the resources for those 3
        for action, resources in needed_resources.items():
            possible_actions = self.player.get_all_possible_actions(game.board, game.game_phase == GamePhase.SETUP)
            if action in possible_actions:
                for resource in resources:
                    if self.player.resources[resource] == 0:
                        return resource

        # If we have at least 1 of every resource needed for settlements, cities, and roads, just pick the one we have the least of
        return min(self.player.resources, key=self.player.resources.get)

    def get_robber_placement(self, game: 'Game') -> CubeCoordinates:
        highest_value_tile = None
        highest_value = -1

        for tile in game.board.tiles.values():
            if tile.has_robber:
                continue

            num_dependents = 0
            for road_vertex in tile.adjacent_road_vertices:
                if road_vertex.owner is not None and road_vertex.owner != self.player.index:
                    num_dependents += 1

            if num_dependents > highest_value:
                highest_value_tile = tile
                highest_value = num_dependents

        if highest_value_tile is not None:
            return highest_value_tile.cube_coords
        else:
            return CubeCoordinates(0, 0, 0)

    def get_player_to_steal_from(self, game: 'Game', options: list[int]) -> int:
        # Choose the player with the larger amount of resources to steal from
        player_resource_count = {}
        for option in options:
            player_resource_count[option] = game.player_agents[option].player.get_resource_count()
        return max(player_resource_count, key=player_resource_count.get)

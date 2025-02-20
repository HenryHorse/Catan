import random
from dataclasses import dataclass

from catan.board import Board
from catan.player import Player
from catan.agent import Agent
from catan.util import CubeCoordinates


@dataclass
class PlayerAgent:
    player: Player
    agent: Agent

    def as_tuple(self) -> tuple[Player, Agent]:
        return (self.player, self.agent)


class Game:
    board: Board
    player_agents: list[PlayerAgent]
    player_turn_index: int
    winning_player_index: int | None
    total_turns_elapsed: int

    ''' keep track of the state of the game'''
    def __init__(self, board: Board, player_agents: list[PlayerAgent]):
        self.board = board
        self.board.initialize_tile_info()
        self.board.set_harbors()
        self.player_agents = player_agents
        self.player_turn_index = 0
        self.winning_player_index = None
        self.total_turns_elapsed = 0

    def perform_dice_roll(self):
        roll = random.randint(1, 6) + random.randint(1, 6)
        print(f"Rolled a {roll}")

        if roll == 7:
            # TODO: do that whole resources >= 8 thing
            new_robber_location = self.player_agents[self.player_turn_index].agent.get_robber_placement()
            self.move_robber(new_robber_location)
            return

        for tile in self.board.tiles.values():
            if tile.number == roll and not tile.has_robber:
                for road_vertex in tile.adjacent_road_vertices:
                    if road_vertex.has_settlement and road_vertex.owner is not None:
                        count = 2 if road_vertex.has_city else 1
                        self.players[road_vertex.owner].give_resource(tile.resource, count)

    def move_robber_and_steal(self, location: CubeCoordinates):
        print(f"{self.player_turn_index} moves robber to {location}")
        for tile in self.board.tiles.values():
            tile.has_robber = tile.cube_coords == location
            if tile.has_robber:
                for road_vertex in tile.adjacent_road_vertices:
                    if road_vertex.has_settlement and road_vertex.owner is not None:
                        count = 2 if road_vertex.has_city else 1
                        self.players[road_vertex.owner].give_resource(tile.resource, count)

    def perform_current_player_action(self):
        # tuple unpacking causes type issues :/
        player, agent = self.player_agents[self.player_turn_index].as_tuple()
        player.perform_action(agent.get_action(), self.board)
    
    def do_full_turn(self):
        if self.winning_player_index is not None:
            return
        self.perform_dice_roll()
        self.perform_current_player_action()
        self.total_turns_elapsed += 1
        for player_agent in self.player_agents:
            if player_agent.player.victory_points >= 10:
                self.winning_player_index = player_agent.player.index
                return
        self.player_turn_index = (self.player_turn_index + 1) % len(self.player_agents)

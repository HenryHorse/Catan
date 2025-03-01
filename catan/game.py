import random
from dataclasses import dataclass
from enum import Enum

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

class GamePhase(Enum):
    SETUP = 0
    MAIN = 1


class Game:
    board: Board
    player_agents: list[PlayerAgent]
    player_turn_index: int
    winning_player_index: int | None
    setup_turns_elapsed: int
    main_turns_elapsed: int
    game_phase: GamePhase
    setup_round_count: int

    ''' keep track of the state of the game'''
    def __init__(self, board: Board, player_agents: list[PlayerAgent]):
        self.board = board
        self.board.initialize_tile_info()
        self.board.set_harbors()
        self.player_agents = player_agents
        self.player_turn_index = 0
        self.winning_player_index = None
        self.setup_turns_elapsed = 0
        self.main_turns_elapsed = 0
        self.game_phase = GamePhase.SETUP
        self.setup_round_count = 2

    def perform_dice_roll(self):
        roll = random.randint(1, 6) + random.randint(1, 6)
        print(f"Rolled a {roll}")

        if roll == 7:
            # TODO: do that whole resources >= 8 thing
            new_robber_location = self.player_agents[self.player_turn_index].agent.get_robber_placement()
            self.move_robber_and_steal(new_robber_location)
            return

        for tile in self.board.tiles.values():
            if tile.number == roll and not tile.has_robber:
                for road_vertex in tile.adjacent_road_vertices:
                    if road_vertex.has_settlement and road_vertex.owner is not None:
                        count = 2 if road_vertex.has_city else 1
                        self.player_agents[road_vertex.owner].player.give_resource(tile.resource, count)

    def move_robber_and_steal(self, location: CubeCoordinates):
        print(f"{self.player_turn_index} moves robber to {location}")
        for tile in self.board.tiles.values():
            tile.has_robber = tile.cube_coords == location
            if tile.has_robber:
                # TODO: implement robbing
                pass
    
    def select_and_give_resource(self, player_index: int):
        player, agent = self.player_agents[player_index].as_tuple()
        resource = agent.get_most_needed_resource()
        player.give_resource(resource, 1)

    def select_and_steal_all_resources(self, player_index: int):
        player, agent = self.player_agents[player_index].as_tuple()
        resource = agent.get_most_needed_resource()
        count = 0
        for player_agent in self.player_agents:
            if player_agent.player.index != player_index:
                count += player_agent.player.resources[resource]
                player_agent.player.resources[resource] = 0
        player.give_resource(resource, count)

    # returns whether the player has ended their turn
    def get_and_perform_player_action(self):
        # tuple unpacking causes type issues :/
        player, agent = self.player_agents[self.player_turn_index].as_tuple()
        all_possible_actions = player.get_all_possible_actions(self.board, self.game_phase == GamePhase.SETUP)
        action = agent.get_action(all_possible_actions)
        return player.perform_action(action, self.board, self)
    
    def advance_player_turn(self):
        self.player_turn_index = (self.player_turn_index + 1) % len(self.player_agents)
    
    def do_full_turn(self):
        if self.winning_player_index is not None:
            return
        if self.game_phase == GamePhase.SETUP:
            if self.setup_turns_elapsed >= len(self.player_agents) * 2 * self.setup_round_count:
                self.game_phase = GamePhase.MAIN
                return
            self.get_and_perform_player_action()
            if self.setup_turns_elapsed % 2 == 1:
                self.advance_player_turn()
            self.setup_turns_elapsed += 1
        else:
            self.perform_dice_roll()
            # keep performing actions until the player ends their turn
            while not self.get_and_perform_player_action():
                pass
            self.main_turns_elapsed += 1
            for player_agent in self.player_agents:
                if player_agent.player.victory_points >= 10:
                    self.winning_player_index = player_agent.player.index
                    return
            self.advance_player_turn()

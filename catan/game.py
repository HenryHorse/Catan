import random
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from catan.agent.human import HumanAgent
from catan.board import Board
from catan.player import Player
from catan.agent import Agent

from globals import DEV_MODE


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
    longest_road_length: int
    largest_army_size: int
    human_dice_rolled: bool
    setup_turn_counter: int
    has_human: bool

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
        self.longest_road_length = 4
        self.largest_army_size = 2
        self.human_dice_rolled = False
        self.has_human = any(isinstance(pa.agent, HumanAgent) for pa in player_agents)
        self.setup_stage = 0
        self.setup_turn_counter = 0

    def perform_dice_roll(self):
        roll = random.randint(1, 6) + random.randint(1, 6)
        if DEV_MODE:
            print(f"Rolled a {roll}")

        if roll == 7:
            # TODO: do that whole resources >= 8 thing
            self.move_robber_and_steal(self.player_turn_index)
            return

        for tile in self.board.tiles.values():
            if tile.number == roll and not tile.has_robber:
                for road_vertex in tile.adjacent_road_vertices:
                    if road_vertex.has_settlement and road_vertex.owner is not None:
                        count = 2 if road_vertex.has_city else 1
                        self.player_agents[road_vertex.owner].player.give_resource(tile.resource, count)

    def move_robber_and_steal(self, player_index: int):
        player, agent = self.player_agents[player_index].as_tuple()
        location = agent.get_robber_placement(self)
        if DEV_MODE:
            print(f"Player {self.player_turn_index + 1} moves robber to {location}")
        for tile in self.board.tiles.values():
            tile.has_robber = tile.cube_coords == location
            if tile.has_robber:
                players_on_tile = [vertex.owner for vertex in tile.adjacent_road_vertices \
                                   if vertex.owner is not None and vertex.owner != player_index]
                if players_on_tile:
                    steal_from = agent.get_player_to_steal_from(self, players_on_tile)
                    target_player = self.player_agents[steal_from].player
                    if target_player.get_resource_count() == 0:
                        continue
                    resource = target_player.take_random_resources(1)[0]
                    player.give_resource(resource, 1)
                    if DEV_MODE:
                        print(f"Player {self.player_turn_index + 1} steals from Player {steal_from + 1}")
    
    def discard_half_resources_from_all(self):
        for player_agent in self.player_agents:
            player = player_agent.player
            if player.get_resource_count() > 7:
                discard_count = player.resource_count() // 2
                _ = player.take_random_resources(discard_count)
                if DEV_MODE:
                    print(f"Player {player.index + 1} discards {discard_count} resources")
    
    def select_and_give_resource(self, player_index: int):
        player, agent = self.player_agents[player_index].as_tuple()
        resource = agent.get_most_needed_resource(self)
        player.give_resource(resource, 1)

    def select_and_steal_all_resources(self, player_index: int):
        player, agent = self.player_agents[player_index].as_tuple()
        resource = agent.get_most_needed_resource(self)
        count = 0
        for player_agent in self.player_agents:
            if player_agent.player.index != player_index:
                count += player_agent.player.resources[resource]
                player_agent.player.resources[resource] = 0
        player.give_resource(resource, count)
    
    def award_from_highest_score(
            self,
            score_func: Callable[[Player], int],
            award_func: Callable[[Player, bool], None],
            min_score: int,
    ):
        scores = [score_func(player_agent.player) for player_agent in self.player_agents]
        highest_score = max(scores)
        players_with_highest_score = [i for i, score in enumerate(scores) if score == highest_score and score >= min_score]

        # If nobody meets the requirements for the card, nobody gets it.
        if not players_with_highest_score:
            for player_agent in self.player_agents:
                award_func(player_agent.player, False)

        # If there is only one player with the highest score, they get the card.
        # Ties would theoretically be broken by previous assertions
        if len(players_with_highest_score) == 1:
            winning_index = players_with_highest_score[0]
            for i, player_agent in enumerate(self.player_agents):
                award_func(player_agent.player, i == winning_index)
    
    def recompute_longest_road(self):
        def set_award(player: Player, award: bool):
            player.has_longest_road = award
        self.award_from_highest_score(
            lambda player: player.find_longest_road_size(),
            set_award,
            5
        )
    
    def recompute_largest_army(self):
        def set_award(player: Player, award: bool):
            player.has_largest_army = award
        self.award_from_highest_score(
            lambda player: player.army_size,
            set_award,
            3
        )

    # returns whether the player has ended their turn
    def get_and_perform_player_action(self, player_index: int = None):
        # Use the provided index if given, else use the stored player_turn_index.
        if player_index is None:
            player_index = self.player_turn_index
        # tuple unpacking moment
        player, agent = self.player_agents[player_index].as_tuple()
        all_possible_actions = player.get_all_possible_actions(self.board, self.game_phase == GamePhase.SETUP)
        if not all_possible_actions:
            return
        elif len(all_possible_actions) == 1:
            return player.perform_action(all_possible_actions[0], self.board, self)
        else:
            action = agent.get_action(self, all_possible_actions)
            return player.perform_action(action, self.board, self)
    
    def advance_player_turn(self):
        self.player_turn_index = (self.player_turn_index + 1) % len(self.player_agents)
    
    def do_full_turn(self):
        if self.winning_player_index is not None:
            return

        if self.game_phase == GamePhase.SETUP:
            if self.has_human:
                # Determine the explicit order.
                # Assumes one human at index 0 and bots at the remaining indices.
                human_index = next(i for i, pa in enumerate(self.player_agents)
                                    if isinstance(pa.agent, HumanAgent))
                bot_indices = [i for i, pa in enumerate(self.player_agents)
                            if not isinstance(pa.agent, HumanAgent)]
                # Desired overall order:
                total_order = [human_index] + bot_indices + bot_indices[::-1] + [human_index]
                if not hasattr(self, "setup_turn_counter"):
                    self.setup_turn_counter = 0
                if self.setup_turn_counter < len(total_order):
                    current_player_index = total_order[self.setup_turn_counter]
                    if current_player_index == human_index:
                        if DEV_MODE:
                            print("Human setup turn: waiting for human input.")
                        return
                    else:
                        if DEV_MODE:
                            print(f"Bot {current_player_index + 1} auto-turn: placing settlement and road.")
                        self.get_and_perform_player_action(current_player_index)  # settlement
                        self.get_and_perform_player_action(current_player_index)  # road
                        self.setup_turn_counter += 1
                        if self.setup_turn_counter < len(total_order):
                            self.player_turn_index = total_order[self.setup_turn_counter]
                        return
                else:
                    if DEV_MODE:
                        print("Setup complete; entering main phase.")
                    self.game_phase = GamePhase.MAIN
                    self.player_turn_index = human_index
                    return
            else:
                n = len(self.player_agents)
                actions_per_player = 2  # settlement then road
                total_actions_in_round = n * actions_per_player
                total_setup_turns = total_actions_in_round * self.setup_round_count

                if self.setup_turns_elapsed >= total_setup_turns:
                    self.game_phase = GamePhase.MAIN
                    for pa in self.player_agents:
                        pa.player.pending_settlement_for_road = None
                    self.player_turn_index = 0
                    return

                current_round = self.setup_turns_elapsed // total_actions_in_round
                remainder = self.setup_turns_elapsed % total_actions_in_round
                player_index_in_round = remainder // actions_per_player
                action_index = remainder % actions_per_player  # 0 for settlement, 1 for road

                if current_round % 2 == 0:
                    current_player_index = player_index_in_round
                else:
                    current_player_index = n - 1 - player_index_in_round

                if action_index == 0:
                    if DEV_MODE:
                        print(f"Round {current_round+1} - Player {current_player_index + 1} places a settlement.")
                else:
                    if DEV_MODE:
                        print(f"Round {current_round+1} - Player {current_player_index + 1} places a road.")
                self.get_and_perform_player_action(current_player_index)
                self.setup_turns_elapsed += 1

        else:
            # MAIN phase: roll dice, process actions until turn ends, etc.
            self.perform_dice_roll()
            while not self.get_and_perform_player_action():
                pass
            self.main_turns_elapsed += 1
            self.recompute_longest_road()
            self.recompute_largest_army()
            for player_agent in self.player_agents:
                if player_agent.player.get_victory_points() >= 10:
                    self.winning_player_index = player_agent.player.index
                    return
            self.advance_player_turn()

    def human_dice_roll(self):
        self.perform_dice_roll()

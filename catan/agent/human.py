from typing import TYPE_CHECKING
import random

from catan.board import Board, Resource
from catan.player import Player, Action
from catan.util import CubeCoordinates
from catan.agent import Agent
if TYPE_CHECKING:
    from catan.game import Game

class HumanAgent(Agent):
    def __init__(self, board: Board, player: Player):
        super().__init__(board, player)

    def get_action(self, game: 'Game', possible_actions: list[Action]) -> Action:
        return random.choice(possible_actions)

    def get_most_needed_resource(self, game: 'Game') -> Resource:
        return random.choice(list(Resource))
    
    def get_robber_placement(self, game: 'Game') -> CubeCoordinates:
        return CubeCoordinates(0, 0, 0)
    
    def get_player_to_steal_from(self, game: 'Game', options: list[int]) -> int:
        return random.choice(options)

import random

from catan.board import Board, Resource
from catan.player import Player, Action
from catan.util import CubeCoordinates
from catan.agent import Agent

class RandomAgent(Agent):
    def __init__(self, board: Board, player: Player):
        super().__init__(board, player)

    def get_action(self, possible_actions: list[Action]) -> Action:
        return random.choice(possible_actions)

    def get_most_needed_resource(self) -> Resource:
        return random.choice(list(Resource))
    
    def get_robber_placement(self):
        return CubeCoordinates(0, 0, 0)

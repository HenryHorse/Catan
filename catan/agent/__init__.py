from catan.board import Board, Resource
from catan.player import Player
from catan.util import CubeCoordinates

class Agent:
    board: Board
    player: Player

    def __init__(self, board: Board, player: Player):
        self.board = board
        self.player = player

    # returns index of chosen action out of all possible player actions
    def get_action(self) -> int:
        raise NotImplementedError

    def get_most_needed_resources(self) -> tuple[Resource, Resource]:
        raise NotImplementedError
    
    def get_robber_placement(self) -> CubeCoordinates:
        raise NotImplementedError

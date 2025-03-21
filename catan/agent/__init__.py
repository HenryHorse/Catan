from typing import TYPE_CHECKING

from catan.board import Board, Resource
from catan.player import Player, Action
from catan.util import CubeCoordinates
if TYPE_CHECKING:
    from catan.game import Game

class Agent:
    board: Board
    player: Player

    def __init__(self, board: Board, player: Player):
        self.board = board
        self.player = player

    # returns index of chosen action out of all possible player actions
    def get_action(self, game: 'Game', possible_actions: list[Action]) -> Action:
        raise NotImplementedError

    def get_most_needed_resource(self, game: 'Game') -> Resource:
        raise NotImplementedError
    
    def get_robber_placement(self, game: 'Game') -> CubeCoordinates:
        raise NotImplementedError

    def get_player_to_steal_from(self, game: 'Game', options: list[int]) -> int:
        raise NotImplementedError

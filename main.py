import argparse

from catan.board import Board
from catan.player import Player
from catan.agent.random import RandomAgent
from catan.agent.human import HumanAgent
from catan.agent.heuristic import HeuristicAgent
from catan.game import Game, PlayerAgent
from catan.ui import CatanUI


def parse_arguments():
    parser = argparse.ArgumentParser(description="Settlers of Catan board visualizer")
    parser.add_argument("--board-size", type=int, default=3, help="Size of the board (default: 3)")
    # TODO: make this do something?
    parser.add_argument("--num-players", type=int, default=4, help="Number of players (default: 4)")
    return parser.parse_args()

def create_game() -> Game:
    board = Board(3)

    player_1 = Player(0, (255, 0, 0))
    agent_1 = HumanAgent(board, player_1)
    # agent_1 = HeuristicAgent(board, player_1)
    # agent_1 = RandomAgent(board, player_1)
    player_2 = Player(1, (0, 0, 255))
    agent_2 = HeuristicAgent(board, player_2)
    player_3 = Player(2, (255, 255, 255))
    agent_3 = HeuristicAgent(board, player_3)
    player_4 = Player(3, (255, 102, 0))
    agent_4 = HeuristicAgent(board, player_4)

    return Game(board, [
        PlayerAgent(player_1, agent_1),
        PlayerAgent(player_2, agent_2),
        PlayerAgent(player_3, agent_3),
        PlayerAgent(player_4, agent_4)])

def main():
    catan_ui = CatanUI(create_game)
    catan_ui.open_and_loop()

if __name__ == '__main__':
    main()

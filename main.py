import argparse

from catan.board import Board
from catan.player import Player
from catan.agent.random import RandomAgent
from catan.agent.rl_agent import RL_Agent

from catan.game import Game, PlayerAgent
from catan.ui import CatanUI
from catan.serialization import BrickRepresentation


def parse_arguments():
    parser = argparse.ArgumentParser(description="Settlers of Catan board visualizer")
    parser.add_argument("--board-size", type=int, default=3, help="Size of the board (default: 3)")
    # TODO: make this do something?
    parser.add_argument("--num-players", type=int, default=4, help="Number of players (default: 4)")
    return parser.parse_args()

def create_game(serialization) -> Game:
    board = Board(3)

    player_1 = Player(0, (255, 0, 0))
    agent_1 = RandomAgent(board, player_1, 1)
    player_2 = Player(1, (0, 0, 255))
    agent_2 = RandomAgent(board, player_2, 2)
    player_3 = Player(2, (255, 255, 255))
    agent_3 = RandomAgent(board, player_3, 3)
    player_4 = Player(3, (255, 102, 0)) 
    agent_4 = RL_Agent(board, player_4, 4)



    return Game(board, [
        PlayerAgent(player_1, agent_1),
        PlayerAgent(player_2, agent_2),
        PlayerAgent(player_3, agent_3),
        PlayerAgent(player_4, agent_4)])

def main():
   serialization = BrickRepresentation(5, 4, None, 1)  
   game = create_game(serialization)  
   serialization.game = game
   serialization.recursive_serialize(game, game.board.center_tile, None, None, False, [])
   #serialization.recursive_serialize(game, game.board.center_tile)  
   print(serialization.board[-1])  

   catan_ui = CatanUI(lambda: game, serialization=serialization) # Pass serialization into catan_ui for testing
   catan_ui.open_and_loop()

if __name__ == '__main__':
    main()

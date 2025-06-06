import argparse
import os
import torch

from catan.QNN import GNNQNetwork
from globals import SELECTED_GRAPH_MODEL, SELECTED_GRID_MODEL

from catan.board import Board
from catan.player import Player
from catan.agent.random import RandomAgent
from catan.agent.rl_agent import RL_Agent, RL_Model, QNetwork, load_or_create_grid_model
from catan.agent.gnn_rl_agent import GNNRLAgent, GNNRLModel

from catan.agent.human import HumanAgent
from catan.agent.heuristic import HeuristicAgent
from catan.game import Game, PlayerAgent
from catan.ui import CatanUI
from catan.serialization import BrickRepresentation

def parse_arguments():
    parser = argparse.ArgumentParser(description="Settlers of Catan board visualizer")
    parser.add_argument("--board-size", type=int, default=3, help="Size of the board (default: 3)")
    parser.add_argument("--num-players", type=int, default=4, help="Number of players (default: 4)")
    parser.add_argument("--players", type=str, default="RHNG", help="Player types, Human = U, Random = R, Heuristic = H, RL_Agent = N, GNNRLAgent = G")
    parser.add_argument("--sim", action="store_true", help="Enable simulation statistics")
    parser.add_argument("--train", action="store_true", help="Enable training")
    return parser.parse_args()


def create_game(players) -> Game:

    if len(players) != 4:
        print("Invalid number of given players")
        exit()

    board = Board(3)
    
    player_list = []
    agents = []

    player_list.append(Player(0, (255, 0, 0)))
    player_list.append(Player(1, (0, 0, 255)))
    player_list.append(Player(2, (255, 255, 255)))
    player_list.append(Player(3, (255, 102, 0)))

    for i, player in enumerate(players):
        if player == "U":
            if agents == None:
                print("Only player 1 can be human")
                exit()
            agents.append(HumanAgent(board, player_list[i]))
        elif player == "R":
            print("Random agent")
            agents.append(RandomAgent(board, player_list[i]))
        elif player == "H":
            agents.append(HeuristicAgent(board, player_list[i]))
        elif player == "N":
            agents.append(RL_Agent(board, player_list[i]))
        elif player == "G":
            agents.append(GNNRLAgent(board, player_list[i], model_path=SELECTED_GRAPH_MODEL))
        else:
            print("Invalid player type")
            exit()

    new_game = Game(board, [
        PlayerAgent(player_list[0], agents[0]),
        PlayerAgent(player_list[1], agents[1]),
        PlayerAgent(player_list[2], agents[2]),
        PlayerAgent(player_list[3], agents[3])
    ])

    return new_game




def main():
    args = parse_arguments()

    game = create_game(args.players)
    # Hard coded to 4 players since no argument functionality at this moment
    serialization = BrickRepresentation(5, 4, None, 1)
    serialization.game = game
    game.serialization = serialization

    # Pass RL Agent to the UI
    catan_ui = CatanUI(lambda: game)
    catan_ui.open_and_loop(doSimulate=args.sim, train=args.train)


if __name__ == '__main__':
    main()

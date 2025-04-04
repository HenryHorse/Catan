import argparse
import os
import torch

from globals import SELECTED_MODEL

from catan.board import Board
from catan.player import Player
from catan.agent.random import RandomAgent
from catan.agent.rl_agent import RL_Agent, RL_Model, QNetwork

from catan.agent.human import HumanAgent
from catan.agent.heuristic import HeuristicAgent
from catan.game import Game, PlayerAgent
from catan.ui import CatanUI
from catan.serialization import BrickRepresentation

def parse_arguments():
    parser = argparse.ArgumentParser(description="Settlers of Catan board visualizer")
    # TODO: Implement these
    parser.add_argument("--board-size", type=int, default=3, help="Size of the board (default: 3)")
    parser.add_argument("--num-players", type=int, default=4, help="Number of players (default: 4)")
    parser.add_argument("--simulate", type=int, default=0, help="Find simulation statistics, 0 or 1 (default: 0)")
    parser.add_argument("--train", type=int, default=0, help="Perform training, 0 or 1 (default: 0)" )
    return parser.parse_args()

def create_game() -> Game:
    board = Board(3)

    # SAMPLES OF ALL AGENT TYPES
    # agent_1 = RandomAgent(board, player_1)
    # agent_1 = HeuristicAgent(board, player_1)
    # agent_1 = RL_Agent(board, player_1)
    # agent_1 = HumanAgent(board, player_1)

    player_1 = Player(0, (255, 0, 0))
    agent_1 = RL_Agent(board, player_1)
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


def load_or_create_model(model_path, board_channels, player_state_dim, action_dim):
    """Load a saved model if it exists, otherwise create a new one."""
    if os.path.exists(model_path):
        print(f"Loading model from {model_path}")
        model = QNetwork(board_channels, player_state_dim, action_dim)
        model.load_state_dict(torch.load(model_path))
        model.eval()  # Set the model to evaluation mode
    else:
        print(f"No model found at {model_path}. Creating a new model.")
        model = QNetwork(board_channels, player_state_dim, action_dim)
    return model



def main():
    args = parse_arguments()
    game = create_game()
    # Hard coded to 4 players since no argument functionality at this moment
    serialization = BrickRepresentation(5, 4, None, 1)
    serialization.game = game

    # Initialize RL Agent
    board_channels = args.num_players + 1  # Number of players + 1 for board state
    player_state_dim = 1224  # Size of the flattened player_state
    action_dim = 7  # Number of possible actions

    # Load or create the model
    model = load_or_create_model(SELECTED_MODEL, board_channels, player_state_dim, action_dim)
    rl_agent = RL_Model(model)

    # Pass RL Agent to the UI
    catan_ui = CatanUI(lambda: game, serialization=serialization, rl_agent=rl_agent, model_path=SELECTED_MODEL)
    catan_ui.open_and_loop(doSimulate=args.simulate, train=args.train)


if __name__ == '__main__':
    main()

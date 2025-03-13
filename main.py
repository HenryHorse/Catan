import argparse
import os
import torch


from catan.board import Board
from catan.player import Player
from catan.agent.random import RandomAgent
from catan.agent.rl_agent import RL_Agent, RLAgent, QNetwork

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
    serialization = BrickRepresentation(args.board_size, args.num_players, None, 1)  
    game = create_game(serialization)  
    serialization.game = game

    # Initialize RL Agent
    board_channels = args.num_players + 1  # Number of players + 1 for board state
    player_state_dim = 13 * args.num_players + 5  # Player states + dev cards
    action_dim = 7  # Number of possible actions

    # Load or create the model
    model = load_or_create_model(args.model_path, board_channels, player_state_dim, action_dim)
    rl_agent = RLAgent(model)

    # Pass RL Agent to the UI
    catan_ui = CatanUI(lambda: game, serialization=serialization, rl_agent=rl_agent, model_path=args.model_path)
    catan_ui.open_and_loop()


if __name__ == '__main__':
    main()

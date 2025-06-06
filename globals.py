DEV_MODE = True
NUM_GAMES = 300
SELECTED_GRID_MODEL = "rl_Model_V3"
SELECTED_GRAPH_MODEL = "GNN_RL_model"
# Define the dimensions for the Q-Network
BOARD_CHANNELS = 4 + 1  # Number of players + 1 for board state
PLAYER_STATE_DIM = 1001  # Player states + dev cards
ACTION_DIM = 246  # Number of possible actions
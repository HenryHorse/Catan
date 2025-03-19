import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
from collections import deque


class QNetwork(nn.Module):
    def __init__(self, board_channels, player_state_dim, action_dim, hidden_dim=128):
        super(QNetwork, self).__init__()
        
        # Convolutional layers for board state
        self.conv1 = nn.Conv2d(board_channels, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        
        # Fully connected layers for player state
        self.fc1 = nn.Linear(player_state_dim, hidden_dim)  # Input size: player_state_dim
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Final layer to output Q-values for each action
        self.fc_action = nn.Linear(29696, action_dim)
    
    def forward(self, x_board, x_player):
        # Debugging: Print shapes
        print(f"x_board shape: {x_board.shape}")
        print(f"x_player shape: {x_player.shape}")

        # Process board state
        x_board = torch.relu(self.conv1(x_board))
        x_board = torch.relu(self.conv2(x_board))
        x_board = torch.relu(self.conv3(x_board))
        x_board = x_board.view(x_board.size(0), -1)  # Flatten
        
        # Process player state
        x_player = x_player.view(x_player.size(0), -1)  # Flatten player_state
        x_player = torch.relu(self.fc1(x_player))
        x_player = torch.relu(self.fc2(x_player))
        
        # Concatenate and output Q-values
        x = torch.cat((x_board, x_player), dim=1)
        q_values = self.fc_action(x)
        return q_values
    

def select_action(model, state, possible_actions, epsilon=0.1):
    if random.random() < epsilon:
        print("random action selected on epsilon of: ",  epsilon)
        return random.choice(possible_actions)  # Exploration
    
    # Separate the image and structured parts of the state
    x_image, x_structured = state
    x_image = torch.tensor(x_image, dtype=torch.float32).unsqueeze(0)  # Add batch dimension
    x_structured = torch.tensor(x_structured, dtype=torch.float32).unsqueeze(0)
    
    # Get logits from the model
    logits = model(x_image, x_structured).detach().numpy().flatten()
    
    # Select the index of the action with the highest logit (action with the highest score)
    action_idx = np.argmax(logits)
    
    # Return the corresponding action (index)
    return possible_actions[action_idx]

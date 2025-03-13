import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
from collections import deque




def serialize_to_tensor(serialized_board: list[list[list[int]]]) -> torch.Tensor:
    #Converts a serialized board representation into a PyTorch tensor.
    matrices = [np.array(channel) for channel in serialized_board]
    tensor_board = torch.stack([torch.tensor(matrix, dtype=torch.float32) for matrix in matrices])
    return tensor_board

def deserialize_from_tensor(tensor_board: torch.Tensor) -> list[list[list[int]]]:
    #Converts a PyTorch tensor back into a list-based board representation.
    return tensor_board.numpy().tolist()


class QNetwork(nn.Module):
    def __init__(self, board_channels, player_state_dim, action_dim, hidden_dim=128):
        super(QNetwork, self).__init__()
        
        # Convolutional layers for board state
        self.conv1 = nn.Conv2d(board_channels, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        
        # Fully connected layers for player state
        self.fc1 = nn.Linear(player_state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Final layer to output Q-values for each action
        self.fc_action = nn.Linear(128 + hidden_dim, action_dim)
    
    def forward(self, x_board, x_player):
        # Process board state
        x_board = torch.relu(self.conv1(x_board))
        x_board = torch.relu(self.conv2(x_board))
        x_board = torch.relu(self.conv3(x_board))
        x_board = x_board.view(x_board.size(0), -1)  # Flatten
        
        # Process player state
        x_player = torch.relu(self.fc1(x_player))
        x_player = torch.relu(self.fc2(x_player))
        
        # Concatenate and output Q-values
        x = torch.cat((x_board, x_player), dim=1)
        q_values = self.fc_action(x)
        return q_values
    

def select_action(model, state, possible_actions, epsilon=0.1):
    if random.random() < epsilon:
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

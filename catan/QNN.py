import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random

import torch_geometric.nn as gnn
from torch_geometric.data import HeteroData


from globals import DEV_MODE


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
        self.fc_action = nn.Linear(29568 + hidden_dim, action_dim)
    
    def forward(self, x_board, x_player):
        # Debugging: Print shapes
        if DEV_MODE:
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

class GNNQNetwork(nn.Module):
    def __init__(self, player_state_dim: int, action_dim: int, hidden_dim: int = 128, out_graph_dim: int = 256):
        super(GNNQNetwork, self).__init__()
        
        self.node_encoders = nn.ModuleDict({
            'tile': nn.linear(8, hidden_dim),
            'vertex': nn.Linear(13, hidden_dim),
            'road': nn.Linear(4, hidden_dim),
        })

        self.hetero_conv1 = gnn.HeteroConv({
            ('road_vertex', 'road_vertex_to_tile', 'tile'): gnn.GATConv(hidden_dim, hidden_dim),
            ('tile', 'tile_to_road_vertex', 'road_vertex'): gnn.GATConv(hidden_dim, hidden_dim),
            ('road', 'road_to_road_vertex', 'road_vertex'): gnn.GATConv(hidden_dim, hidden_dim),
            ('road_vertex', 'road_vertex_to_road', 'road'): gnn.GATConv(hidden_dim, hidden_dim),
            ('tile', 'tile_to_road', 'road'): gnn.GATConv(hidden_dim, hidden_dim),
            ('road', 'road_to_tile', 'tile'): gnn.GATConv(hidden_dim, hidden_dim),
        }, aggr='sum')

        # Fully connected layers for player state
        self.fc1 = nn.Linear(player_state_dim, hidden_dim)  # Input size: player_state_dim
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Final layer to output Q-values for each action
        self.fc_action = nn.Linear(29568 + hidden_dim, action_dim)
    
    def forward(self, data: HeteroData, x_player):
        # Encode initial features for each node type
        x_dict = {
            node_type: self.node_encoders[node_type](data[node_type].x)
            for node_type in data.node_types
        }

        # Apply heterogeneous graph convolution
        x_dict = self.hetero_conv(x_dict, data.edge_index_dict)

        # Pool all node representations (i am not typing allat)
        x_all = torch.cat([
            gnn.global_mean_pool(x_dict[node_type], batch=data[node_type].batch)
            for node_type in x_dict
        ], dim=1)

        # Process player state
        x_player = x_player.view(x_player.size(0), -1)  # Flatten player_state
        x_player = torch.relu(self.fc1(x_player))
        x_player = torch.relu(self.fc2(x_player))

        # Concatenate and produce Q-values
        x = torch.cat([x_all, x_player], dim=1)
        return self.output_layer(x)

def select_action(model, state, possible_actions, epsilon=0.1):
    if random.random() < epsilon:
        if DEV_MODE:
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

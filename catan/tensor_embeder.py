import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
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
    def __init__(self, state_dim, action_dim, n_players, hidden_dim=128):
        super(QNetwork, self).__init__()
        
        # Convolutional layers for image-like data (e.g., board and player pieces)
        self.conv1 = nn.Conv2d(2*n_players + 3, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        
        # Fully connected layers for other structured data (e.g., possible actions, cards)
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        
        # Final layer to output logits for each action (not Q-values)
        self.fc_action = nn.Linear(128 + hidden_dim, action_dim)
    
    def forward(self, x_image, x_structured):
        # Process image-like data (e.g., board and player pieces)
        x_image = torch.relu(self.conv1(x_image))
        x_image = torch.relu(self.conv2(x_image))
        x_image = torch.relu(self.conv3(x_image))
        x_image = x_image.view(x_image.size(0), -1)  # Flatten the output of convolutional layers
        
        # Process structured data (e.g., possible actions, cards)
        x_structured = torch.relu(self.fc1(x_structured))
        x_structured = torch.relu(self.fc2(x_structured))
        
        # Concatenate both image and structured outputs
        x = torch.cat((x_image, x_structured), dim=1)
        
        # Final output layer to predict logits (raw scores) for each action
        logits = self.fc_action(x)
        return logits
    

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



# class BoardNN(nn.Module):
#     def __init__(self, input_channels: int, output_size: int):
#         super(BoardNN, self).__init__()
#         self.conv1 = nn.Conv2d(input_channels, 16, kernel_size=3, padding=1)
#         self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
#         self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
#         self.dropout1 = nn.Dropout(0.25)
#         self.conv4 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
#         self.dropout2 = nn.Dropout(0.25) #drop out for reduction in overfitting
#         self.fc1 = nn.Linear(128 * 8 * 8, 256)  # 8x8 board size?
#         self.dropout3 = nn.Dropout(0.5) #drop out for reduction in overfitting
#         self.fc2 = nn.Linear(256, 128)
#         self.fc3 = nn.Linear(128, output_size)
    
#     def forward(self, x):
#         x = F.relu(self.conv1(x))
#         x = F.relu(self.conv2(x))
#         x = F.relu(self.conv3(x))
#         x = self.dropout1(x)
#         x = F.relu(self.conv4(x))
#         x = self.dropout2(x)
#         x = torch.flatten(x, start_dim=1)
#         x = F.relu(self.fc1(x))
#         x = self.dropout3(x)
#         x = F.relu(self.fc2(x))
#         x = self.fc3(x)
#         return x
    
# #need to encode actions and need a reward function too but this is the belman eq framwork i think?

# def train_rl(agent, target_net, optimizer, memory, gamma=0.99, batch_size=32):
#     if len(memory) < batch_size:
#         return
    
#     batch = random.sample(memory, batch_size)
#     states, actions, rewards, next_states, done = zip(*batch)
    
#     #tensor handling
#     states = torch.cat(states)
#     actions = torch.tensor(actions, dtype=torch.long)
#     rewards = torch.tensor(rewards, dtype=torch.float32)
#     next_states = torch.cat(next_states)
#     done = torch.tensor(done, dtype=torch.float32)
    
#     #belman eq
#     q_values = agent(states).gather(1, actions.unsqueeze(1)).squeeze(1)
#     next_q_values = target_net(next_states).max(1)[0].detach()
#     target_q_values = rewards + (gamma * next_q_values * (1 - done))
    
#     #loss and backprop
#     loss = F.mse_loss(q_values, target_q_values)
#     optimizer.zero_grad()
#     loss.backward()
#     optimizer.step()

# # Memory replay buffer
# memory = deque(maxlen=10000)
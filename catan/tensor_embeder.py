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



class BoardNN(nn.Module):
    def __init__(self, input_channels: int, output_size: int):
        super(BoardNN, self).__init__()
        self.conv1 = nn.Conv2d(input_channels, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.dropout1 = nn.Dropout(0.25)
        self.conv4 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.dropout2 = nn.Dropout(0.25) #drop out for reduction in overfitting
        self.fc1 = nn.Linear(128 * 8 * 8, 256)  # 8x8 board size?
        self.dropout3 = nn.Dropout(0.5) #drop out for reduction in overfitting
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, output_size)
    
    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = self.dropout1(x)
        x = F.relu(self.conv4(x))
        x = self.dropout2(x)
        x = torch.flatten(x, start_dim=1)
        x = F.relu(self.fc1(x))
        x = self.dropout3(x)
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    
#need to encode actions and need a reward function too but this is the belman eq framwork i think?

def train_rl(agent, target_net, optimizer, memory, gamma=0.99, batch_size=32):
    if len(memory) < batch_size:
        return
    
    batch = random.sample(memory, batch_size)
    states, actions, rewards, next_states, done = zip(*batch)
    
    #tensor handling
    states = torch.cat(states)
    actions = torch.tensor(actions, dtype=torch.long)
    rewards = torch.tensor(rewards, dtype=torch.float32)
    next_states = torch.cat(next_states)
    done = torch.tensor(done, dtype=torch.float32)
    
    #belman eq
    q_values = agent(states).gather(1, actions.unsqueeze(1)).squeeze(1)
    next_q_values = target_net(next_states).max(1)[0].detach()
    target_q_values = rewards + (gamma * next_q_values * (1 - done))
    
    #loss and backprop
    loss = F.mse_loss(q_values, target_q_values)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

# Memory replay buffer
memory = deque(maxlen=10000)
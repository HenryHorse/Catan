from typing import TYPE_CHECKING

import random
import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque
from catan.tensor_embeder import QNetwork


from catan.board import Board, Resource
from catan.player import Player, Action
from catan.util import CubeCoordinates
from catan.agent import Agent
if TYPE_CHECKING:
    from catan.game import Game

class RLAgent(Agent):
    def __init__(self, board: Board, player: Player):
        super().__init__(board, player)

    def get_action(self, game: 'Game', possible_actions: list[Action]) -> Action:
        return random.choice(possible_actions)

    def get_most_needed_resource(self, game: 'Game') -> Resource:
        return random.choice(list(Resource))
    
    def get_robber_placement(self, game: 'Game') -> CubeCoordinates:
        return CubeCoordinates(0, 0, 0)
    
    def get_player_to_steal_from(self, game: 'Game', options: list[int]) -> int:
        return random.choice(options)



class RLAgent:
    def __init__(self, model: QNetwork, gamma=0.99, epsilon=1.0, epsilon_decay=0.995, batch_size=32, learning_rate=0.001):
        self.model = model
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.replay_buffer = []  # Store (state, action, reward, next_state, done)

    def get_action(self, game: 'Game', possible_actions: list[Action]) -> Action:
        """Select an action using epsilon-greedy strategy"""
        if random.random() < self.epsilon:
            return random.choice(possible_actions)  # Explore (random action)
        else:
            state = self.get_state(game)
            q_values = self.model(state)
            return possible_actions[q_values.argmax().item()]  # Exploit (best action based on Q-values)

    def store_experience(self, state, action, reward, next_state, done):
        """Store the agent's experience in the replay buffer"""
        self.replay_buffer.append((state, action, reward, next_state, done))
        # If the buffer exceeds a certain size, remove old experiences
        if len(self.replay_buffer) > 10000:
            self.replay_buffer.pop(0)

    def train(self):
        """Train the agent based on experiences collected during the game"""
        if len(self.replay_buffer) < self.batch_size:
            return  # Not enough experiences to train

        # Sample a random batch from the replay buffer
        batch = random.sample(self.replay_buffer, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        # Convert to tensors
        states_tensor = torch.tensor(states, dtype=torch.float32)
        actions_tensor = torch.tensor(actions, dtype=torch.long)
        rewards_tensor = torch.tensor(rewards, dtype=torch.float32)
        next_states_tensor = torch.tensor(next_states, dtype=torch.float32)
        dones_tensor = torch.tensor(dones, dtype=torch.float32)

        # Compute Q-values from the current state
        q_values = self.model(states_tensor)
        current_q_values = q_values.gather(1, actions_tensor.unsqueeze(1)).squeeze(1)

        # Compute the target Q-values using the Bellman equation
        with torch.no_grad():
            next_q_values = self.model(next_states_tensor)
            max_next_q_values = next_q_values.max(1)[0]
            target_q_values = rewards_tensor + self.gamma * max_next_q_values * (1 - dones_tensor)

        # Compute the loss (mean squared error)
        loss = torch.nn.functional.mse_loss(current_q_values, target_q_values)

        # Backpropagation and update the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update epsilon (decay exploration rate)
        self.epsilon = max(self.epsilon * self.epsilon_decay, 0.01)

    def get_state(self, game: 'Game'):
        """Generate a state representation from the game"""
        # Implement how you extract the state from the game object
        return game.get_state()
    


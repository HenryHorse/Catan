from typing import TYPE_CHECKING
import random

from catan.board import Board, Resource
from catan.player import Player, Action
from catan.util import CubeCoordinates
from catan.agent import Agent
if TYPE_CHECKING:
    from catan.game import Game

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
from catan.tensor_embeder import QNetwork
from catan.serialization import BrickRepresentation

BOARD_SIZE = 5

class RL_Agent(Agent):
    def __init__(self, board: Board, player: Player):
        super().__init__(board, player)
        
        # Define the dimensions for the Q-Network
        board_channels = 4 + 1  # Number of players + 1 for board state
        player_state_dim = 13 * 4 + 5  # Player states + dev cards
        action_dim = 7  # Number of possible actions
        
        # Initialize the Q-Network
        self.model = QNetwork(board_channels, player_state_dim, action_dim)
        
        # Initialize the RLAgent
        self.rl_agent = RLAgent(self.model)

    def get_action(self, game: 'Game', possible_actions: list[Action]) -> Action:
        return self.rl_agent.get_action(game, self.player, possible_actions)

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
        self.replay_buffer = deque(maxlen=10000)
        self.action_mapper = ActionMapper()

    def get_state(self, game: 'Game', player: 'Player'):
        """Generate a state representation using BrickRepresentation"""
        brick_rep = BrickRepresentation(size=BOARD_SIZE, num_players=len(game.player_agents), game=game, agent_player_num=player.index)
        brick_rep.encode_player_states(game, player)
        
        # Board state: Multi-channel tensor
        board_state = torch.tensor(brick_rep.board, dtype=torch.float32)
        
        # Player state: Structured vector
        player_state = torch.tensor(brick_rep.player_states, dtype=torch.float32).flatten()
        
        return board_state, player_state

    def get_action(self, game: 'Game', player: 'Player', possible_actions: list[Action]):
        """Select an action using epsilon-greedy strategy"""
        if random.random() < self.epsilon:
            return random.choice(possible_actions)  # Explore (random action)
        else:
            board_state, player_state = self.get_state(game, player)
            board_state = board_state.unsqueeze(0)  # Add batch dimension
            player_state = player_state.unsqueeze(0)
            
            # Get Q-values from the model
            q_values = self.model(board_state, player_state).detach().numpy().flatten()
            
            # Map Q-values to actions
            action_idx = np.argmax(q_values)
            return possible_actions[action_idx]  # Exploit (best action based on Q-values)

    def store_experience(self, state, action, reward, next_state, done):
        """Store the agent's experience in the replay buffer"""
        self.replay_buffer.append((state, action, reward, next_state, done))

    def train(self):
        """Train the agent based on experiences collected during the game"""
        if len(self.replay_buffer) < self.batch_size:
            return  # Not enough experiences to train

        # Sample a random batch from the replay buffer
        batch = random.sample(self.replay_buffer, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Convert to tensors
        board_states = torch.stack([s[0] for s in states])
        player_states = torch.stack([s[1] for s in states])
        actions = torch.tensor([self.action_mapper.get_action_index(a) for a in actions], dtype=torch.long)
        rewards = torch.tensor(rewards, dtype=torch.float32)
        next_board_states = torch.stack([s[0] for s in next_states])
        next_player_states = torch.stack([s[1] for s in next_states])
        dones = torch.tensor(dones, dtype=torch.float32)
        
        # Compute Q-values from the current state
        current_q_values = self.model(board_states, player_states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Compute the target Q-values using the Bellman equation
        with torch.no_grad():
            next_q_values = self.model(next_board_states, next_player_states).max(1)[0]
            target_q_values = rewards + self.gamma * next_q_values * (1 - dones)
        
        # Compute the loss (mean squared error)
        loss = torch.nn.functional.mse_loss(current_q_values, target_q_values)
        
        # Backpropagation and update the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update epsilon (decay exploration rate)
        self.epsilon = max(self.epsilon * self.epsilon_decay, 0.01)


class ActionMapper:
    def __init__(self):
        self.actions = [
            "endturnaction",
            "buildsettlementaction",
            "buildcityaction",
            "buildroadaction",
            "buydevelopmentcardaction",
            "usedevelopmentcardaction",
            "tradeaction",
        ]
        self.action_to_idx = {action: idx for idx, action in enumerate(self.actions)}
    
    def get_action_index(self, action: Action):
        """Convert a Catan action to an index"""
        action_name = action.__class__.__name__.lower()
        return self.action_to_idx.get(action_name, -1)  # Default to -1 for unknown actions
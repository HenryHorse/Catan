from typing import TYPE_CHECKING
import random

from catan.util import CubeCoordinates, print_debug
from catan.agent import Agent
if TYPE_CHECKING:
    from catan.game import Game

import torch
import torch.optim as optim
import numpy as np
from collections import deque
from catan.QNN import QNetwork
from catan.serialization import BrickRepresentation
import os


from catan.board import Board, Resource, RoadVertex, Road, DevelopmentCardType, DevelopmentCard
from catan.player import Player, Action, BuildSettlementAction, BuildCityAction, BuildRoadAction, \
    BuyDevelopmentCardAction, TradeAction, UseDevelopmentCardAction, EndTurnAction
from catan.game import GamePhase

from globals import  SELECTED_GRID_MODEL, BOARD_CHANNELS, PLAYER_STATE_DIM, ACTION_DIM

BOARD_SIZE = 5

# I put this function here because each Agent should have an associated model
def load_or_create_grid_model(model_path, board_channels, player_state_dim, action_dim):
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

class RL_Agent(Agent):
    shared_model = load_or_create_grid_model(SELECTED_GRID_MODEL, BOARD_CHANNELS, PLAYER_STATE_DIM, ACTION_DIM)

    def __init__(self, board: Board, player: Player):
        super().__init__(board, player)

        # Initialize the RLAgent
        self.rl_agent = RL_Model(RL_Agent.shared_model)

    def get_action(self, game: 'Game', possible_actions: list[Action]) -> Action:
        return self.rl_agent.get_action(game, self.player, possible_actions)

    def get_most_needed_resource(self, game: 'Game') -> Resource:
        return random.choice(list(Resource))
    
    def get_robber_placement(self, game: 'Game') -> CubeCoordinates:
        return CubeCoordinates(0, 0, 0)
    
    def get_player_to_steal_from(self, game: 'Game', options: list[int]) -> int:
        return random.choice(options)

    def store_experience(self, state, action, reward, next_state, done):
        self.rl_agent.store_experience(state, action, reward, next_state, done)

    def train(self):
        self.rl_agent.train()

    def get_model(self):
        return self.rl_agent.model

    def save_model(self):
        torch.save(RL_Agent.shared_model.state_dict(), SELECTED_GRID_MODEL)
        print_debug(f"Model saved to {SELECTED_GRID_MODEL}")


class RL_Model:
    def __init__(self, model: QNetwork, gamma=0.99, epsilon=1.0, epsilon_decay=0.99995, batch_size=12, learning_rate=0.001):
        self.model = model
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.replay_buffer = deque(maxlen=10000)
        self.action_mapper = ActionMapper()

    def get_action_heuristic(self, game: 'Game', possible_actions: list[Action], player: 'Player') -> Action:
            # The logic is straightforward: prioritize certain types of actions first, try others next. If it can't do anything, just end the turn
            # You can try swapping the order of the isinstance statements to see if one performs better than the other (i.e. prioritizing using dev cards early on)
            best_action = None
            best_score = -1
            for action in possible_actions:
                score = -1
                if isinstance(action, BuildSettlementAction):
                    score = self.evaluate_settlement_location(action.road_vertex, game)
                if isinstance(action, BuildCityAction):
                    score = self.evaluate_city_location(action.road_vertex, game)
                if isinstance(action, BuildRoadAction):
                    score = self.evaluate_road_location(action.road, game, player)
                if isinstance(action, TradeAction):
                    score = self.evaluate_trade(action, game, player)
                if isinstance(action, UseDevelopmentCardAction):
                    score = self.evaluate_dev_card(action.card, game)
                if score > best_score:
                    best_action = action
                    best_score = score
            if best_action:
                return best_action


            for action in possible_actions:
                if isinstance(action, BuyDevelopmentCardAction):
                    current_player = game.player_agents[player.index].player
                    if (current_player.resources[Resource.SHEEP] > 1
                            and current_player.resources[Resource.GRAIN] > 1
                            and current_player.resources[Resource.ORE] > 1):
                        return action


            return EndTurnAction()

    def evaluate_settlement_location(self, road_vertex: RoadVertex, game: 'Game') -> int:
        score = 0
        resource_types = set()
        dice_probability = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

        for tile in road_vertex.adjacent_tiles:
            if tile and tile.resource:
                score += dice_probability[tile.number]
                resource_types.add(tile.resource)

        # the more resource types there are adjacent to this road_vertex, the bigger the score
        score += len(resource_types)

        num_available_roads = 0
        for road in road_vertex.adjacent_roads:
            if road.owner is None:
                num_available_roads += 1
        score += num_available_roads

        if road_vertex.harbor:
            score += 5

        return score

    def evaluate_city_location(self, road_vertex: RoadVertex, game: 'Game') -> int:
        score = 0
        resource_types = set()
        dice_probability = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

        for tile in road_vertex.adjacent_tiles:
            if tile and tile.resource:
                score += 2 * dice_probability[tile.number]
                resource_types.add(tile.resource)

        # the more resource types there are adjacent to this road_vertex, the bigger the score
        score += len(resource_types)

        return score

    def evaluate_road_location(self, road: Road, game: 'Game', player: 'Player') -> int:
        score = 0
        current_player = game.player_agents[player.index].player

        for vertex in road.endpoints:
            if current_player.is_valid_settlement_location(vertex):
                score += self.evaluate_settlement_location(vertex, game)
        return score

    def evaluate_trade(self, trade_action: TradeAction, game: 'Game', player: 'Player') -> int:
        score = 0
        most_needed_resource = self.get_most_needed_resource(game, player)
        if most_needed_resource in trade_action.receiving:
            score += 10 # Reward for getting a required resource
            for resource in trade_action.giving:
                if player.resources[resource] == 1:
                    score -= 10 # Punishment for giving up a resource player only has 1 of
        return score

    def evaluate_dev_card(self, dev_card: DevelopmentCard, game: 'Game') -> int:
        score = 0
        match dev_card.card_type:
            case dev_card.card_type.KNIGHT:
                score += 3
            case dev_card.card_type.ROAD_BUILDING:
                score += 10
            case dev_card.card_type.YEAR_OF_PLENTY:
                score += 10
            case dev_card.card_type.MONOPOLY:
                score += 10
        return score

    def get_most_needed_resource(self, game: 'Game', player: 'Player') -> Resource:
        needed_resources = {
            BuildSettlementAction: [Resource.BRICK, Resource.WOOD, Resource.GRAIN, Resource.SHEEP],
            BuildCityAction: [Resource.ORE, Resource.ORE, Resource.ORE, Resource.GRAIN, Resource.GRAIN],
            BuildRoadAction: [Resource.BRICK, Resource.WOOD]
        }

        # Given the order of iteration, this will prioritize settlements, then cities, then roads if we have 0 of the resources for those 3
        for action, resources in needed_resources.items():
            possible_actions = player.get_all_possible_actions(game.board, game.game_phase == GamePhase.SETUP)
            if action in possible_actions:
                for resource in resources:
                    if player.resources[resource] == 0:
                        return resource

        # If we have at least 1 of every resource needed for settlements, cities, and roads, just pick the one we have the least of
        return min(player.resources, key=player.resources.get)

    def get_robber_placement(self, game: 'Game', player: 'Player') -> CubeCoordinates:
        highest_value_tile = None
        highest_value = -1

        for tile in game.board.tiles.values():
            if tile.has_robber:
                continue

            num_dependents = 0
            for road_vertex in tile.adjacent_road_vertices:
                if road_vertex.owner is not None and road_vertex.owner != player.index:
                    num_dependents += 1

            if num_dependents > highest_value:
                highest_value_tile = tile
                highest_value = num_dependents

        if highest_value_tile is not None:
            return highest_value_tile.cube_coords
        else:
            return CubeCoordinates(0, 0, 0)

    def get_player_to_steal_from(self, game: 'Game', options: list[int]) -> int:
        # Choose the player with the larger amount of resources to steal from
        player_resource_count = {}
        for option in options:
            player_resource_count[option] = game.player_agents[option].player.get_resource_count()
        return max(player_resource_count, key=player_resource_count.get)
    

    def get_state(self, game: 'Game', player: 'Player'):
        """Generate a state representation using BrickRepresentation"""
        brick_rep = BrickRepresentation(size=BOARD_SIZE, num_players=len(game.player_agents), game=game, agent_player_num=player.index)
        brick_rep.encode_all(player)
        
        # Board state: Multi-channel tensor
        board_state = torch.tensor(brick_rep.board, dtype=torch.float32)
        
        # Player state: Structured vector
        player_state = torch.tensor(brick_rep.player_states, dtype=torch.float32).flatten()
        
        return board_state, player_state

    def get_action(self, game: 'Game', player: 'Player', possible_actions: list[Action]) -> Action:
        """Select an action using epsilon-greedy strategy"""
        if random.random() < self.epsilon:
            print_debug("Heuristic action selected on epsilon of: ", self.epsilon)
            return self.get_action_heuristic(game, possible_actions, player)
        else:
            print_debug("Model action selected on epsilon of: ", self.epsilon)
            board_state, player_state = self.get_state(game, player)
            board_state = board_state.unsqueeze(0)  # Add batch dimension
            player_state = player_state.unsqueeze(0)
            
            # Get Q-values from the model
            q_values = self.model.forward(board_state, player_state).detach().numpy().flatten()

            # Get the full action space
            action_space = player.get_all_actions(game.board)

            if q_values.shape[0] != len(action_space):
                print_debug(f"Warning: Q-values shape {q_values.shape} does not match action space length {len(action_space)}")

            # Identify which actions are valid based on the current game state
            possible_actions_ordered = []
            valid_q_values = []
            for i, action in enumerate(action_space):
                if action in possible_actions:
                    possible_actions_ordered.append(action)
                    valid_q_values.append(q_values[i])

            # Select the action with the highest Q-value among valid actions
            if len(valid_q_values) == 0:
                print_debug("Warning: No valid actions found based on Q-values. Defaulting to EndTurnAction.")
                return EndTurnAction()
            action_idx = np.argmax(valid_q_values)
            return possible_actions_ordered[action_idx]  # Exploit (best action based on Q-values)

    def store_experience(self, state, action, reward, next_state, done):
        """Store the agent's experience in the replay buffer."""
        board_state, player_state = state
        next_board_state, next_player_state = next_state

        # Convert states to tensors
        board_state_tensor = torch.tensor(board_state, dtype=torch.float32)
        player_state_tensor = torch.tensor(player_state, dtype=torch.float32)
        next_board_state_tensor = torch.tensor(next_board_state, dtype=torch.float32)
        next_player_state_tensor = torch.tensor(next_player_state, dtype=torch.float32)

        # Store the experience
        self.replay_buffer.append((
            (board_state_tensor, player_state_tensor),
            action,
            reward,
            (next_board_state_tensor, next_player_state_tensor),
            done
        ))

    def train(self):
        """Train the agent based on experiences collected during the game."""
        if len(self.replay_buffer) < self.batch_size:
            print_debug("replay buff too small"+ " Buffer size: "+str(len(self.replay_buffer))+ " Batch size:  "+ str(self.batch_size))
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
        current_q_values = self.model.forward(board_states, player_states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Compute the target Q-values using the Bellman equation
        with torch.no_grad():
            next_q_values = self.model.forward(next_board_states, next_player_states).max(1)[0]
            target_q_values = rewards + self.gamma * next_q_values * (1 - dones)

        # Compute the loss (mean squared error)
        loss = torch.nn.functional.mse_loss(current_q_values, target_q_values)

        # Backpropagation and update the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update epsilon (decay exploration rate)
        self.epsilon = max(self.epsilon * self.epsilon_decay, 0.01)
        print_debug("updated epsilon:" + str(self.epsilon))


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

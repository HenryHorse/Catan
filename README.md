
# Settlers of Catan AI Project

Class: CSC 570
Instructor: Rodrigo Canaan

Welcome to our Settlers of Catan AI project repository! This project aims to develop AI bots capable of autonomously playing the popular board game Settlers of Catan. By leveraging artificial intelligence techniques, we seek to create bots that can make strategic decisions, manage resources, and compete against each other or human players.

## Project Overview

In this project, we represent the Settlers of Catan game board as a graph, where nodes represent hexagonal tiles and edges represent connections between them. The bots are trained using a reinforcement learning approach to perform the most optimal moves in any given board situation. Training will consist of rewards based around resource counts, game points, and other various factors.

# How to Run
Clone the repository, then run the following to install Pygame (consider making a virtual environment first)
```shell
    pip install -r requirements.txt
```

First, select the 4 agents in main.py  from the following list:
- RandomAgent
- HeuristicAgent
- RL_Agent
- HumanAgent

To change number of games in a simulation, edit NUM_GAMES in globals.py

To run a base game:
```shell
    python3 main.py
```

To run a simulation (make sure there are no human players):
```shell
    python3 main.py --simulate 1
```

To run a simulation with training (make sure there are no human players):
```shell
    python3 main.py --simulate 1 --train 1
```

# Reproducing Paper Results

To reproduce paper results, in globals.py please disable DEV_MODE, set NUM_GAMES to 100 or 1000, set the model to the one used in the paper, and then recreate the proper lineup of agents in main.py. Then, run a simulation without training to see results.

# Controls

IF THERE IS NO HUMAN PLAYER:

- **space bar**: Plays one turn, displays bot actions in terminal
- **'x' key**: Executes the entire game (all turns) at once
- **'r' key**: Resets board to a different initial configuration

IF THERE IS A HUMAN PLAYER:

- **'c' key**: Progresses game to next available human turn, or until a bot wins
- **'r' key**: Resets board to a different initial configuration
- Settlement/City/Road placement done on board
- Trading and dev card usage done on right sidebar
    - KNIGHT, MONOPOLY, HUMAN STEALING NOT IMPLEMENTED

# File Overview
- **board.py** contains functions that aid in creating and initializing the board data structure
- **evaluation.py** contains functions that evaluate locations on the board as potential building spots
- **game.py** contains the class representing the game state
- **helpers.py** contains two helper functions for finding values in a dictionary
- **main.py** creates a new board and starts running the simulation with PyGame
- **models.py** contains various data structures such as TileVertex and RoadVertex representing game characteristics
- **player.py** contains the class representing each player's state
- **turn.py** contains the function that determines the actions each player can take each turn
- **serialization.py** contains the code to serialize the board and player states
- **tensor_embeder.py** contains the code for the QNetwork and action selection
- **globals.py** contains the toggle for console logs, setting for number of simulation games, and selected RL model to use for the RL agent
- **random.py** contains random agent code
- **heuristic.py** contains heuristic agent code
- **rl_agent.py** contains reinforcement learning agent code
- **human.py** contains human player code, unused, is instead use as a flag for main program

## Contributors

- Shayan Daijavad
- Jacob Kelleran
- Aiden Smith
- Tymon Vu
- Sam Kaplan

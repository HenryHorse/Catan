
# Settlers of Catan AI Project

Welcome to our Settlers of Catan AI project repository! This project aims to develop AI bots capable of autonomously playing the popular board game Settlers of Catan. By leveraging artificial intelligence techniques, we seek to create bots that can make strategic decisions, manage resources, and compete against each other or human players.

## Project Overview

In this project, we represent the Settlers of Catan game board as a graph, where nodes represent hexagonal tiles and edges represent connections between them. The bots are trained using a reinforcement learning approach to perform the most optimal moves in any given board situation. Training will consist of rewards based around resource counts, game points, and other various factors.

# How to Run
Run the catan.py file and you should see the board pop up. You can reset the board to a different initial configuration using the 'r' key, and can run each bot's turn one at a time using the space bar. The terminal displays what the bot did during that move. You can execute the entire game (all turns) at once by hitting the 'x' key. 

# File Overview
- **board.py** contains functions that aid in creating and initializing the board data structure
- **evaluation.py** contains functions that evaluate locations on the board as potential building spots
- **game.py** contains the class representing the game state
- **helpers.py** contains two helper functions for finding values in a dictionary
- **main.py** creates a new board and starts running the simulation with PyGame
- **models.py** contains various data structures such as TileVertex and RoadVertex representing game characteristics
- **player.py** contains the class representing each player's state
- **turn.py** contains the function that determines the actions each player can take each turn

# How to Run
Run the catan.py file and you should see the board pop up. You can reset the board to a different initial configuration using the 'r' key, and can run each bot's turn one at a time using the space bar. The terminal displays what the bot did during that move. You can execute the entire game (all turns) at once by hitting the 'x' key. 

## Contributors

- Shayan Daijavad
- Jacob Kelleran
- Aiden Smith
- Tymon Vu
- Sam Kaplan

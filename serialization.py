from dataclasses import dataclass

from models import TileVertex, RoadVertex
from game import Game
from player import Player

BOARD_SIZE = 5

RESOURCE_MAP = {
    None: 0,
    'desert': 0,
    'wood': 1,
    'grain': 2,
    'sheep': 3,
    'ore': 4,
    'brick': 5,
}

@dataclass(init=False)
class BrickRepresentation:
    size: int
    width: int
    height: int
    board: list[list[int]]

    def __init__(self, size: int):
        self.size = size
        self.width = 4 * size + 1
        self.height = 2 * size + 1
        self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]
    
    def to_1d(self):
        return [cell for row in self.board for cell in row]
    
    def recursive_serialize(
            self,
            game: Game,
            center_tile: TileVertex,
            center: tuple[int, int] | None = None,
            visited: set[tuple[int, int]] | None = None
            ):
        center = center or (2 * self.size, self.size)
        visited = visited or set()
        if center in visited: return
        visited.add(center)

        self.serialize_tile(game, center_tile, center)
        for neighbor in center_tile.adjacent_tiles:
            dx, dy = BrickRepresentation.get_tile_displacement(center_tile, neighbor)
            self.recursive_serialize(game, neighbor, (center[0] + dx, center[1] + dy), visited)
    
    def serialize_tile(self, game: Game, tile: TileVertex, center: tuple[int, int]):
        x, y = center

        self.board[y][x] = tile.number or 0
        self.board[y][x - 1] = RESOURCE_MAP[tile.resource]
        self.board[y][x + 1] = 1 if (game.robber.x, game.robber.y) == (tile.x, tile.y) else 0

        for index, intersection in enumerate(tile.adjacent_roads):
            next_intersection = tile.adjacent_roads[(index + 1) % len(tile.adjacent_roads)]
            int_dx, int_dy = BrickRepresentation.get_intersection_displacement(tile, intersection)
            self.serialize_intersection(game, intersection, (x + int_dx, y + int_dy))
            road_dx, road_dy = BrickRepresentation.get_road_displacement(tile, intersection)
            self.serialize_road(game, intersection, next_intersection, (x + road_dx, y + road_dy))
    
    def serialize_intersection(self, game: Game, intersection: RoadVertex, position: tuple[int, int]):
        x, y = position
        for index, player in enumerate(game.players):
            player: Player = player
            for settlement in player.settlements:
                if (settlement.location.x, settlement.location.y) == (x, y):
                    self.board[y][x] = index + len(game.players)
                    return
            for city in player.cities:
                if (city.location.x, city.location.y) == (x, y):
                    self.board[y][x] = index + len(game.players) * 2
                    return
    
    def serialize_road(self, game: Game, intersection_1: RoadVertex, intersection_2: RoadVertex, position: tuple[int, int]):
        x, y = position
        for index, player in enumerate(game.players):
            player: Player = player
            for road in player.roads:
                if ((road.rv1.x, road.rv1.y) == (intersection_1.x, intersection_1.y) and \
                    (road.rv2.x, road.rv2.y) == (intersection_2.x, intersection_2.y)) or \
                   ((road.rv1.x, road.rv1.y) == (intersection_2.x, intersection_2.y) and \
                    (road.rv2.x, road.rv2.y) == (intersection_1.x, intersection_1.y)):
                    self.board[y][x] = index
                    return
    
    def get_intersection_displacement(tile: TileVertex, intersection: RoadVertex) -> tuple[int, int]:
        if intersection.x == tile.x and intersection.y < tile.y:
            return [0, -1]
        elif intersection.x == tile.x and intersection.y > tile.y:
            return [0, 1]
        elif intersection.y < tile.y and intersection.x < tile.x:
            return [-2, -1]
        elif intersection.y < tile.y and intersection.x > tile.x:
            return [2, -1]
        elif intersection.y > tile.y and intersection.x < tile.x:
            return [-2, 1]
        elif intersection.y > tile.y and intersection.x > tile.x:
            return [2, 1]
        raise ValueError("Invalid intersection position")
    
    # assumes that the intersections are ordered in a clockwise direction
    def get_road_displacement(tile: TileVertex, intersection_1: RoadVertex) -> tuple[int, int]:
        if intersection_1.x == tile.x and intersection_1.y < tile.y:
            return [1, -1]
        elif intersection_1.x == tile.x and intersection_1.y > tile.y:
            return [-1, 1]
        elif intersection_1.y < tile.y and intersection_1.x < tile.x:
            return [-1, -1]
        elif intersection_1.y < tile.y and intersection_1.x > tile.x:
            return [2, 0]
        elif intersection_1.y > tile.y and intersection_1.x < tile.x:
            return [-2, 0]
        elif intersection_1.y > tile.y and intersection_1.x > tile.x:
            return [1, 1]
        raise ValueError("Invalid intersection position")
    
    def get_tile_displacement(tile: TileVertex, neighbor: TileVertex) -> tuple[int, int]:
        if neighbor.y == tile.y and neighbor.x > tile.x:
            return [4, 0]
        elif neighbor.y == tile.y and neighbor.x < tile.x:
            return [-4, 0]
        elif neighbor.y < tile.y and neighbor.x < tile.x:
            return [-2, -2]
        elif neighbor.y < tile.y and neighbor.x > tile.x:
            return [2, -2]
        elif neighbor.y > tile.y and neighbor.x < tile.x:
            return [-2, 2]
        elif neighbor.y > tile.y and neighbor.x > tile.x:
            return [2, 2]
        raise ValueError("Invalid neighbor position")

from __future__ import annotations
# stupid python import
# i hate this
# evil stuff

# https://www.redblobgames.com/grids/hexagons/ Very useful source for hexagons

import random
import enum
import itertools

from catan.util import Point, CubeCoordinates, cube_coordinate_directions, hexagon_vertex_displacements

class Resource(enum.Enum):
    WOOD = 0
    GRAIN = 1
    SHEEP = 2
    ORE = 3
    BRICK = 4

class Harbor(enum.Enum):
    THREE_TO_ONE = 0
    ORE = 1
    WOOD = 2
    BRICK = 3
    GRAIN = 4
    SHEEP = 5

HARBOR_LOCATIONS = [
    (CubeCoordinates(1, -2, 1), 0, 1),
    (CubeCoordinates(2, -1, -1), 0, 1),
    (CubeCoordinates(2, 0, -2), 1, 2),
    (CubeCoordinates(1, 1, -2), 2, 3),
    (CubeCoordinates(-1, 2, -1), 2, 3),
    (CubeCoordinates(-2, 2, 0), 3, 4),
    (CubeCoordinates(-2, 1, 1), 4, 5),
    (CubeCoordinates(-1, -1, 2), 4, 5),
    (CubeCoordinates(0, -2, 2), 5, 0),
]

class Tile:
    cube_coords: CubeCoordinates
    resource: Resource | None
    number: int
    has_robber: bool
    # fixed length of 6
    # order: top-right, right, bottom-right, bottom-left, left, top-left
    adjacent_tiles: list[Tile | None]
    # fixed length of 6
    # order: top, top-right, bottom-right, bottom, bottom-left, top-left
    adjacent_road_vertices: list[RoadVertex]
    # fixed length of 6
    # order: top-right, right, bottom-right, bottom-left, left, top-left
    adjacent_roads: list[Road]

    def __init__(
            self,
            cube_coords: CubeCoordinates,
            resource: Resource | None,
            number: int,
            has_robber: bool = False,
            adjacent_tiles: list[Tile | None] | None = None,
            adjacent_road_vertices: list[RoadVertex] | None = None,
            adjacent_roads: list[Road] | None = None):
        self.cube_coords = cube_coords
        self.resource = resource
        self.number = number
        self.has_robber = has_robber
        self.adjacent_tiles = adjacent_tiles or [None] * 6
        self.adjacent_road_vertices = adjacent_road_vertices or [None] * 6
        self.adjacent_roads = adjacent_roads or [None] * 6
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tile):
            return False
        return self.cube_coords == other.cube_coords

    def get_screen_position(self, hex_radius: float) -> Point:
        return self.cube_coords.to_cartesian() * hex_radius

class RoadVertex:
    harbor: Harbor | None
    owner: int | None
    has_settlement: bool
    has_city: bool
    adjacent_tiles: list[Tile]
    adjacent_road_vertices: list[RoadVertex]
    adjacent_roads: list[Road]

    def __init__(
            self,
            harbor: Harbor | None = None,
            owner: int | None = None,
            has_settlement: bool = False,
            has_city: bool = False,
            adjacent_tiles: list[Tile | None] | None = None,
            adjacent_road_vertices: list[RoadVertex] | None = None,
            adjacent_roads: list[Road | None] | None = None):
        self.harbor = harbor
        self.owner = owner
        self.has_settlement = has_settlement
        self.has_city = has_city
        self.adjacent_tiles = adjacent_tiles or []
        self.adjacent_road_vertices = adjacent_road_vertices or []
        self.adjacent_roads = adjacent_roads or []

    def __eq__(self, other: object) -> bool:
        # maybe the worst eq function of all time
        if not isinstance(other, RoadVertex):
            return False
        for vertex, other_vertex in zip(self.adjacent_road_vertices, other.adjacent_road_vertices):
            if vertex.adjacent_tiles != other_vertex.adjacent_tiles:
                return False
        return self.adjacent_tiles == other.adjacent_tiles

    def __repr__(self) -> str:
        return f'RoadVertex(harbor={self.harbor}, owner={self.owner}, has_settlement={self.has_settlement}, has_city={self.has_city})'
    
    def get_screen_position(self, hex_radius: float) -> Point:
        tile = self.adjacent_tiles[0]
        index = tile.adjacent_road_vertices.index(self)
        displacement = hexagon_vertex_displacements[index] * hex_radius
        return tile.get_screen_position(hex_radius) + displacement

class Road:
    endpoints: tuple[RoadVertex, RoadVertex]
    owner: int | None
    adjacent_tiles: list[Tile]

    def __init__(
            self,
            endpoints: tuple[RoadVertex, RoadVertex],
            owner: int | None = None,
            adjacent_tiles: list[Tile | None] | None = None):
        self.endpoints = endpoints
        self.owner = owner
        self.adjacent_tiles = adjacent_tiles or []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Road):
            return False
        return self.endpoints == other.endpoints or self.endpoints == (other.endpoints[1], other.endpoints[0])
    
    def __repr__(self) -> str:
        return f'Road(endpoints={self.endpoints}, owner={self.owner})'


class Board:
    size: int
    center_tile: Tile
    tiles: dict[CubeCoordinates, Tile]
    road_vertices: list[RoadVertex]
    roads: list[Road]

    def __init__(self, size: int):
        assert size > 0
        self.size = size
        self.center_tile = Tile(CubeCoordinates(0, 0, 0), None, 0)
        self.tiles = {self.center_tile.cube_coords: self.center_tile}
        self.road_vertices = []
        self.roads = []

        # create tiles
        for i in range(1, size):
            # convert to list to prevent iterator runtime error
            tiles_list = list(self.tiles.values())
            for tile in tiles_list:
                self._extend_tile_in_all_directions(tile)
        
        # connect edge tiles that were not included
        for tile in self.tiles.values():
            self._connect_tile_to_neighbors(tile)

        # create road vertices
        for tile in self.tiles.values():
            self._create_road_vertices_on_tile(tile)
        
        # create roads
        for tile in self.tiles.values():
            self._create_roads_on_tile(tile)
        
        self.set_harbors()
        
        # verify
        for tile in self.tiles.values():
            assert len(tile.adjacent_road_vertices) == 6
            assert tile.adjacent_road_vertices.count(None) == 0
            assert len(tile.adjacent_roads) == 6
            assert tile.adjacent_roads.count(None) == 0
    
    def _extend_tile_in_all_directions(self, tile: Tile):
        for i, offset in enumerate(cube_coordinate_directions):
            if tile.adjacent_tiles[i] is not None:
                continue
            new_coords = tile.cube_coords + offset
            if new_coords not in self.tiles:
                self.tiles[new_coords] = Tile(new_coords, None, 0)
            tile.adjacent_tiles[i] = self.tiles[new_coords]
            self.tiles[new_coords].adjacent_tiles[(i + 3) % 6] = tile
    
    def _connect_tile_to_neighbors(self, tile: Tile):
        for i, offset in enumerate(cube_coordinate_directions):
            if tile.adjacent_tiles[i] is not None:
                continue
            new_coords = tile.cube_coords + offset
            if new_coords in self.tiles:
                tile.adjacent_tiles[i] = self.tiles[new_coords]
                self.tiles[new_coords].adjacent_tiles[(i + 3) % 6] = tile
    
    def _create_road_vertices_on_tile(self, tile: Tile):
        for i in range(6):
            if tile.adjacent_road_vertices[i] is not None:
                continue
            new_road_vertex = RoadVertex()
            tile.adjacent_road_vertices[i] = new_road_vertex
            new_road_vertex.adjacent_tiles.append(tile)
            self.road_vertices.append(new_road_vertex)
            if (tile_1 := tile.adjacent_tiles[i - 1]) is not None:
                tile_1.adjacent_road_vertices[(i + 2) % 6] = new_road_vertex
                new_road_vertex.adjacent_tiles.append(tile_1)
            if (tile_2 := tile.adjacent_tiles[i]) is not None:
                tile_2.adjacent_road_vertices[(i + 4) % 6] = new_road_vertex
                new_road_vertex.adjacent_tiles.append(tile_2)

    def _create_roads_on_tile(self, tile: Tile):
        for i in range(6):
            if tile.adjacent_roads[i] is not None:
                continue
            vert_1 = tile.adjacent_road_vertices[i]
            vert_2 = tile.adjacent_road_vertices[(i + 1) % 6]
            new_road = Road((vert_1, vert_2))
            self.roads.append(new_road)

            vert_1.adjacent_roads.append(new_road)
            vert_1.adjacent_road_vertices.append(vert_2)
            assert len(vert_1.adjacent_roads) <= 3
            assert len(vert_1.adjacent_road_vertices) <= 3
            vert_2.adjacent_roads.append(new_road)
            vert_2.adjacent_road_vertices.append(vert_1)
            assert len(vert_2.adjacent_roads) <= 3
            assert len(vert_2.adjacent_road_vertices) <= 3
            tile.adjacent_roads[i] = new_road
            if (shared_tile := tile.adjacent_tiles[i]) is not None:
                shared_tile.adjacent_roads[(i + 3) % 6] = new_road
    
    def set_harbors(self):
        remaining_harbor_types = list(Harbor) + [Harbor.THREE_TO_ONE] * (len(HARBOR_LOCATIONS) - len(Harbor))
        random.shuffle(remaining_harbor_types)

        for tile_coords, vert_1, vert_2 in HARBOR_LOCATIONS:
            harbor = remaining_harbor_types.pop()
            tile = self.tiles[tile_coords]
            tile.adjacent_road_vertices[vert_1].harbor = harbor
            tile.adjacent_road_vertices[vert_2].harbor = harbor

    def initialize_tile_info(self):
        resources_remaining: dict[Resource, int] = {}

        for _, resource in zip(range(len(self.tiles) - 1), itertools.cycle(Resource)):
            resources_remaining[resource] = resources_remaining.get(resource, 0) + 1
        
        # TODO: find a way to not hardcode this??? idk
        numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

        for tile in self.tiles.values():
            if len(resources_remaining) > 0:
                tile.resource = random.choice(list(resources_remaining.keys()))
                resources_remaining[tile.resource] -= 1
                if resources_remaining[tile.resource] == 0:
                    del resources_remaining[tile.resource]
                tile.number = random.choice(numbers)
                numbers.remove(tile.number)
            else:
                tile.has_robber = True
    
    def get_robber_tile(self) -> Tile | None:
        for tile in self.tiles.values():
            if tile.has_robber:
                return tile
        return None

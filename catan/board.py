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

    def __str__(self):
        return self.name.title()

class Harbor(enum.Enum):
    THREE_TO_ONE = 0
    ORE = 1
    WOOD = 2
    BRICK = 3
    GRAIN = 4
    SHEEP = 5

    def __str__(self):
        if self == Harbor.THREE_TO_ONE:
            return '3:1'
        return f'2:1 {self.name.title()}'

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


class DevelopmentCard(enum.Enum):
    KNIGHT = 0
    ROAD_BUILDING = 1
    YEAR_OF_PLENTY = 2
    MONOPOLY = 3
    VICTORY_POINT = 4

    def __str__(self):
        return self.name.replace('_', ' ').title()

class DevelopmentCardDeck:
    cards: list[DevelopmentCard]

    def __init__(self):
        self.cards = [DevelopmentCard.KNIGHT] * 14 + \
            [DevelopmentCard.ROAD_BUILDING] * 2 + \
            [DevelopmentCard.YEAR_OF_PLENTY] * 2 + \
            [DevelopmentCard.MONOPOLY] * 2 + \
            [DevelopmentCard.VICTORY_POINT] * 5
        random.shuffle(self.cards)

    def draw(self) -> DevelopmentCard:
        return self.cards.pop()
    
    def remaining_cards(self) -> int:
        return len(self.cards)


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
    
    def __hash__(self) -> int:
        return hash(self.cube_coords)

    def get_screen_position(self, hex_radius: float) -> Point:
        return self.cube_coords.to_cartesian() * hex_radius

class RoadVertex:
    parent_tile: Tile
    index_on_parent: int

    harbor: Harbor | None
    owner: int | None
    has_settlement: bool
    has_city: bool

    adjacent_tiles: list[Tile]
    adjacent_road_vertices: list[RoadVertex]
    adjacent_roads: list[Road]


    def __init__(
            self,
            parent_tile: Tile,
            index_on_parent: int,
            harbor: Harbor | None = None,
            owner: int | None = None,
            has_settlement: bool = False,
            has_city: bool = False,
            adjacent_tiles: list[Tile | None] | None = None,
            adjacent_road_vertices: list[RoadVertex] | None = None,
            adjacent_roads: list[Road | None] | None = None):
        self.parent_tile = parent_tile
        self.index_on_parent = index_on_parent

        self.harbor = harbor
        self.owner = owner
        self.has_settlement = has_settlement
        self.has_city = has_city

        self.adjacent_tiles = adjacent_tiles or []
        self.adjacent_road_vertices = adjacent_road_vertices or []
        self.adjacent_roads = adjacent_roads or []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RoadVertex):
            return False
        return self.parent_tile.cube_coords == other.parent_tile.cube_coords and \
            self.index_on_parent == other.index_on_parent
    
    def __hash__(self):
        return hash((self.parent_tile.cube_coords, self.index_on_parent))

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
    
    def __hash__(self) -> int:
        return hash(self.endpoints)
    
    def __repr__(self) -> str:
        return f'Road(endpoints={self.endpoints}, owner={self.owner})'


class Board:
    size: int
    center_tile: Tile
    tiles: dict[CubeCoordinates, Tile]
    road_vertices: list[RoadVertex]
    roads: list[Road]
    development_card_deck: DevelopmentCardDeck

    def __init__(self, size: int):
        assert size > 0
        self.size = size
        self.center_tile = Tile(CubeCoordinates(0, 0, 0), None, 0)
        self.tiles = {self.center_tile.cube_coords: self.center_tile}
        self.road_vertices = []
        self.roads = []
        self.development_card_deck = DevelopmentCardDeck()

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
            new_road_vertex = RoadVertex(tile, i)
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
        total_tiles = len(self.tiles)
        
        desert_tile = random.choice(list(self.tiles.values()))
        desert_tile.number = 0
        desert_tile.has_robber = True

        numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

        resources_remaining: dict[Resource, int] = {}

        for _, resource in zip(range(total_tiles - 1), itertools.cycle(Resource)):
            resources_remaining[resource] = resources_remaining.get(resource, 0) + 1

        for tile in self.tiles.values():
            if tile is desert_tile:
                continue
            tile.number = random.choice(numbers)
            numbers.remove(tile.number)
            tile.resource = random.choice(list(resources_remaining.keys()))
            resources_remaining[tile.resource] -= 1
            if resources_remaining[tile.resource] == 0:
                del resources_remaining[tile.resource]

        def is_valid_placement(tile, new_number, swap_partner=None, partner_new_number=None):
            for neighbor in tile.adjacent_tiles:
                neighbor_number = partner_new_number if neighbor == swap_partner else getattr(neighbor, 'number', None)
                if neighbor_number is not None:
                    if new_number in (6, 8) and neighbor_number in (6, 8):
                        return False
            return True

        def swap_tiles(tile1, tile2):
            tile1.number, tile2.number = tile2.number, tile1.number
            tile1.resource, tile2.resource = tile2.resource, tile1.resource
            tile1.has_robber, tile2.has_robber = tile2.has_robber, tile1.has_robber

        # Loop to fix conflicts where a 6 or 8 is adjacent to another 6 or 8.
        conflict_found = True
        while conflict_found:
            conflict_found = False
            for tile in self.tiles.values():
                if getattr(tile, 'number', None) in (6, 8):
                    for adj in tile.adjacent_tiles:
                        if getattr(adj, 'number', None) in (6, 8):
                            candidate_tiles = []
                            for candidate in self.tiles.values():
                                if candidate == tile:
                                    continue
                                if (is_valid_placement(tile, candidate.number, swap_partner=candidate, partner_new_number=tile.number) and
                                    is_valid_placement(candidate, tile.number, swap_partner=tile, partner_new_number=candidate.number)):
                                    candidate_tiles.append(candidate)
                            if candidate_tiles:
                                chosen = random.choice(candidate_tiles)
                                swap_tiles(tile, chosen)
                                conflict_found = True
                                break
                    if conflict_found:
                        break                    
    
    def get_robber_tile(self) -> Tile | None:
        for tile in self.tiles.values():
            if tile.has_robber:
                return tile
        return None
    
    def get_vertex_at_pos(self, mouse_pos: tuple[float, float],
                        hexagon_size: float,
                        displacement: Point,
                        threshold: float = 5) -> RoadVertex | None:
        """
        Return a vertex from the board's road_vertices if the mouse position is within a threshold distance.
        """
        for vertex in self.road_vertices:
            vertex_screen_pos = vertex.get_screen_position(hexagon_size) + displacement
            if abs(vertex_screen_pos.x - mouse_pos[0]) < threshold and abs(vertex_screen_pos.y - mouse_pos[1]) < threshold:
                return vertex
        return None

    def get_road_at_pos(self, mouse_pos: tuple[float, float],
                        hexagon_size: float,
                        displacement: Point,
                        threshold: float = 8) -> Road | None:
        """
        Return a road from the board's roads if the mouse position
        is within a threshold distance of the road segment.
        """
        for road in self.roads:
            v1, v2 = road.endpoints
            v1_pos = v1.get_screen_position(hexagon_size) + displacement
            v2_pos = v2.get_screen_position(hexagon_size) + displacement
            if self.is_point_near_line(mouse_pos, (v1_pos.x, v1_pos.y), (v2_pos.x, v2_pos.y), threshold):
                return road
        return None
    
    def is_point_near_line(self,
                       point: tuple[float, float],
                       line_start: tuple[float, float],
                       line_end: tuple[float, float],
                       threshold: float) -> bool:
        """
        Determine if the given point is within a threshold distance of a line
        segment defined by line_start and line_end.
        """
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end

        line_length_squared = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if line_length_squared == 0:
            return False  # The line is a single point

        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_squared))
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)

        return (px - closest_x) ** 2 + (py - closest_y) ** 2 < threshold ** 2

    def point_in_polygon(self, point: tuple[float, float], vertices: list[tuple[float, float]]) -> bool:
        """Ray-casting algorithm to determine if point is inside the polygon defined by vertices."""
        x, y = point
        inside = False
        n = len(vertices)
        for i in range(n):
            xi, yi = vertices[i]
            xj, yj = vertices[(i + 1) % n]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
        return inside

    def get_tile_at_pos(self, mouse_pos: tuple[float, float],
                        hexagon_size: float,
                        displacement: Point) -> Tile | None:
        """
        For each tile in the board, compute its hexagon polygon (using its center plus
        the hexagon_vertex_displacements scaled by hexagon_size) and return the first tile
        that contains the given mouse position.
        """
        for tile in self.tiles.values():
            center = tile.get_screen_position(hexagon_size) + displacement
            # Compute vertices for a regular hexagon
            vertices = []
            for disp in hexagon_vertex_displacements:
                vertex = center + (disp * hexagon_size)
                vertices.append((vertex.x, vertex.y))
            if self.point_in_polygon(mouse_pos, vertices):
                return tile
        return None


from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, other: float) -> Point:
        return Point(self.x * other, self.y * other)

    def __truediv__(self, other: float) -> Point:
        return Point(self.x / other, self.y / other)

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)
    
    def to_int_tuple(self) -> tuple[int, int]:
        return (int(self.x), int(self.y))

hexagon_vertex_displacements = [
    Point(0, 1),  # top
    Point(math.sqrt(3) / 2, 0.5),  # top-right
    Point(math.sqrt(3) / 2, -0.5),  # bottom-right
    Point(0, -1),  # bottom
    Point(-math.sqrt(3) / 2, -0.5),  # bottom-left
    Point(-math.sqrt(3) / 2, 0.5)  # top-left
]

@dataclass(frozen=True)
class OffsetCoordinates:
    # odd-r offset coordinates
    q: int
    r: int

@dataclass(frozen=True)
class CubeCoordinates:
    q: int
    r: int
    s: int

    def __add__(self, other: CubeCoordinates) -> CubeCoordinates:
        return CubeCoordinates(self.q + other.q, self.r + other.r, self.s + other.s)
    
    def __sub__(self, other: CubeCoordinates) -> CubeCoordinates:
        return CubeCoordinates(self.q - other.q, self.r - other.r, self.s - other.s)

    def to_cartesian(self) -> Point:
        height = 2
        width = math.sqrt(3)
        x = self.q * width + self.r * width / 2
        y = -self.r * height * 3 / 4
        return Point(x, y)

cube_coordinate_directions = [
    CubeCoordinates(1, -1, 0),  # top-right
    CubeCoordinates(1, 0, -1),  # right
    CubeCoordinates(0, 1, -1),  # bottom-right
    CubeCoordinates(-1, 1, 0),  # bottom-left
    CubeCoordinates(-1, 0, 1),  # left
    CubeCoordinates(0, -1, 1)   # top-left
]

@dataclass(frozen=True)
class DoubledCoordinates:
    col: int
    row: int

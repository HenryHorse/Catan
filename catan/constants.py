from catan.board import Resource

ROAD_COST = [Resource.BRICK, Resource.WOOD]
SETTLEMENT_COST = [Resource.BRICK, Resource.WOOD, Resource.GRAIN, Resource.SHEEP]
CITY_COST = [Resource.GRAIN, Resource.GRAIN, Resource.ORE, Resource.ORE, Resource.ORE]
DEVELOPMENT_CARD_COST = [Resource.SHEEP, Resource.GRAIN, Resource.ORE]

# Constants
BACKGROUND_COLOR = (0, 160, 255)
BOARD_BG_COLOR = (0, 160, 255)
STATS_BG_COLOR = (230, 230, 230)
TILE_COLOR = (154, 205, 50)
ROAD_COLOR = (0, 0, 0)
HOVER_COLOR = (255, 255, 0)

RESOURCE_COLORS = {
    'ORE': (129, 128, 128),
    'WOOD': (34, 139, 34),
    'BRICK': (178, 34, 34),
    'GRAIN': (220, 165, 32),
    'SHEEP': (154, 205, 50),
}
DESERT_COLOR = (255, 215, 90)

RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
ORANGE = (255, 102, 0)
BROWN = (101, 67, 33)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

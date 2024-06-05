from catan import *
import random

class Game:
    def __init__(self):
        self.occ_tiles = [] #list of occupied road vertices
        self.occ_roads = [] #list of occupied road vertices

class Settlement:
    def __init__(self, color, location):
        self.color = color
        self.location = location

class City:
    def __init__(self, color, location):
        self.color = color
        self.location = location

class Road:
    def __init__(self, color, rv1, rv2):
        # road connects road vertex to road vertex
        self.color = color
        self.rv1 = rv1
        self.rv2 = rv2

class Player:
    def __init__(self, color):
        self.color = color
        self.resources = {
            'forest': 0,
            'grain': 0,
            'sheep': 0,
            'ore': 0,
            'brick': 0,
        }
        self.dev_cards = []

        self.unbuilt_settlements = 5
        self.settlements = [] # think ab keeping track of location
       
        self.unbuilt_cities = 4
        self.cities = []

        self.unbuilt_roads = 15
        self.roads = [] 
        self.victory_points = 0 # need 10 to win

    # adding resources based on dice roll and where the settlements are 
    def add_resource(self, resource, amount):
        self.resources[resource] += amount

    def remove_resource(self, resource, amount):
        self.resources[resource] -= amount

    def add_dev_card(self, dev_card):
        self.dev_cards.append(dev_card)

    def remove_dev_card(self, dev_card):
        self.dev_cards.remove(dev_card)

    def build_settlement(self, location):
        # can only build settlement if unbuilt settlements > 0
        settlement = Settlement(self.color, location)
        self.settlements.append(settlement)
        self.unbuilt_settlements -= 1
        self.victory_points += 1

    def build_city(self, location):
        # can only build city if unbuilt cities > 0
        city = City(self.color, location)
        self.cities.append(city)
        self.unbuilt_cities -= 1
        self.victory_points += 2

    def build_road(self, loc1, loc2):
        road = Road(self.color, loc1, loc2)
        self.roads.append(road)
        self.unbuilt_roads -= 1

    def get_victory_points(self):
        return self.victory_points

def roll_dice(n):
    '''rolls dice n times and adds them'''
    total = 0
    for i in range(n):
        total += random.randint(1, 6)
    return total

' -------------------- Turn --------------------'

def turn_roll_dice():
    tile_number = roll_dice(2)
    # if the RoadVertex correspondng to settlement.location has tile w tile_number in the adjacent tiles, then give resources to the player.
    my_settlement_locs = {}
    for s in self.settlements:
        my_settlement_locs.add(s.location)
    for tile in tile_vertices:
        if tile.number == tile_number and (tile.x, tile.y) in my_settlement_locs:
            self.resources[tile.resource] += tile.number

def turn_trade():
    pass
def turn_build():
    pass

def turn(player, tile_vertices, road_vertices):
    if player.victory_points == 10:
        return True
    else:
        # 1) resource production/roll dice
        turn_roll_dice()
        # 2) trade

        # 3) build

def main():
    player_red = Player('red')
    player_blue = Player('blue')

    build_loc = (261.4359353944899, 400.0)
    if unbuilt_settlements > 0:
        build_settlement(build_loc)

    # testing stuff
    tile_vertices = get_tile_vertices()
    road_vertices = get_road_vertices()
    for tile in tile_vertices:
        print("center number: ", tile.number)
        print("\n(x,y): ", tile.x, tile.y)
    print("\n\ntile vertices:", tile_vertices, "list size", len(tile_vertices))
    print("\n\nroad vertices:", road_vertices, "list size", len(road_vertices))



if __name__ == '__main__':
    main()
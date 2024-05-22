from catan import *

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
            "lumber": 0,
            "brick": 0,
            "wool": 0,
            "grain": 0,
            "ore": 0
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

def turn():
    # roll dice
    # trade
    # build
    pass

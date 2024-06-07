from catan import *
import random
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

class DevelopmentCard:
    def __init__(self, card_type):
        self.card_type = card_type
        self.played = False

    def use_effect(self, player, game):
        if self.card_type == 'knight':
            # player can move robber
            pass
        elif self.card_type == 'victory_point':
            # add victory point
            pass
        elif self.card_type == 'road_building':
            # can place 2 roads as if just built them
            pass
        elif self.card_type == 'year_of_plenty':
            # draw 2 resource cards of choice from bank
            pass
        elif self.card_type == 'monopoly':
            # claim all resource cards of specific declared type
            pass
        
class Game:
    ''' keep track of the state of the game'''
    def __init__(self):
        self.occ_tiles = []  # occupied tile vertices
        self.occ_roads = []  # occupied road vertices
        self.players = []  # players in the game
        self.tile_vertices = []  # all tile vertices on the board
        self.road_vertices = []  # all road vertices on the board
        self.harbors = {} # key: location of harbor, val: trade ratio
    
    def initialize_harbors_dict(self):
        for rv in self.road_vertices:
            if rv.harbor:
                self.harbors[(rv.x, rv.y)] = rv.harbor_type

    def distribute_dev_cards(self):
        cards_per_type = {
            'knight': 14,
            'victory_point': 5,
            'road_building': 2,
            'year_of_plenty': 2,
            'monopoly': 2
        }
        # add correct number of each card to the deck
        for card_type, count in cards_per_type.items():
            for _ in range(count):
                self.dev_card_deck.append(DevelopmentCard(card_type))

        random.shuffle(self.dev_card_deck)

    def draw_dev_card(self):
        if len(self.dev_card_deck) > 0:
            return self.dev_card_deck.pop()
        return None

    def add_player(self, player):
        self.players.append(player)
        
    # def get_tile_vertices(self):
    #     return self.tile_vertices

    # def get_road_vertices(self):
    #     return self.road_vertices

    def is_valid_settlement_location(self, location):
        # if location is empty and not within one vertex of another settlement
        if location in self.occ_tiles:
            return False
        for neighbor in self.get_adjacent_vertices(location):
            if neighbor in self.occ_tiles:
                return False
        return True


    def is_valid_road_location(self, loc1, loc2):
        # check if road is connected to player's existing roads or settlements
        if loc1 in self.occ_roads or loc2 in self.occ_roads:
            return False
        if loc1 in self.occ_tiles or loc2 in self.occ_tiles:
            return False
        if loc1 in self.get_adjacent_vertices(loc2):
            return True
        return False

    def occupy_tile(self, location):
        self.occ_tiles.append(location)

    def occupy_road(self, loc1, loc2):
        self.occ_roads.append((loc1, loc2))
    
    def get_harbor_trade_ratio(self, player, resource):
        # default trade ratio is 4:1
        trade_ratio = 4

        for settlement in player.settlements:
            location = settlement.location
            if location in self.harbors:
                harbor_type = self.harbors[location]
                # sets trade ratio to minimum trade ratio
                if harbor_type == '3:1 any':
                    trade_ratio = min(trade_ratio, 3)
                elif harbor_type == f'2:1 {resource}':
                    trade_ratio = min(trade_ratio, 2)
        
        return trade_ratio

class Player:
    def __init__(self, color):
        self.color = color
        self.resources = {
            'wood': 0,
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
    
    def buy_dev_card(self, game):
        # dev card costs 1 ore, 1 wool, 1 grain
        self.remove_resource('ore', 1)
        self.remove_resource('wool', 1)
        self.remove_resource('grain', 1)

        card = game.draw_dev_card()
        self.dev_cards.append(card)

    def play_dev_card(self, card_type):
        for card in self.dev_cards:
            if card.card_type == card_type and not card.played:
                card.played = True
                card.use_effect(self, game)
                return True
        return False

    def build_settlement(self, location):
        # can only build settlement if unbuilt settlements > 0
        settlement = Settlement(self.color, location)
        self.settlements.append(settlement)
        self.unbuilt_settlements -= 1
        self.victory_points += 1

    def build_city(self, location):
        # can only build city if unbuilt cities > 0
        # check if the location has a settlement owned by the player
        self.settlements.remove(settlement_to_upgrade)
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
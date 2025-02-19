import random
from collections import defaultdict

from models import Settlement, City, Road
from evaluation import evaluate_settlement_location


class Player:
    def __init__(self, color):
        self.color = color
        self.is_human = False
        self.resources = {
            'wood': 0,
            'grain': 0,
            'sheep': 0,
            'ore': 0,
            'brick': 0,
        }
        self.resource_scores = {
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


        self.longest_road_size = 0
        self.has_longest_road = False

        self.army_size = 0
        self.has_largest_army = False

    def initialize_settlements_roads(self, game):
        ''' builds 2 settlements and 2 roads on the map in random valid locations,
            returns the location of the second settlement'''
        settlement_loc1 = self.find_random_valid_settlement_location(game)
        self.build_settlement(settlement_loc1)
        game.occupy_tile(settlement_loc1)
        _, resource_scores = evaluate_settlement_location(settlement_loc1, game)
        for resource in resource_scores:
            self.resource_scores[resource] += resource_scores[resource]
        print(f"{self.color} built 1st settlement at {(settlement_loc1.x, settlement_loc1.y)}")

        road_loc1 = self.find_random_valid_road_location(settlement_loc1, game)
        self.build_road(settlement_loc1, road_loc1)
        game.occupy_road(settlement_loc1, road_loc1)
        print(f"{self.color} built 1st road from {(settlement_loc1.x, settlement_loc1.y)} to {(road_loc1.x, road_loc1.y)}")

        settlement_loc2 = self.find_random_valid_settlement_location(game)
        self.build_settlement(settlement_loc2)
        game.occupy_tile(settlement_loc2)
        _, resource_scores = evaluate_settlement_location(settlement_loc1, game)
        for resource in resource_scores:
            self.resource_scores[resource] += resource_scores[resource]
        print(f"{self.color} built 2nd settlement at {(settlement_loc2.x, settlement_loc2.y)}")

        road_loc2 = self.find_random_valid_road_location(settlement_loc2, game)
        self.build_road(settlement_loc2, road_loc2)
        game.occupy_road(settlement_loc2, road_loc2)
        print(f"{self.color} built 2nd road from {(settlement_loc2.x, settlement_loc2.y)} to {(road_loc2.x, road_loc2.y)}")

        self.resources = {
            'wood': 0,
            'grain': 0,
            'sheep': 0,
            'ore': 0,
            'brick': 0,
        }

        # for all adjacent tiles to the settlement 2, add resource for player
        for tile in settlement_loc2.adjacent_tiles:
            self.add_resource(tile.resource, 1)



        # return settlement_loc2

    def find_random_valid_settlement_location(self, game):
        ''' returns a random road vertex that is valid '''
        valid_locations = [v for v in game.road_vertices if game.is_valid_initial_settlement_location(v)]
        location_scores = {}
        for valid_location in valid_locations:
            location_scores[valid_location], _ = evaluate_settlement_location(valid_location, game)
        # random_choice = random.choice(valid_locations)
        # # This prevents the initial settlements from being an edge location without being a harbor, because that is a bad move
        # while (len(random_choice.adjacent_tiles) == 2 or len(random_choice.adjacent_roads) == 2):
        #     random_choice = random.choice(valid_locations)
        best_location = max(location_scores.items(), key = lambda item: item[1])
        return best_location[0]



    def find_random_valid_road_location(self, settlement_location, game):
        """
        Returns a random adjacent vertex to the settlement that results in a valid road,
        i.e. one that isn’t already occupied.
        """
        valid_candidates = [
            candidate
            for candidate in settlement_location.adjacent_roads
            if game.is_valid_road_location(settlement_location, candidate, self)
        ]
        if valid_candidates:
            return random.choice(valid_candidates)
        else:
            print(f"No valid road placements available from settlement at ({settlement_location.x}, {settlement_location.y}).")
            return None


    def add_resource(self, resource, amount):
        if resource != 'desert':
            self.resources[resource] += amount

    def remove_resource(self, resource, amount):
        self.resources[resource] -= amount

    def buy_dev_card(self, game):
        # dev card costs 1 ore, 1 wool, 1 grain
        self.remove_resource('ore', 1)
        self.remove_resource('sheep', 1)
        self.remove_resource('grain', 1)

        card = game.draw_dev_card()
        if card.card_type == 'victory_point':
            self.victory_points += 1
        self.dev_cards.append(card)

    def play_dev_card(self, card_type, game):
        for card in self.dev_cards:
            if card.card_type == card_type and not card.played and card.card_type != 'victory_point':
                card.played = True
                print(f"{self.color} played dev card: {card.card_type}")
                card.use_effect(self, game)

                if card.card_type == 'knight':
                    self.army_size += 1

                return True
        return False

    def build_settlement(self, location):
        # can only build settlement if unbuilt settlements > 0
        settlement = Settlement(self.color, location)
        self.settlements.append(settlement)
        self.unbuilt_settlements -= 1
        self.victory_points += 1
        self.resources['grain'] -= 1
        self.resources['brick'] -= 1
        self.resources['wood'] -= 1
        self.resources['sheep'] -= 1

    def build_city(self, location):
        # can only build city if unbuilt cities > 0
        # check if the location has a settlement owned by the player
        for settlement in self.settlements:
            if settlement.location == location:
                self.settlements.remove(settlement)
        city = City(self.color, location)
        self.cities.append(city)
        self.unbuilt_cities -= 1
        self.victory_points += 1
        self.resources['grain'] -= 2
        self.resources['ore'] -= 3

    def build_road(self, loc1, loc2):
        road = Road(self.color, loc1, loc2)
        self.roads.append(road)
        self.unbuilt_roads -= 1
        self.resources['wood'] -= 1
        self.resources['brick'] -= 1


    def get_victory_points(self):
        return self.victory_points


    def find_longest_road_size(self):
        graph = defaultdict(list)
        for road in self.roads:
            graph[road.rv1].append(road)
            graph[road.rv2].append(road)

        max_length = 0
        best_path = []

        def dfs(vertex, visited_roads, current_length, current_path):
            nonlocal max_length, best_path
            if current_length > max_length:
                max_length = current_length
                best_path = current_path.copy()

            for road in graph.get(vertex, []):
                if road not in visited_roads:
                    visited_roads.add(road)
                    next_vertex = road.rv2 if road.rv1 == vertex else road.rv1
                    current_path.append(road)
                    dfs(next_vertex, visited_roads, current_length + 1, current_path)
                    current_path.pop()
                    visited_roads.remove(road)

        for vertex in graph:
            dfs(vertex, set(), 0, [])

        self.longest_road_size = max_length
        self.longest_road_path = best_path
        return max_length


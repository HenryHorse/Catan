from models import TileVertex, DevelopmentCard
import random


class Game:
    ''' keep track of the state of the game'''
    def __init__(self):
        self.occ_tiles = []  # occupied tile vertices
        self.occ_roads = []  # occupied road vertices
        self.players = []  # players in the game
        self.tile_vertices = []  # all tile vertices on the board
        self.road_vertices = []  # all road vertices on the board
        self.harbors = {} # key: location of harbor, val: trade ratio
        self.robber = TileVertex(0, 0) 
        self.dev_card_deck =[]
        self.largest_army_player = None
        self.largest_army_size = 2 # Initialized to 2 because the first person to get an army > 2 takes largest army
        self.longest_road_player = None
        self.longest_road_size = 4 # Initialized to 4 because the first person to get a road > 4 takes longest road
    
    def initialize_game(self, tile_vertices, road_vertices):
        # initialize vertices
        self.tile_vertices = tile_vertices
        self.road_vertices = road_vertices

        # initialize harbors dictionary
        for rv in self.road_vertices:
            if rv.harbor:
                self.harbors[(rv.x, rv.y)] = rv.harbor_type

        # set robber start location to desert
        for tile in tile_vertices:
            if tile.resource == 'desert':
                self.robber = TileVertex(tile.x, tile.y)
        print(f"robber placed at {(tile.x, tile.y)}")

        #initialize dev card deck
        self.distribute_dev_cards() 
        
    def add_player(self, player):
        self.players.append(player)

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

    # TODO Fix this so it only takes 1 resource from 1 person, not 1 from every person adjacent to robber
    def move_robber(self, location, player):
        ''' moves robber to specified location (x, y) and whoever moves gets to steal player's resources who has settlement adj to tile'''
        print(f"{player.color} moves robber to {location}")
        self.robber = location
        for adj in location.adjacent_roads:
            # check who has adjacent settlements
            for opp in self.players:
                for settlement in opp.settlements:
                    if settlement.location.x == adj.x and settlement.location.y == adj.y:
                        # take random resource from them
                        stealables = []
                        for resource in opp.resources:
                            if opp.resources[resource] > 0:
                                stealables.append(resource)
                        if len(stealables) > 0:
                            resource = random.choice(stealables)
                            print(f"{player.color} takes {resource} from {opp.color}")
                            player.add_resource(resource, 1)
                            opp.remove_resource(resource, 1)

    # def get_tile_vertices(self):
    #     return self.tile_vertices

    # def get_road_vertices(self):
    #     return self.road_vertices

    def is_valid_initial_settlement_location(self, location):
        # if location is empty and not within one vertex of another settlement
        if location in self.occ_tiles:
            return False
        for neighbor in location.adjacent_roads:
            if neighbor in self.occ_tiles:
                return False
        # Placing a settlement next to a desert tile is always a bad move
        for tile in location.adjacent_tiles:
            if tile.resource == 'desert':
                return False
        return True

    def is_valid_settlement_location(self, player, location):
        if location in self.occ_tiles:
            return False
        for neighbor in location.adjacent_roads:
            if neighbor in self.occ_tiles:
                return False
        for road in player.roads:
            if location == road.rv1 or location == road.rv2:
                return True
        return False

    def is_valid_road_location(self, loc1, loc2, player):
        # TODO: check if the road connects to player's existing roads
        # check if road is connected to player's existing roads or settlements
        if (loc1, loc2) in self.occ_roads or (loc2, loc1) in self.occ_roads:
            return False
        # if loc1 in self.occ_tiles or loc2 in self.occ_tiles:
        #     return False
        if loc1 in loc2.adjacent_roads:
            for road in player.roads:
                if loc1 == road.rv1 or loc1 == road.rv2:
                        return True
                elif loc2 == road.rv1 or loc2 == road.rv2:
                        return True
            for settlement in player.settlements:
                if loc1 == settlement.location or loc2 == settlement.location:
                    return True
            for city in player.cities:
                if loc1 == city.location or loc2 == city.location:
                    return True
            return False
        else:
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

    # def get_adjacent_vertices(self, vertex):
    #     ''' returns the adjacent tile vertices to the tile at location (x, y) '''
    #     x = vertex.x
    #     y = vertex.y
    #     for vertex in self.road_vertices:
    #         if vertex.x == x and vertex.y == y:
    #             return vertex.adjacent_tiles
    #     return []

    def award_largest_army(self, new_largest_army_player):
        if new_largest_army_player != self.largest_army_player:
            print(f"{new_largest_army_player.color} now has the largest army")

            if self.largest_army_player:
                print(f"{self.largest_army_player.color} loses largest army")
                self.largest_army_player.victory_points -= 2
                self.largest_army_player.has_largest_army = False

            new_largest_army_player.victory_points += 2
            new_largest_army_player.has_largest_army = True

            self.largest_army_size = new_largest_army_player.army_size
            self.largest_army_player = new_largest_army_player

    def award_longest_road(self, new_longest_road_player):
        if new_longest_road_player != self.longest_road_player:
            print(f"{new_longest_road_player.color} now has the longest road")

            if self.longest_road_player:
                print(f"{self.longest_road_player.color} loses longest road")
                self.longest_road_player.victory_points -= 2
                self.longest_road_player.has_longest_road = False

            new_longest_road_player.victory_points += 2
            new_longest_road_player.has_longest_road = True

            self.longest_road_size = new_longest_road_player.longest_road_size
            self.longest_road_player = new_longest_road_player


        


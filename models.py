import random

from turn import find_road_location, calc_needed_resources
from helpers import keywithmaxval


class TileVertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.adjacent_roads = []
        self.adjacent_tiles = []
        self.resource = None
        self.number = None

    def add_adjacent_tile(self, tile_vertex):
        if tile_vertex not in self.adjacent_tiles:
            self.adjacent_tiles.append(tile_vertex)

    def add_adjacent_road(self, road_vertex):
        if road_vertex not in self.adjacent_roads:
            self.adjacent_roads.append(road_vertex)

    def __repr__(self):
        return "Tile Vert: (" + str(self.x) + "," + str(self.y) + ")"


class RoadVertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.adjacent_roads = []
        self.adjacent_tiles = []
        self.harbor = False
        self.harbor_type = None
        self.order = None

    def add_adjacent_tile(self, tile_vertex):
        if tile_vertex not in self.adjacent_tiles:
            self.adjacent_tiles.append(tile_vertex)

    def add_adjacent_road(self, road_vertex):
        if road_vertex not in self.adjacent_roads:
            self.adjacent_roads.append(road_vertex)

    def __repr__(self):
        return "Road Vert: (" + str(self.x) + "," + str(self.y) + ")"


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
            location = random.choice(game.tile_vertices) #TODO: change from random?
            game.move_robber(location, player)
        elif self.card_type == 'victory_point':
            # add victory point
            player.victory_points += 1
        elif self.card_type == 'road_building':
            # can place 2 roads as if just built them
            loc1, loc2 = find_road_location(player, game)
            loc3, loc4 = find_road_location(player, game)
            if loc1 and loc2:
                player.build_road(loc1, loc2)
                game.occupy_road(loc1, loc2)
                print(f"{player.color} built road between {loc1} and {loc2}")
            if loc3 and loc4:
                player.build_road(loc3, loc4)
                game.occupy_road(loc3, loc4)
                print(f"{player.color} built road between {loc3} and {loc4}")
        elif self.card_type == 'year_of_plenty':
            # draw 2 most needed resource cards of choice from bank
            needed_resources = calc_needed_resources(player)
            for _ in range(2): #get two
                target_resource = keywithmaxval(needed_resources)
                player.resources[target_resource] +=1
                print(f"{player.color} takes 1 {target_resource} from bank")

        elif self.card_type == 'monopoly':
            # claim all resource cards of player's most needed resource
            needed_resources = calc_needed_resources(player)
            target_resource = keywithmaxval(needed_resources)
            for opponent in game.players:
                if opponent != player:
                    # take all their resources
                    amount = opponent.resources[target_resource]
                    opponent.remove_resource(target_resource, amount)
                    player.add_resource(target_resource, amount)
                    print(f"{player.color} takes {amount} {target_resource} from opponent")

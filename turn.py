from catan import *
from game import * # includes Player, Game, Settlement, Road, City classes

def main():
    player_red = Player('red')
    player_blue = Player('blue')

    game = Game()
    game.tile_vertices = get_tile_vertices()  
    game.road_vertices = get_road_vertices()

    while not turn(player_red, game):
        pass
    print("Red player wins!")

def turn(player, game):
    if player.victory_points >= 10:
        return True
    else:
        # 1) resource production/roll dice
        turn_roll_dice()
        # 2) trade
        turn_trade(player)
        # 3) build
        turn_build(player, game)

def turn_roll_dice():
    ''' gives player resources they own settlements on from the dice roll'''
    tile_number = roll_dice(2)
    # if the RoadVertex correspondng to settlement.location has tile w tile_number in the adjacent tiles, give resources to the player
    my_settlement_locs = {}
    for s in self.settlements:
        my_settlement_locs.add(s.location)
    for tile in tile_vertices:
        if tile.number == tile_number and (tile.x, tile.y) in my_settlement_locs:
            self.resources[tile.resource] += tile.number

def turn_trade(player):
    ''' trade any excess resources for needed ones'''
    needed_resources = {'brick': 0, 'wood': 0, 'grain': 0, 'sheep': 0, 'ore': 0}
    
    # check what player can build and set needed resources
    #building a settlement requires 1 brick, 1 wood, 1 grain, 1 sheep
    if can_build_settlement(player):
        needed_resources['brick'] += 1
        needed_resources['wood'] += 1
        needed_resources['grain'] += 1
        needed_resources['sheep'] += 1
    # building a road requires 1 brick and 1 wood
    elif can_build_road(player): 
        needed_resources['brick'] += 1
        needed_resources['wood'] += 1
    #building a city requires 3 grain and 2 ore
    elif can_build_city(player):
        needed_resources['grain'] += 2
        needed_resources['ore'] += 3
    
    # TODO: add more advanced game logic
        if player.resources[resource] < amount:
            # TODO: implement trade logic
            print(f"{player.color} needs {amount - player.resources[resource]} {resource}")

def turn_build(player, game):
    ''' build the first thing the player can (for now, change later?)'''
    if can_build_settlement(player):
        location = find_settlement_location(game)
        player.build_settlement(location)
    elif can_build_road(player):
        loc1, loc2 = find_road_location(game)
        player.build_road(loc1, loc2)
    elif can_build_city(player):
        location = find_city_location(game)
        player.build_city(location)

def roll_dice(n):
    '''rolls dice n times and adds them'''
    total = 0
    for i in range(n):
        total += random.randint(1, 6)
    return total

def can_build_settlement(player):
    return (player.resources['brick'] >= 1 and 
            player.resources['wood'] >= 1 and 
            player.resources['grain'] >= 1 and 
            player.resources['sheep'] >= 1 and 
            player.unbuilt_settlements > 0)

def can_build_road(player):
    return (player.resources['brick'] >= 1 and 
            player.resources['wood'] >= 1 and 
            player.unbuilt_roads > 0)

def can_build_city(player):
    return (player.resources['grain'] >= 2 and 
            player.resources['ore'] >= 3 and 
            player.unbuilt_cities > 0)

def find_settlement_location(game):
    # TODO: find valid settlement location, set to 0,0 for now
    return (0, 0)

def find_road_location(game):
    # TODO: find valid road location, set to 0,0 for now
    return (0, 0), (0, 1)  

def find_city_location(game):
    # TODO: find valid city location, set to 0,0 for now
    return (0, 0)

# def main():
#     player_red = Player('red')
#     player_blue = Player('blue')

#     build_loc = (261.4359353944899, 400.0)
#     if unbuilt_settlements > 0:
#         build_settlement(build_loc)

#     # testing stuff
#     # tile_vertices = get_tile_vertices()
#     # road_vertices = get_road_vertices()
#     # for tile in tile_vertices:
#     #     print("center number: ", tile.number)
#     #     print("\n(x,y): ", tile.x, tile.y)
#     # print("\n\ntile vertices:", tile_vertices, "list size", len(tile_vertices))
#     # print("\n\nroad vertices:", road_vertices, "list size", len(road_vertices))

if __name__ == '__main__':
    main()

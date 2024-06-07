from catan import *
from game import * # includes Player, Game, Settlement, Road, City classes

def main():
    player_red = Player('red')
    player_blue = Player('blue')

    game = Game()
    game.tile_vertices = get_tile_vertices()  
    game.road_vertices = get_road_vertices()
    game.initialize_harbors_dict()

    # while not turn(player_red, game):
    #     pass
    # print("Red player wins!")

    # test getting resources
    # res = key, val = random.choice(list(game.harbors.items()))
    # player_blue.settlements.append((key))
    # turn(player_red, game)

def turn(player, game):
    if player.victory_points >= 10:
        return True
    else:
        # 1) resource production/roll dice
        turn_roll_dice(player, game)
        # 2) trade
        turn_trade(player, game)
        # 3) build
        turn_build(player, game)

def turn_roll_dice(player, game):
    tile_vertices = game.tile_vertices
    ''' gives player resources they own settlements on from the dice roll'''
    tile_number = roll_dice(2)
    print(player.color, "player rolled number: ", tile_number)
    # if the RoadVertex correspondng to settlement.location has tile w tile_number in the adjacent tiles, give resources to the player
    for p in game.players:
        player_settlement_locs = {}
        for s in p.settlements:
            player_settlement_locs.add(s.location)
        for tile in tile_vertices:
            if tile.number == tile_number and (tile.x, tile.y) in player_settlement_locs:
                p.resources[tile.resource] += tile.number
                print(p.color, "received", tile.number, tile.resource)

def turn_trade(player, game):
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

    for resource, amount in needed_resources.items():
        if player.resources[resource] < amount:
            # calculate the deficit
            deficit = amount - player.resources[resource]
            
            # try trading w other players first
            while deficit > 0:
                trade_made = False
                for other_player in game.players:
                    if other_player != player:
                        other_player, trade_resource = can_domestic_trade(player, resource, game.players)
                        if other_player:
                            print(f"{player.color} trades with {other_player.color} for {resource}")
                            player.resources[resource] += 1
                            player.resources[trade_resource] -= 1
                            other_player.resources[resource] -= 1
                            other_player.resources[trade_resource] += 1
                            deficit -= 1
                            trade_made = True
                            break  # reevaluate deficit
                if not trade_made:
                    break  # exit loop if no trades made
            
            # then try maritime trade
            while deficit > 0:
                bank_resource, trade_amount = can_maritime_trade(player, resource, game)
                if bank_resource:
                    print(f"{player.color} trades with the bank for {resource}")
                    player.resources[resource] += 1
                    player.resources[bank_resource] -= trade_amount
                    deficit -= 1
                else:
                    break


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

# ---------- roll dice helper methods ----------

def roll_dice(n):
    '''rolls dice n times and adds them'''
    total = 0
    for i in range(n):
        total += random.randint(1, 6)
    return total

# ---------- trade helper methods ----------

def can_maritime_trade(player, resource_needed):
    # check for maritime trade: 4:1 ratio, give 4 resources to "bank", take 1
    # if they have harbor, use the min trade ratio from that
    trade_ratio = game.get_harbor_trade_ratio(player, resource_needed)
    for resource, amount in player.resources.items():
        if resource != resource_needed and amount >= trade_ratio:
            return resource, trade_ratio
    return None, 0

def can_domestic_trade(player, resource_needed, players):
    # attempt to trade with other players
    for other_player in players:
        if other_player != player:
            for resource, amount in other_player.resources.items():
                if resource == resource_needed and amount > 0:
                    # assume 1:1 resource trade
                    if other_player.resources[needed_resource] > 0:
                        return other_player, resource
    return None, None

# ---------- build helper methods ----------

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

def find_settlement_location(player, game):
    ''' finds a settlement location based on valid locations and optimal locations'''
    best_location = None
    best_score = -1
    
    for vertex in game.road_vertices:
        if game.is_valid_settlement_location(vertex):
            score = evaluate_settlement_location(vertex, game)
            if score > best_score:
                best_location = vertex
                best_score = score

    return best_location

def find_road_location(player, game):
    ''' finds a road location based on valid locations and optimal locations'''
    best_loc1, best_loc2 = None, None
    best_score = -1
    
    for road in game.road_vertices:
        for neighbor in game.get_adjacent_vertices(road):
            if game.is_valid_road_location(road, neighbor):
                score = evaluate_road_location(road, neighbor, game)
                if score > best_score:
                    best_loc1, best_loc2 = road, neighbor
                    best_score = score

    return best_loc1, best_loc2

def find_city_location(player, game):
    ''' finds a city location based on valid locations and optimal locations'''
    best_location = None
    best_score = -1
    
    for settlement in player.settlements:
        score = evaluate_city_location(settlement.location, game)
        if score > best_score:
            best_location = settlement.location
            best_score = score

    return best_location

def evaluate_settlement_location(location, game):
    '''returns calculated score for how settlement good location is based on adjacent resoucres and harbors '''
    # TODO: change this??
    score = 0
    adjacent_tiles = game.get_adjacent_tiles(location)
    resource_values = {
        'brick': 0,
        'wood': 0,
        'grain': 0,
        'sheep': 0,
        'ore': 0
    }
    for tile in adjacent_tiles:
        resource_values[tile.resource] += tile.value
    for value in resource_values.values():
        score += value
    if location in game.harbors:
        score += 3  # Arbitrary bonus value for being near a harbor
    return score

def evaluate_road_location(loc1, loc2, game):
    '''returns calculated score for how good road location is '''
    score = 0
    if game.is_valid_road_location(loc1, loc2):
        score += 1
    return score

def evaluate_city_location(location, game):
    score = 0
    adjacent_tiles = game.get_adjacent_tiles(location)
    for tile in adjacent_tiles:
        score += tile.value
    # points for upgrading
    score += 2 
    return score

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

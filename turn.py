
import random

from evaluation import evaluate_settlement_location, evaluate_road_location, evaluate_city_location
from helpers import keywithminval


def turn(player, game, disable_trading):
    print(f"Current Victory Points: {player.victory_points}")
    # 1) resource production/roll dice
    turn_roll_dice(player, game)
    # buy dev cards
    if(player.resources['ore'] > 1 and player.resources['sheep'] > 1 and player.resources['grain'] > 1 and can_buy_dev_card(game)):
        print(f"player buys dev card")
        player.buy_dev_card(game)
    if player.victory_points >= 10:
        return True
    # play dev cards
    if((len(player.dev_cards)) > 0):
        player.play_dev_card((random.choice(player.dev_cards)).card_type, game)
    if player.army_size > game.largest_army_size:
        game.award_largest_army(player)
    if player.victory_points >= 10:
        return True
    # 2) trade
    turn_trade(player, game, disable_trading)
    print(player.resources)
    # 3) build
    turn_build(player, game)
    if player.victory_points >= 10:
        return True
    
def turn_roll_dice(player, game):
    ''' gives player resources they own settlements on from the dice roll'''
    tile_number = roll_dice(2)
    print(f"{player.color} player rolled number: {tile_number}")

    if tile_number == 7:
        # no one receives any resources
        print("7 rolled! No one gets any resources.")
        # every player that has more than 7 resource cards must select half of them and return them to bank
        for p in game.players:
            total_resource_count = sum(p.resources.values())
            print(f"{p.color} has {total_resource_count} resource cards")
            if total_resource_count > 7:
                print(f"{p.color} has more than 7 resource cards!")
                needed_resources = calc_needed_resources(p)
                print(f"{p.color}'s resources: {p.resources}")
                print(f"{p.color}'s needed resources:'{needed_resources}")
                for _ in range(total_resource_count // 2):
                    target_resource = keywithminval(needed_resources)
                    if p.resources[target_resource] > 1:
                        print(f"{p.color} loses 1 {target_resource}")
                        p.remove_resource(target_resource, 1)
                    else:
                        valid_resources = [resource for resource, amount in p.resources.items() if amount > 0]
                        random_resource = random.choice(valid_resources)
                        print(f"{p.color} loses 1 {random_resource}")
                        p.remove_resource(random_resource, 1)
            print(f"{p.color}'s resources: {p.resources}")
        # player moves robber
        location = random.choice(game.tile_vertices)
        game.move_robber(location, player)

    else:
        # find all tiles that match the rolled number
        matching_tiles = [tile for tile in game.tile_vertices if tile.number == tile_number]

        for tile in matching_tiles:
            print(f"tile {tile_number} at ({tile.x}, {tile.y}) with resource {tile.resource}")

            for player in game.players:
                for settlement in player.settlements:
                    # checl if the settlement is adjacent to the tile
                    if (tile.x, tile.y) in [(v.x, v.y) for v in settlement.location.adjacent_tiles]:
                        player.resources[tile.resource] += 1
                        print(f"{player.color} player received 1 {tile.resource} from settlement")

                for city in player.cities:
                    if (tile.x, tile.y) in [(v.x, v.y) for v in city.location.adjacent_tiles]:
                        player.resources[tile.resource] += 2
                        print(f"{player.color} player received 2 {tile.resource} from city")

def turn_trade(player, game, disable_trading):
    ''' trade any excess resources for needed ones'''
    needed_resources = calc_needed_resources(player)
    for resource, amount in needed_resources.items():
        if player.resources[resource] < amount:
            # calculate the deficit
            deficit = amount - player.resources[resource]
            
            # try trading w other players first
            if disable_trading is False:
                while deficit > 0:
                    trade_made = False
                    for other_player in game.players:
                        if other_player != player:
                            other_player, trade_resource = can_domestic_trade(player, resource, game.players)
                            if other_player:
                                for potential_exchange_resource in player.resources:
                                    trade_player, exchange_resource = can_domestic_trade(other_player, potential_exchange_resource, game.players)
                                    if trade_player and player.color == trade_player.color:
                                        print(f"{player.color} trades with {other_player.color} for {resource} giving {exchange_resource}")
                                        player.resources[resource] += 1
                                        player.resources[exchange_resource] -= 1
                                        other_player.resources[resource] -= 1
                                        other_player.resources[exchange_resource] += 1
                                        deficit -= 1
                                        trade_made = True
                                        break
                                if trade_made:
                                    break
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
        location = find_settlement_location(player, game)
        if location is not None:
            player.build_settlement(location)
            game.occupy_tile(location)
            _, resource_scores = evaluate_settlement_location(location, game)
            for resource in resource_scores:
                player.resource_scores[resource] += resource_scores[resource]
            print(f"{player.color} built settlement at {location}")
    if can_build_city(player):
        location = find_city_location(player, game)
        if location is not None:
            player.build_city(location)
            print(f"{player.color} upgraded settlement to city at {location}")
    if can_build_road(player):
        loc1, loc2 = find_road_location(player, game)
        if loc1 is not None and loc2 is not None:
            player.build_road(loc1, loc2)
            game.occupy_road(loc1, loc2)
            print(f"{player.color} built road between {loc1} and {loc2}")
            if player.find_longest_road_size() > game.longest_road_size:
                game.award_longest_road(player)
    


# ---------- roll dice helper methods ----------

def roll_dice(n):
    '''rolls dice n times and adds them'''
    total = 0
    for i in range(n):
        total += random.randint(1, 6)
    return total

def can_buy_dev_card(game):
    return game.dev_card_deck

# ---------- trade helper methods ----------
def calc_needed_resources(player):
    needed_resources = {'brick': 0, 'wood': 0, 'grain': 0, 'sheep': 0, 'ore': 0}
    
    # check what player can build and set needed resources
    #building a settlement requires 1 brick, 1 wood, 1 grain, 1 sheep
    for i in range(0, player.unbuilt_settlements):
        needed_resources['brick'] += 1
        needed_resources['wood'] += 1
        needed_resources['grain'] += 1
        needed_resources['sheep'] += 1
    #building a city requires 3 grain and 2 ore
    for i in range(0, player.unbuilt_cities):
        needed_resources['grain'] += 2
        needed_resources['ore'] += 3
    # building a road requires 1 brick and 1 wood
    for i in range(0, player.unbuilt_roads):
        needed_resources['brick'] += 1
        needed_resources['wood'] += 1
    
    return needed_resources

def can_maritime_trade(player, resource_needed, game):
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
                    if (resource == 'wood' or resource == 'brick') and can_build_road(other_player):
                        continue
                    if (resource == 'wood' or resource == 'brick' or resource == 'grain' or resource == 'sheep') and can_build_settlement(other_player):
                        continue
                    if (resource == 'grain' or resource == 'ore') and can_build_city(other_player):
                        continue
                    # assume 1:1 resource trade
                    if other_player.resources[resource_needed] > 0:
                        return other_player, resource_needed
    return None, None

# ---------- build helper methods ----------


def can_build_settlement(player):
    return (player.resources['brick'] >= 1 and 
            player.resources['wood'] >= 1 and 
            player.resources['grain'] >= 1 and 
            player.resources['sheep'] >= 1 and 
            player.unbuilt_settlements > 0)
    # return player.unbuilt_settlements > 0

def can_build_road(player):
    return (player.resources['brick'] >= 1 and 
        player.resources['wood'] >= 1 and 
        player.unbuilt_roads > 0)
    # return player.unbuilt_roads > 0

def can_build_city(player):
    return (player.resources['grain'] >= 2 and 
            player.resources['ore'] >= 3 and 
            player.unbuilt_cities > 0)
    # return player.unbuilt_cities > 0

def find_settlement_location(player, game):
    ''' finds a settlement location based on valid locations and optimal locations'''
    best_location = None
    best_score = -1
    best_resource_scores = None
    
    for vertex in game.road_vertices:
        if game.is_valid_settlement_location(player, vertex):
            score, resource_scores = evaluate_settlement_location(vertex, game)
            if score > best_score:
                best_location = vertex
                best_score = score
                best_resource_scores = resource_scores

    if best_location is not None:
        for resource in best_resource_scores:
            player.resource_scores[resource] += best_resource_scores[resource]
    return best_location

def find_road_location(player, game):
    ''' finds a road location based on valid locations and optimal locations'''
    best_loc1, best_loc2 = None, None
    best_score = -1
    
    for road in game.road_vertices:
        for neighbor in road.adjacent_roads:
            if game.is_valid_road_location(road, neighbor, player):
                score = evaluate_road_location(road, neighbor, game, player)
                if score > best_score:
                    best_loc1, best_loc2 = road, neighbor
                    best_score = score
    # print(f"Best road location found between {best_loc1} and {best_loc2}")
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



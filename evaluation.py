def count_combos(n):
    count = 0
    for i in range(1, 7):
        for j in range(1, 7):
            if i + j == n:
                count += 1
    return count


def evaluate_settlement_location(location, game):
    '''returns calculated score for how settlement good location is based on adjacent resoucres and harbors '''
    score = 0
    adjacent_tiles = location.adjacent_tiles
    resource_values = {
        'brick': 0,
        'wood': 0,
        'grain': 0,
        'sheep': 0,
        'ore': 0
    }
    for tile in adjacent_tiles:
        if tile.resource != 'desert':
            resource_values[tile.resource] += count_combos(tile.number)
    for value in resource_values.values():
        score += value
    if location in game.harbors:
        score += 1  # Arbitrary bonus value for being near a harbor
    return score, resource_values


def evaluate_road_location(loc1, loc2, game, player):
    '''returns calculated score for how good road location is '''
    score = 0
    if game.is_valid_road_location(loc1, loc2, player):
        if game.is_valid_settlement_location(player, loc2):
            score, resource_scores = evaluate_settlement_location(loc2, game)
            for resource in resource_scores:
                if player.resource_scores[resource] == 0 and resource_scores[resource] != 0:
                    score += 3
                elif player.resource_scores[resource] < resource_scores[resource]:
                    score += 1
    return score


def evaluate_city_location(location, game):
    '''returns calculated score for how good city location is '''
    score = 0
    adjacent_tiles = []
    for vertex in game.road_vertices:
        if (vertex.x, vertex.y) == location:
            adjacent_tiles = vertex.adjacent_tiles
    for tile in adjacent_tiles:
        score += tile.number
    # points for upgrading
    score += 2
    return score

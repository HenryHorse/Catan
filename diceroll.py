import random

def initialize_tiles(centers):
    resources = ['forest', 'grain', 'sheep', 'ore', 'brick', 'desert']
    resource_distribution = {
        'forest': 4,
        'grain': 4,
        'sheep': 4,
        'ore': 3,
        'brick': 3,
        'desert': 1
    }

    numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

    random.shuffle(centers)
    for center in centers:
        if resource_distribution['desert'] > 0:
            center.resource = 'desert'
            center.number = None
            resource_distribution['desert'] -= 1
        else:
            resource = random.choices(resources[:-1], weights=[resource_distribution[r] for r in resources[:-1]])[0]
            center.resource = resource
            resource_distribution[resource] -= 1
            if numbers:
                center.number = numbers.pop()

    return centers
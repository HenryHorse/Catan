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

    def build_settlement(self, settlement):
        # can only build settlement if unbuilt settlements > 0
        self.unbuilt_settlements -= 1
        self.settlements.append(settlement)
        self.victory_points += 1

    def build_city(self, city):
        # can only build city if unbuilt cities > 0
        self.unbuilt_cities -= 1
        self.cities.append(city)
        self.victory_points += 2

    def build_road(self, road):
        self.unbuilt_roads -= 1
        self.roads.append(road)

    def get_victory_points(self):
        return self.victory_points
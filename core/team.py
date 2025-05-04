class Team:
    def __init__(self, name, players):
        self.name = name            # "red" or "blue"
        self.players = players      # List of Player objects

    def draw(self, screen):
        for player in self.players:
            player.draw(screen)

    def reset_positions(self, positions):
        # positions: list of (x, y) tuples
        for player, pos in zip(self.players, positions):
            player.x, player.y = pos

    def handle_inputs(self, keys, controllers, ball):
        for controller in controllers:
            controller.handle_input(keys, ball)

    def get_all_positions(self):
        return [(p.x, p.y) for p in self.players]

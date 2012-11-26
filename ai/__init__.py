class AI(object):
    def __init__(self, player, game, world, **kwargs):
        self.player = player
        self.game = game
        self.world = world
    
    def start(self):
        pass

    def end(self):
        pass

    def event(self, msg):
        pass

    def initial_placement(self, empty, remaining):
        raise NotImplementedError

    def reinforce(self, available):
        raise NotImplementedError
    
    def attack(self):
        raise NotImplementedError

    def freemove(self):
        return None

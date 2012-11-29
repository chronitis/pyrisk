class AI(object):
    _sim_cache = {}
    @classmethod
    def simulate(cls, n_atk, n_def, tests=1000):
        if (n_atk, n_def) in cls._sim_cache:
            return cls._sim_cache[(n_atk, n_def)]
        survive = []
        victory = 0
        for i in range(tests):
            a = n_atk
            d = n_def
            while a > 1 and d > 0:
                atk_dice = min(a - 1, 3)
                atk_roll = sorted([random.randint(1, 6) for i in range(atk_dice)], reverse=True)
                def_dice = min(d, 2)
                def_roll = sorted([random.randint(1, 6) for i in range(def_dice)], reverse=True)

                for aa, dd in zip(atk_roll, def_roll):
                    if aa > dd:
                        d -= 1
                    else:
                        a -= 1
            if d == 0:
                survive.append(a)
                victory += 1
        
        cls._sim_cache[(n_atk, n_def)] = (victory / tests, 
                                          (sum(survive) / victory) if victory else 0)
        return cls._sim_cache[(n_atk, n_def)]
            

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

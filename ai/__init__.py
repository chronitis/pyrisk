import random

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
        """
        Initial placement phase. Called repeatedly until initial forces are exhausted.
        Claimed territories may only be reinforced once all empty territories are claimed.
    
        `empty` is a list of unclaimed territory names, or None if all have been claimed.
        `remaining` is the number of pieces the player has left to place.

        Return a territory name, which must be in `empty` if it is not None.
        """
        raise NotImplementedError

    def reinforce(self, available):
        """
        Reinforcement stage at the start of the turn.

        `available` is the number of pieces available.

        Return a dictionary of territory name -> count, which should sum to `available`.
        """
        raise NotImplementedError
    
    def attack(self):
        """
        Combat stage of a turn.

        Return or yield a sequence of (src, dest, atk_strategy, move_strategy) tuples.

        `src` and `dest` must be territory names.
        `atk_strategy` should be a function f(n_atk, n_def) which returns True to
        continue attacking, or None to use the default (victory or death) strategy.
        `move_strategy` should be a function f(n_atk) which returns the number
        of forces to move, or None to use the default (move maximum) behaviour.
        """
        raise NotImplementedError

    def freemove(self):
        """
        Free movement section of the turn.

        Return a single tuple (src, dest, count) where `src` and `dest` are territory 
        names, or None to skip this part of the turn.
        """
        return None

import random
import logging

class AI(object):
    """
    Base class for AIs to inherit from, containing some utility methods
    """
    _sim_cache = {}
    @classmethod
    def simulate(cls, n_atk, n_def, tests=1000):
        """
        Simulates the outcome of a battle with `n_atk` attackers and `n_def`
        defenders. The battle is simulated `tests` times, and the result cached
        and shared between all AI instances.
        
        Returns a tuple (probability_of_victory,
                         avg_surviving_attackers,
                         avg_surviving_defenders)
        """
        if (n_atk, n_def) in cls._sim_cache:
            return cls._sim_cache[(n_atk, n_def)]
        a_survive = []
        d_survive = []
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
                a_survive.append(a)
                victory += 1
            else:
                d_survive.append(d)
        
        cls._sim_cache[(n_atk, n_def)] = (float(victory) / tests, 
                                          (float(sum(a_survive)) / victory) if victory else 0,
                                          (float(sum(d_survive)) / (tests - victory)) if tests - victory else 0)
        return cls._sim_cache[(n_atk, n_def)]
            

    def __init__(self, player, game, world, **kwargs):
        """
        Initialise the AI class. Don't override this, rather instead use the
        start() method to do any setup which you require.
        Note that the `player`, `game` and `world` objects are unproxied, direct
        pointers to the real game structures. They could be proxied or copied
        each turn, or we could behave.
        """
        self.player = player
        self.game = game
        self.world = world
        self.logger = logging.getLogger("pyrisk.ai.%s" % self.__class__.__name__)
    
    def loginfo(self, msg, *args):
        """
        Logging methods. These messages will appear at the bottom of the screen
        when in curses mode, on screen in console mode or in a logfile if you
        specify that at the command line. 
        """
        self.logger.info(msg, *args)
        
    def logwarn(self, msg, *args):
        """As loginfo, but slightly more emphasis."""
        self.logger.warn(msg, *args)
        
    def logerror(self, msg, *args):
        """As loginfo, but will cause curses mode to pause for longer over this message."""
        self.logger.error(msg, *args)
    
    def start(self):
        """
        This method is called when the game starts. Implement it if you want
        to open resources, create data structures, etc.
        """
        pass

    def end(self):
        """
        This method is called after the game has ended. Implement it if you want
        to save to file, output postmortem information, etc.
        """
        pass

    def event(self, msg):
        """
        This method is called every time a game event occurs. `msg` will be a tuple
        containing a string followed by a set of arguments, look in game.py to see
        the types of messages that can be generated.
        
        Implement it if you want to know what is happening during other player's
        turns, etc.
        """
        pass

    def initial_placement(self, empty, remaining):
        """
        Initial placement phase. Called repeatedly until initial forces are exhausted.
        Claimed territories may only be reinforced once all empty territories are claimed.
    
        `empty` is a list of unclaimed territory objects, or None if all have been claimed.
        `remaining` is the number of pieces the player has left to place.

        Return a territory object or name, which must be in `empty` if it is not None.
        """
        raise NotImplementedError

    def reinforce(self, available):
        """
        Reinforcement stage at the start of the turn.

        `available` is the number of pieces available.

        Return a dictionary of territory object or name -> count, which should sum to `available`.
        """
        raise NotImplementedError
    
    def attack(self):
        """
        Combat stage of a turn.

        Return or yield a sequence of (src, dest, atk_strategy, move_strategy) tuples.

        `src` and `dest` must be territory objects or names.
        `atk_strategy` should be a function f(n_atk, n_def) which returns True to
        continue attacking, or None to use the default (attack until exhausted) strategy.
        `move_strategy` should be a function f(n_atk) which returns the number
        of forces to move, or None to use the default (move maximum) behaviour.
        """
        raise NotImplementedError

    def freemove(self):
        """
        Free movement section of the turn.

        Return a single tuple (src, dest, count) where `src` and `dest` are territory 
        objects or names, or None to skip this part of the turn.
        """
        return None

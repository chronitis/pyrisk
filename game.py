from display import Display, CursesDisplay
from player import Player
from territory import World
from world import CONNECT, AREAS, MAP, KEY
import logging
LOG = logging.getLogger("pyrisk")
import random



class Game(object):
    """
    This class represents an individual game, and contains the main game logic.
    """
    defaults = {
        "curses": True, #whether to use ncurses for map display
        "color": True, #whether to use color with ncurses
        "delay": 0.1, #seconds to sleep after each (ncurses) display update
        "connect": CONNECT, #the territory connection graph (see world.py)
        "areas": AREAS, #the territory->continent mapping, and values
        "cmap": MAP, #the ASCII art map to use
        "ckey": KEY, #the territority->char mapping key for the map
        "screen": None, #a curses.window (for use with the curses.wrapper function)
        "round": None, #the round number
        "wait": False, #whether to pause and wait for a keypress after each event
        "history": {}, #the win/loss history for each player, for multiple rounds
        "deal": False #deal out territories rather than let players choose
    }
    def __init__(self, **options):
        self.options = self.defaults.copy()
        self.options.update(options)

        self.world = World()
        self.world.load(self.options['areas'], self.options['connect'])

        self.players = {}

        self.turn = 0
        self.turn_order = []

        if self.options['curses']:
            self.display = CursesDisplay(self.options['screen'], self,
                                         self.options['cmap'], self.options['ckey'],
                                         self.options['color'], self.options['wait'])
        else:
            self.display = Display()


    def add_player(self, name, ai_class, **ai_kwargs):
        assert name not in self.players
        player = Player(name, self, ai_class, ai_kwargs)
        self.players[name] = player

    @property
    def player(self):
        """Property that returns the correct player object for this turn."""
        return self.players[self.turn_order[self.turn % len(self.players)]]

    def aiwarn(self, *args):
        """Generate a warning message when an AI player tries to break the rules."""
        logging.getLogger("pyrisk.player.%s" % self.player.ai.__class__.__name__).warn(*args)

    def event(self, msg, territory=None, player=None):
        """
        Record any game action.
        `msg` is a tuple describing what happened.
        `territory` is a list of territory objects to be highlighted, if any
        `player` is a list of player names to be highlighted, if any
        
        Calling this method triggers the display to be updated, and any AI
        players that have implemented event() to be notified.
        """
        
        self.display.update(msg, territory=territory, player=player)
        
        LOG.info([str(m) for m in msg])
        for p in self.players.values():
            p.ai.event(msg)
        
    def play(self):
        assert 2 <= len(self.players) <= 5
        self.turn_order = list(self.players)
        random.shuffle(self.turn_order)
        for i, name in enumerate(self.turn_order):
            self.players[name].color = i + 1
            self.players[name].ord = ord('\/-|+*'[i])
            self.players[name].ai.start()
        self.event(("start", ))
        live_players = len(self.players)
        self.initial_placement()
        
        while live_players > 1:
            if self.player.alive:
                choices = self.player.ai.reinforce(self.player.reinforcements)
                assert sum(choices.values()) == self.player.reinforcements
                for tt, ff in choices.items():
                    t = self.world.territory(tt)
                    f = int(ff)
                    if t is None:
                        self.aiwarn("reinforce invalid territory %s", tt)
                        continue
                    if t.owner != self.player:
                        self.aiwarn("reinforce unowned territory %s", t.name)
                        continue
                    if f < 0:
                        self.aiwarn("reinforce invalid count %s", f)
                        continue
                    t.forces += f
                    self.event(("reinforce", self.player, t, f), territory=[t], player=[self.player.name])
                
                for src, target, attack, move in self.player.ai.attack():
                    st = self.world.territory(src)
                    tt = self.world.territory(target)
                    if st is None:
                        self.aiwarn("attack invalid src %s", src)
                        continue
                    if tt is None:
                        self.aiwarn("attack invalid target %s", target)
                        continue
                    if st.owner != self.player:
                        self.aiwarn("attack unowned src %s", st.name)
                        continue
                    if tt.owner == self.player:
                        self.aiwarn("attack owned target %s", tt.name)
                        continue
                    if tt not in st.connect:
                        self.aiwarn("attack unconnected %s %s", st.name, tt.name)
                        continue
                    initial_forces = (st.forces, tt.forces)
                    opponent = tt.owner
                    victory = self.combat(st, tt, attack, move)
                    final_forces = (st.forces, tt.forces)
                    self.event(("conquer" if victory else "defeat", self.player, opponent, st, tt, initial_forces, final_forces), territory=[st, tt], player=[self.player.name, tt.owner.name])
                freemove = self.player.ai.freemove()
                if freemove:
                    src, target, count = freemove
                    st = self.world.territory(src)
                    tt = self.world.territory(target)
                    f = int(count)
                    valid = True
                    if st is None:
                        self.aiwarn("freemove invalid src %s", src)
                        valid = False
                    if tt is None:
                        self.aiwarn("freemove invalid target %s", target)
                        valid = False
                    if st.owner != self.player:
                        self.aiwarn("freemove unowned src %s", st.name)
                        valid = False
                    if tt.owner != self.player:
                        self.aiwarn("freemove unowned target %s", tt.name)
                        valid = False
                    if not 0 <= f < st.forces:
                        self.aiwarn("freemove invalid count %s", f)
                        valid = False
                    if valid:
                        st.forces -= count
                        tt.forces += count
                        self.event(("move", self.player, st, tt, count), territory=[st, tt], player=[self.player.name])
                live_players = len([p for p in self.players.values() if p.alive])
            self.turn += 1
        winner = [p for p in self.players.values() if p.alive][0]
        self.event(("victory", winner), player=[self.player.name])
        for p in self.players.values():
            p.ai.end()
        return winner.name

    def combat(self, src, target, f_atk, f_move):
        n_atk = src.forces
        n_def = target.forces

        if f_atk is None:
            f_atk = lambda a, d: True
        if f_move is None:
            f_move = lambda a: a - 1

        while n_atk > 1 and n_def > 0 and f_atk(n_atk, n_def):
            atk_dice = min(n_atk - 1, 3)
            atk_roll = sorted([random.randint(1, 6) for i in range(atk_dice)], reverse=True)
            def_dice = min(n_def, 2)
            def_roll = sorted([random.randint(1, 6) for i in range(def_dice)], reverse=True)

            for a, d in zip(atk_roll, def_roll):
                if a > d:
                    n_def -= 1
                else:
                    n_atk -= 1
        
        if n_def == 0:
            move = f_move(n_atk)
            min_move = min(n_atk - 1, 3)
            max_move = n_atk - 1
            if move < min_move:
                self.aiwarn("combat invalid move request %s (%s-%s)", move, min_move, max_move)
                move = min_move
            if move > max_move:
                self.aiwarn("combat invalid move request %s (%s-%s)", move, min_move, max_move)
                move = max_move
            src.forces = n_atk - move
            target.forces = move
            target.owner = src.owner
            return True
        else:
            src.forces = n_atk
            target.forces = n_def
            return False

    def initial_placement(self):
        empty = list(self.world.territories.values())
        available = 35 - 2*len(self.players)
        remaining = {p: available for p in self.players}

        if self.options['deal']:
            random.shuffle(empty)
            while empty:
                t = empty.pop()
                t.forces += 1
                remaining[self.player.name] -= 1
                t.owner = self.player
                self.event(("deal", self.player, t), territory=[t], player=[self.player.name])
                self.turn += 1
        else:
            while empty:
                choice = self.player.ai.initial_placement(empty, remaining[self.player.name])
                t = self.world.territory(choice)
                if t is None:
                    self.aiwarn("invalid territory choice %s", choice)
                    self.turn += 1
                    continue
                if t not in empty:
                    self.aiwarn("initial invalid empty territory %s", t.name)
                    self.turn += 1
                    continue
                t.forces += 1
                t.owner = self.player
                remaining[self.player.name] -= 1
                empty.remove(t)
                self.event(("claim", self.player, t), territory=[t], player=[self.player.name])
                self.turn += 1
        
        while sum(remaining.values()) > 0:
            if remaining[self.player.name] > 0:
                choice = self.player.ai.initial_placement(None, remaining[self.player.name])
                t = self.world.territory(choice)
                if t is None:
                    self.aiwarn("initial invalid territory %s", choice)
                    self.turn += 1
                    continue
                if t.owner != self.player:
                    self.aiwarn("initial unowned territory %s", t.name)
                    self.turn += 1
                    continue
                t.forces += 1
                remaining[self.player.name] -= 1
                self.event(("reinforce", self.player, t, 1), territory=[t], player=[self.player.name])
                self.turn += 1


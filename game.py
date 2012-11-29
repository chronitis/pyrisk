from display import Display, CursesDisplay
from player import Player
from territory import Territory, Area, World
from world import CONNECT, AREAS, MAP, KEY
import logging
LOG = logging.getLogger("pyrisk")
import random
import collections


class Game(object):
    defaults = {
        "curses": True,
        "color": True,
        "delay": 0.1,
        "connect": CONNECT,
        "areas": AREAS,
        "cmap": MAP,
        "ckey": KEY,
        "screen": None,
        "round": None,
        "history": {}
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
                                         self.options['color'])
        else:
            self.display = Display()


    def add_player(self, name, ai_class, **ai_kwargs):
        assert name not in self.players
        player = Player(name, self, ai_class, ai_kwargs)
        self.players[name] = player

    @property
    def player(self):
        return self.players[self.turn_order[self.turn % len(self.players)]]

    def aiwarn(self, *args):
        logging.getLogger("pyrisk.ai.%s" % self.player.ai.__class__.__name__).warn(*args)

    def event(self, msg, territory=None, player=None):
        msg = [str(m) for m in msg]
        self.display.update(msg, territory=territory, player=player)
        LOG.info(msg)
        for p in self.players.values():
            p.ai.event(msg)
        
    def start(self):
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
                for t, f in choices.items():
                    if t not in self.world.territories:
                        self.aiwarn("reinforce invalid territory %s", t)
                        continue
                    if self.world.territories[t].owner != self.player:
                        self.aiwarn("reinforce unowned territory %s", t)
                        continue
                    if f < 0:
                        self.aiwarn("reinforce invalid count %s", f)
                        continue
                    self.world.territories[t].forces += f
                    self.event(("reinforce", self.player.name, t, f), territory=[t], player=[self.player.name])
                
                for src, target, attack, move in self.player.ai.attack():
                    if src not in self.world.territories:
                        self.aiwarn("attack invalid src %s", src)
                        continue
                    if target not in self.world.territories:
                        self.aiwarn("attack invalid target %s", target)
                        continue
                    if self.world.territories[src].owner != self.player:
                        self.aiwarn("attack unowned src %s", src)
                        continue
                    if self.world.territories[target].owner == self.player:
                        self.aiwarn("attack owned target %s", target)
                        continue
                    if self.world.territories[target] not in self.world.territories[src].connect:
                        self.aiwarn("attack unconnected %s %s", src, target)
                        continue
                    victory = self.combat(src, target, attack, move)
                    self.event(("conquer" if victory else "defeat", self.player.name, src, target), territory=[src, target], player=[self.player.name, self.world.territories[target].owner.name])
                freemove = self.player.ai.freemove()
                if freemove:
                    src, target, count = freemove
                    valid = True
                    if src not in self.world.territories:
                        self.aiwarn("freemove invalid src %s", src)
                        valid = False
                    if target not in self.world.territories:
                        self.aiwarn("freemove invalid target %s", target)
                        valid = False
                    if self.world.territories[src].owner != self.player:
                        self.aiwarn("freemove unowned src %s", src)
                        valid = False
                    if self.world.territories[target].owner != self.player:
                        self.aiwarn("freemove unowned target %s", target)
                        valid = False
                    if not 0 <= count < self.world.territories[src].forces:
                        self.aiwarn("freemove invalid count %s", count)
                        valid = False
                    if valid:
                        self.world.territories[src].forces -= count
                        self.world.territories[target].forces += count
                        self.event(("move", self.player.name, src, target, count), territory=[src, target], player=[self.player.name])
                live_players = len([p for p in self.players.values() if p.alive])
            self.turn += 1
        winner = [p for p in self.players.values() if p.alive][0]
        self.event(("victory", winner), player=[self.player.name])
        for p in self.players.values():
            p.ai.end()
        return winner.name

    def combat(self, src, target, f_atk, f_move):
        n_atk = self.world.territories[src].forces
        n_def = self.world.territories[target].forces

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
            self.world.territories[src].forces = n_atk - move
            self.world.territories[target].forces = move
            self.world.territories[target].owner = self.world.territories[src].owner
            return True
        else:
            self.world.territories[src].forces = n_atk
            self.world.territories[target].forces = n_def
            return False

    def initial_placement(self):
        empty = list(self.world.territories)
        available = 35 - 2*len(self.players)
        remaining = {p: available for p in self.players}

        while empty:
            choice = self.player.ai.initial_placement(empty, remaining[self.player.name])
            if choice not in empty:
                self.aiwarn("initial invalid empty territory %s", choice)
                turn += 1
                continue
            self.world.territories[choice].forces += 1
            self.world.territories[choice].owner = self.player
            remaining[self.player.name] -= 1
            empty.remove(choice)
            self.event(("claim", self.player.name, choice), territory=[choice], player=[self.player.name])
            self.turn += 1
        
        while sum(remaining.values()) > 0:
            if remaining[self.player.name] > 0:
                choice = self.player.ai.initial_placement(None, remaining[self.player.name])
                if choice not in self.world.territories:
                    self.aiwarn("initial invalid territory %s", choice)
                    self.turn += 1
                    continue
                if self.world.territories[choice].owner != self.player:
                    self.aiwarn("initial unowned territory %s", choice)
                    self.turn += 1
                    continue
                self.world.territories[choice].forces += 1
                remaining[self.player.name] -= 1
                self.event(("reinforce", self.player.name, choice, 1), territory=[choice], player=[self.player.name])
                self.turn += 1


#!/usr/bin/env python

import random
import copy
import sys
import curses
import logging
import collections
import time
from world import CONNECT, MAP, KEY, AREAS
logging.basicConfig()#filename="pyrisk.log", filemode="w")
LOG = logging.getLogger("pyrisk")
#LOG.setLevel(logging.DEBUG)

class Territory(object):
    def __init__(self, name, area):
        self.name = name
        self.area = area
        self.owner = None
        self.forces = 0
        self.connect = set()

    @property
    def border(self):
        for c in self.connect:
            if c.owner != self.owner:
                return True
        return False

    @property
    def ownarea(self):
        return self.owner == self.area.owner

    def __repr__(self):
        return "Territory(%s, %s, %s)" % (self.name, self.area.name if self.area else None, self.owner) 
        
class Area(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.territories = set()

    def __repr__(self):
        return "Area(%s, %s, %s)" % (self.name, self.value, self.territories)
    
    @property
    def owner(self):
        owners = set(t.owner for t in self.territories)
        if len(owners) == 1:
            return owners.pop()
        else:
            return None
        

class World(object):
    def __init__(self):
        self.territories = {}
        self.areas = {}

    def load(self, areas, connections):
        for name, (value, territories) in areas.items():
            LOG.debug("Creating area=%s", name)
            area = Area(name, value)
            self.areas[name] = area
            for t in territories:
                LOG.debug("Creating territory=%s", t)
                territory = Territory(t, area)
                area.territories.add(territory)
                self.territories[t] = territory
        for line in filter(lambda l: l.strip(), connections.split('\n')):
            joins = [t.strip() for t in line.split('--')]
            for i in range(len(joins) - 1):
                t0 = self.territories[joins[i]]
                t1 = self.territories[joins[i+1]]
                t0.connect.add(t1)
                t1.connect.add(t0)
            

class Player(object):
    def __init__(self, name, game, ai_class, ai_kwargs):
        self.name = name
        self.color = 0
        self.ord = 32
        self.ai = ai_class(self, game, game.world, **ai_kwargs)
        self.game = game

    @property
    def territories(self):
        for t in self.game.world.territories.values():
            if t.owner == self:
                yield t

    @property
    def territory_count(self):
        count = 0
        for t in self.game.world.territories.values():
            if t.owner == self:
                count += 1
        return count

    @property
    def areas(self):
        for a in self.game.world.areas.values():
            if a.owner == self:
                yield a

    @property    
    def forces(self):
        return sum(t.forces for t in self.territories)

    @property
    def alive(self):
        return self.territory_count > 0

    @property
    def reinforcements(self):
        return max(self.territory_count//3, 3) + sum(a.value for a in self.areas)

class Display(object):
    def update(self, msg, player=None, territory=None):
        LOG.info(msg)

class CursesDisplay(Display):
    EMPTY = ord(' ')
    UNCLAIMED = ord(':')
    ix = 80
    iy = 8
    def __init__(self, screen, game, cmap, ckey, color):
        self.screen = screen
        self.game = game
        self.t_coords = collections.defaultdict(list)
        self.t_centre = {}

        self.wx = 0
        self.wy = 0
        for j, line in enumerate(cmap.strip(' \n').split('\n')):
            self.wy += 1
            self.wx = max(self.wx, len(line))
            for i, char in enumerate(line):
                if char in ckey:
                    self.t_coords[ckey[char]] += [(i, j)]

        for t, ijs in self.t_coords.items():
            sum_i = sum(i[0] for i in ijs)
            sum_j = sum(i[1] for i in ijs)
            self.t_centre[t] = (sum_j//len(ijs), sum_i//len(ijs))
        
        self.sy, self.sx = self.screen.getmaxyx()    
        curses.noecho()
        if color:
            for i in range(1, 8):
                curses.init_pair(i, i, curses.COLOR_BLACK)
        
        self.worldpad = curses.newpad(self.wy, self.wx)
        self.infopad = curses.newpad(self.iy, self.ix)    
            
    def update(self, msg, territory=None, player=None):
        if not territory:
            territory = []  
        if not player:
            player = []
        self.worldpad.clear()
        for name, t in self.game.world.territories.items():
            if t.owner:
                attrs = curses.color_pair(t.owner.color)
                char = t.owner.ord
            else:
                attrs = curses.COLOR_WHITE
                char = self.UNCLAIMED
            if name in territory:
                attrs |= curses.A_BOLD
            for i, j in self.t_coords[name]:
                self.worldpad.addch(j, i, char, attrs)
            if t.owner:
                self.worldpad.addstr(self.t_centre[name][0], 
                                     self.t_centre[name][1], 
                                     str(t.forces), attrs)

        self.infopad.clear()
        self.infopad.addstr(0, 0, 
                            "TURN " + str(self.game.turn//len(self.game.players)) + ": " + " ".join(msg), 
                            curses.COLOR_WHITE | curses.A_BOLD)
        self.infopad.addstr(2, 0, 
                            "NAME        TERR    FORCES  +FORCES AREA", 
                            curses.COLOR_WHITE | curses.A_BOLD)
        for i, name in enumerate(self.game.turn_order):
            p = self.game.players[name]
            attrs = curses.color_pair(p.color)
            if name in player:
                attrs |= curses.A_BOLD
            if not p.alive:
                attrs |= curses.A_DIM
            self.infopad.addstr(3+i, 0, p.name.ljust(12)[:12]+str(p.territory_count).ljust(8)[:8]+str(p.forces).ljust(8)[:8]+str(p.reinforcements).ljust(8)[:8]+" ".join(a.name for a in p.areas), attrs)

        self.worldpad.overwrite(self.screen, 0, 0, 1, 0, 
                                min(self.sy, self.wy), min(self.sx, self.wx-1))
        self.infopad.overwrite(self.screen, 0, 0, min(self.wy+2, self.sy), 0, 
                               min(self.sy, self.wy + self.iy+1), min(self.ix-1, self.sx))
        self.screen.refresh()
        time.sleep(0.1)
          
class Game(object):
    defaults = {
        "curses": True,
        "color": True,
        "delay": 0,
        "connect": CONNECT,
        "areas": AREAS,
        "cmap": MAP,
        "ckey": KEY,
        "attack_dice": 3,
        "defense_dice": 2,
        "screen": None
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
        return winner

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

     

if __name__ == '__main__':
    from ai.random_ai import RandomAI
    from ai.better_ai import BetterAI
    def wrapper(stdscr, *args, **kwargs):
        g = Game(screen=stdscr, **kwargs)
        for i in range(4):
            g.add_player(["ALPHA", "BETA", "GAMMA", "DELTA"][i], BetterAI)
        g.start()
    curses.wrapper(wrapper)
    


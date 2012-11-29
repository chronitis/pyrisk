import collections
import logging
LOG = logging.getLogger("pyrisk")
import curses
import time

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
        info = "TURN " + str(self.game.turn//len(self.game.players)) + ": " + " ".join(msg)
        if self.game.options['round']:
            info = ("ROUND %d/%d " % self.game.options['round']) + info
        self.infopad.addstr(0, 0, info, curses.COLOR_WHITE | curses.A_BOLD)
        self.infopad.addstr(2, 0, 
                            "NAME    AI      WINS    TERR    FORCES  +FORCES AREA", 
                            curses.COLOR_WHITE | curses.A_BOLD)
        for i, name in enumerate(self.game.turn_order):
            p = self.game.players[name]
            attrs = curses.color_pair(p.color)
            if name in player:
                attrs |= curses.A_BOLD
            if not p.alive:
                attrs |= curses.A_DIM
            info = [p.name, p.ai.__class__.__name__[:-2], 
                    str(self.game.options['history'].get(p.name, 0)), 
                    str(p.territory_count), str(p.forces), 
                    str(p.reinforcements)]
            info = "".join(s.ljust(8)[:8] for s in info) + " ".join(a.name for a in p.areas)
            self.infopad.addstr(3+i, 0, info, attrs)

        self.worldpad.overwrite(self.screen, 0, 0, 1, 0, 
                                min(self.sy, self.wy), min(self.sx, self.wx-1))
        self.infopad.overwrite(self.screen, 0, 0, min(self.wy+2, self.sy), 0, 
                               min(self.sy, self.wy + self.iy+1), min(self.ix-1, self.sx))
        self.screen.refresh()
        time.sleep(self.game.options['delay'])

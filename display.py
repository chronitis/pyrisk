import collections
import logging
LOG = logging.getLogger("pyrisk")
import curses
import time

class LogQueue(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self, level=logging.DEBUG)
        self.queue = []
    def emit(self, record):
        self.queue.append(record)

class Display(object):
    def update(self, msg, player=None, territory=None):
        pass

class CursesDisplay(Display):
    EMPTY = ord(' ')
    UNCLAIMED = ord(':')
    ix = 80
    iy = 20
    def __init__(self, screen, game, cmap, ckey, color, wait):
        self.screen = screen
        self.game = game
        self.t_coords = collections.defaultdict(list)
        self.t_centre = {}
        self.color = color
        self.wait = wait
        self.logqueue = LogQueue()
        LOG.addHandler(self.logqueue)

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
        if self.color:
            for i in range(1, 8):
                curses.init_pair(i, i, curses.COLOR_BLACK)
        
        self.worldpad = curses.newpad(self.wy, self.wx)
        self.infopad = curses.newpad(self.iy, self.ix)    

    def format(self, msg):
        if msg[0] == 'start':
            return "Game begins"
        elif msg[0] == 'victory':
            return "Victory to %s" % msg[1].name
        elif msg[0] == 'reinforce':
            _, player, t, f = msg
            return "%s reinforces %s with %d (total %d)" % (player.name, t.name, f, t.forces)
        elif msg[0] == 'conquer':
            _, player, oppfor, st, tt, init, final = msg
            return "%s conquers %s in %s from %s (lost %da, %dd)" % (player.name, oppfor.name, tt.name, st.name, init[0]-final[0]-final[1], init[1])
        elif msg[0] == 'defeat':
            _, player, oppfor, st, tt, init, final = msg
            return "%s defeated by %s in %s from %s (lost %da, %dd)" % (player.name, oppfor.name, tt.name, st.name, init[0]-final[0], init[1]-final[1])
        elif msg[0] == 'move':
            _, player, st, tt, f = msg
            return "%s moves %d from %s to %s (total %d)" % (player.name, f, st.name, tt.name, tt.forces)
        elif msg[0] == 'claim':
            _, player, t = msg
            return "%s claims %s" % (player.name, t.name)
        elif msg[0] == 'deal':
            _, player, t = msg
            return "%s dealt %s" % (player.name, t.name)
        else:
            raise
            
    def update(self, msg, territory=None, player=None, extra=None, modal=False):
        if not territory:
            territory = []  
        if not player:
            player = []
        self.worldpad.clear()
        for name, t in self.game.world.territories.items():
            if t.owner:
                attrs = curses.color_pair(t.owner.color)
                if self.color:
                    char = t.ord
                else:
                    char = t.owner.ord
            else:
                attrs = curses.COLOR_WHITE
                if self.color:
                    char = t.ord
                else:
                    char = self.UNCLAIMED
            if t in territory:
                attrs |= curses.A_BOLD
            for i, j in self.t_coords[name]:
                self.worldpad.addch(j, i, char, attrs)
            if t.owner:
                self.worldpad.addstr(self.t_centre[name][0], 
                                     self.t_centre[name][1], 
                                     str(t.forces), attrs)

        self.infopad.clear()
        info = "TURN " + str(self.game.turn//len(self.game.players)) + ": " + self.format(msg)
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

        logline = len(self.game.turn_order) + 4
        for i, record in enumerate(self.logqueue.queue):
            self.infopad.addstr(logline+i, 0, record.getMessage()[:self.ix-1], curses.A_NORMAL)
            if logline + i == self.iy - 2 and i < len(self.logqueue.queue) - 1:
                self.infopad.addstr(logline+i+1, 0, "(%d more suppressed)" % (len(self.logqueue.queue) - i), curses.A_NORMAL)
                break
        
        delay = self.game.options['delay']
        if any(r.levelno > logging.WARN for r in self.logqueue.queue):
            delay *= 5
                
        self.logqueue.queue = []
        

        self.worldpad.overwrite(self.screen, 0, 0, 1, 1, 
                                min(self.sy-1, self.wy), min(self.sx-1, self.wx-1))
        self.infopad.overwrite(self.screen, 0, 0, min(self.wy+2, self.sy-1), 0, 
                               min(self.sy-1, self.wy + self.iy+1), min(self.ix-1, self.sx-1))
        self.screen.refresh()
        if self.wait or modal:
            self.screen.getch()
        else:
            time.sleep(delay)

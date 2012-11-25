#!/usr/bin/env python

import random
import copy
import sys
import curses
import logging
logging.basicConfig()
LOG = logging.getLogger("pyrisk")

class Territory(object):
    def __init__(self, name, area):
        self.name = name
        self.area = area
        self.owner = None
        self.forces = 0
        self.connect = {}

    def __repr__(self):
        return "Territory(%s, %s, %s)" % (self.name, self.area.name if self.area else None, self.owner) 
        
class Area(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.territories = {}

    def __repr__(self):
        return "Area(%s, %s, %s)" % (self.name, self.value, list(self.territories.values()))
    
    @property
    def owner(self):
        owners = set(t.owner for t in self.territories)
        if len(owners) == 1:
            return owners[0]
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
                area.territories[t] = territory
                self.territories[t] = territory
        for line in filter(lambda l: l.strip(), connections.split('\n')):
            joins = [t.strip() for t in line.split('--')]
            for i in range(len(joins) - 1):
                t0 = self.territories[joins[i]]
                t1 = self.territories[joins[i+1]]
                t0.connect[t1.name] = t1
                t1.connect[t0.name] = t0
            

class Player(object):
    def __init__(self):
        self.name = name
        self.color = color
        self.ord = 0
        self.ai = None
        self.world = world

    @property
    def territories(self):
        for t in self.world.territories.values():
            if t.owner == self:
                yield t

    @property
    def areas(self):
        for a in self.world.areas.values():
            if a.owner == self:
                yield a

    @property    
    def forces(self):
        return sum(t.forces for t in self.territories)

    @property
    def alive(self):
        return len(self.territories)

    @property
    def reinforcements(self):
        return max(len(self.territories)/3, 3) + sum(a.value for a in self.areas)

class Display(object):
    def update(self, event):
        LOG.info(event)

class CursesDisplay(Display):
    def __init__(self, screen, game, cmap, ckey):
        self.screen = screen
        self.game = game
        self.t_coords = {t: [] for t in ckey}
        self.t_centre = {}
        for i, line in enumerate(cmap.split('\n')):
            for j, char in enumerate(line):
                if char in ckey:
                    self.t_coords[ckey[char]] += [(i, j)]
        for t, ijs in self.t_coords.items():
            sum_i = sum(i[0] for i in ijs)
            sum_j = sum(i[1] for i in ijs)
            self.t_centre[t] = (sum_i/len(ijs), sum_j/len(ijs))
            
    def update(self, event):
        pass
        
                
                    

class Game(object):
    defaults = {
        "curses": True,
        "color": True,
        "delay": 0,
        "connect": CONNECT,
        "areas": AREAS
        "cmap": MAP,
        "ckey": KEY,
        "attack_dice": 3,
        "defense_dice": 2,
        "screen": None
    }
    def __init__(self, **options):
        self.options = defaults.copy()
        self.options.update(options)

        self.world = World()
        self.world.load(self.options['areas'], self.options['connect'])

        self.players = {}

        self.turn = 0
        self.turn_order = []

        if self.options['curses']:
            self.display = CursesDisplay(self.options['screen'], self,
                                         self.options['cmap'], self.options['ckey'])
        else:
            self.display = Display


    @property
    def player:
        return self.players[self.turn_order[self.turn % len(self.players)]]

    def event(self, e, *args):
        self.display.update((e, *args))
        LOG.info((e, *args))
        
    def start(self):
        self.event("start")
        self.turn_order = random.shuffle(self.players.keys())
        live_players = len(self.players)
        self.initial_placement(turn_order)
        
        while live_players > 1:
            if self.player.alive:
                choices = self.player.ai.reinforce(self.player.reinforcements)
                assert sum(choices.values()) == self.player.reinforcements
                for t, f in choices.items():
                    assert t in self.world.territories
                    assert self.world.territories[t].owner == self.player
                    assert f >= 0
                    self.world.territories[t].forces += f
                    self.event("reinforce", self.player.name, t, f)
                
                for src, target, attack, move in self.player.ai.attack():
                    assert src in self.world.territories
                    assert target in self.world.territories
                    assert self.world.territories[src].owner == self.player
                    assert self.world.territories[target].owner != self.player
                    victory = self.combat(src, target, attack, move)
                    self.event("conquer" if victory else "defeat", self.player.name, src, target)
                freemove = self.player.ai.freemove()
                if freemove:
                    src, target, count = freemove
                    assert src in self.world.territories
                    assert target in self.world.territories
                    assert self.world.territories[src].owner == self.player
                    assert self.world.territories[target].owner == self.player
                    assert 0 < count < self.world.territories[src].forces
                    self.world.territories[src].forces -= count
                    self.world.territories[target].forces += count
                    self.event("move", self.player.name, src, target, count)
                live_players = len([p for p in self.players.values() if p.alive])
            self.turn += 1
        winner = [p for p in self.players.values() if p.alive][0]
        self.event("victory", winner)
        return winner

    def combat(self, src, target, f_atk, f_move):
        n_atk = self.territories[src].forces
        n_def = self.territories[target].forces

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
            assert min(n_atk - 1, 3) =< move < n_atk
            self.world.territories[src].forces = n_atk - move
            self.world.territories[target].forces = move
            self.world.territories[target].owner = self.world.territories[src].owner
            return True
        else:
            self.world.territories[src].forces = n_atk
            self.world.territories[target].forces = n_def
            return False

    def initial_placement(self):
        empty = self.world.territories.keys()
        available = 35 - 2*len(self.players)
        remaining = {p.name: available for p in self.players}

        while empty:
            choice = self.player.ai.initial_placement(empty, remaining[self.player.name])
            assert choice in empty
            self.world.territories[choice].forces += 1
            self.world.territories[choice].owner = self.player
            remaining[self.player.name] -= 1
            empty.remove(choice)
            self.event("claim", self.player.name, choice)
            self.turn += 1
        
        while sum(remaining.values()) > 0:
            if remaining[self.player.name] > 0:
                choice = self.player.ai.initial_placement(None, remaining[self.player.name])
                assert choice in self.world.territories
                assert self.world.territories[choice].owner == self.player
                self.world.territories[choice].forces += 1
                remaining[self.player.name] -= 1
                self.event("reinforce", self.player.name, choice, 1)
                self.turn += 1


class Game(object):
  def __init__(self,**kwargs):
    self.players = {}
    self.ai = {}
    self.areas = {}
    self.territories = {}
    self.enable_dot = False
    self.enable_curses = False
    if 'map' in kwargs:
      self.parse(kwargs['map'])
    s = ('stdout' in kwargs and kwargs['stdout'])
    l = ('logfile' in kwargs and kwargs['logfile'])
    if s and l:
      self.output = MultiOut(sys.stdout,open(kwargs['logfile'],'w'))
    elif s and not l:
      self.output = sys.stdout
    elif l and not s:
      self.output = open(kwargs['logfile'],'w')
    else:
      self.output = NullOut()
    
    
    self.enable_dot = kwargs.get('dot',False)
    self.prefix = kwargs.get('dot_prefix','')
      
    self.enable_curses = kwargs.get('curses',False)
    self.allow_curses_colors = kwargs.get('curses_colors',False)
    if self.enable_curses:
      self.curses(kwargs['cursemap'],kwargs['cursekey'])
     
    self.player_history = kwargs.get('player_history',{})
    
    self.turn_counter = 0
    self.last_action = None
    self.current_player = None
    
    self.pause = kwargs.get('pause',False)
    
  def addTerritory(self,name,polygon):
    self.territories[name] = Territory(name,polygon)
  def addArea(self,name,value,territories):
    self.areas[name] = Area(name,value,territories)
  def addConnection(self,a,b):
    ta = self.territories[a]
    tb = self.territories[b]
    if not b in ta.adjacent:
        ta.adjacent.append(b)
    if not a in tb.adjacent:
        tb.adjacent.append(a)
  def parse(self,text):
    for line in text.strip().split('\n'):
      line = line.strip()
      if len(line)>0 and line[0]!=' ':
        if line[0]=='[':
          name = line[1:].split(']')[0].split(',')[0]
          value = int(line[1:].split(']')[0].split(',')[1])
          territories = line.split(']')[1].split(',')
          if all([t in self.territories for t in territories]):
            self.addArea(name,value,territories)
          for territory in territories:
            self.territories[territory].area = name
        else:
          names = line.split('--')
          for name in names:
            if not name in self.territories:
              self.addTerritory(name,None)
          for i in range(len(names)-1):
            self.addConnection(names[i],names[i+1])
  def curses(self,cursemap,cursekey):
    self.enable_curses = True
    
    for t in self.territories.values():
      t.curse_coords = []
    
    self.curse_map_lines = len(cursemap.split('\n'))
    for y,line in enumerate(cursemap.split('\n')):
      for x,char in enumerate(line):
        if char in cursekey:
          self.territories[cursekey[char]].curse_coords.append((y,x))
    
    for t in self.territories.values():
      n = len(t.curse_coords)
      sum_y = sum([cc[0] for cc in t.curse_coords])
      sum_x = sum([cc[1] for cc in t.curse_coords])
      t.curse_centre = (int(sum_y/float(n)),int(sum_x/float(n)))
    
    self.screen = curses.initscr()
    self.curses_color = False
    if self.allow_curses_colors:
      curses.start_color()
      self.curses_color = curses.has_colors()
    self.cursepad = curses.newpad(50,100)
    
    
  def update_curses(self):
    self.cursepad.clear()
    for p in self.players.values():
      for nt in p.territories:
        t = self.territories[nt]
        for (y,x) in t.curse_coords:
          if self.curses_color:
            self.cursepad.addch(y,x,32,curses.color_pair(p.curses_color))
          else:
            self.cursepad.addch(y,x,p.curses_char)
        if self.curses_color:
          self.cursepad.addstr(t.curse_centre[0],t.curse_centre[1],str(t.forces),curses.color_pair(p.curses_color) | curses.A_BOLD)
        else:
          self.cursepad.addstr(t.curse_centre[0],t.curse_centre[1],str(t.forces),curses.A_BOLD)
    self.cursepad.addstr(self.curse_map_lines,0,"Turn %s Current Player %s Action %s"%(self.turn_counter/len(self.players),self.current_player[:8].ljust(8),self.last_action))
    self.cursepad.addstr(self.curse_map_lines+1,0,"# PLAYER  WIN AI      TER FOR REI CON")
    for i, name in enumerate(self.order):
      player = self.players[name]
      if self.curses_color:
        self.cursepad.addch(i+2+self.curse_map_lines,0,32,curses.color_pair(player.curses_color))
        self.cursepad.addstr(i+2+self.curse_map_lines,2,player.name[:8].ljust(8),curses.color_pair(player.curses_color))
        self.cursepad.addstr(i+2+self.curse_map_lines,10,"%s%s%s%s%s%s"%(str(self.player_history.get(player.name,0)).ljust(4),self.ai[player.name].__class__.__name__[:8].ljust(8),str(len(player.territories))[:4].ljust(4),str(player.forces)[:4].ljust(4),str(player.reinforcements)[:4].ljust(4),' '.join(player.areas)))
      else:  
        self.cursepad.addstr(i+2+self.curse_map_lines,0,"%s %s%s%s%s%s%s%s"%(chr(player.curses_char),player.name[:8].ljust(8),str(self.player_history.get(player.name,0)).ljust(4),self.ai[player.name].__class__.__name__[:8].ljust(8),str(len(player.territories))[:4].ljust(4),str(player.forces)[:4].ljust(4),str(player.reinforcements)[:4].ljust(4),' '.join(player.areas)))
    
    maxyx = self.screen.getmaxyx()
    self.cursepad.refresh(0,0,0,0,maxyx[0]-1,maxyx[1]-1)
    
    if self.pause:
      curses.getch()
    
  def __del__(self):
    if self.enable_curses:
      curses.endwin()
      pass
  
  def addPlayer(self,name,ai,colour=None):
    if colour==None:
      colour = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    index = len(self.players)  
      
    self.players[name]=Player(name,colour)
    self.players[name].curses_color = (index+1)%8
    self.players[name].curses_char = ord('-|+@$:=*'[index])
    self.ai[name]=ai

  def toDot(self,savename,attacks=None,freemove=None):
    if not self.enable_dot:
      return
    result = "graph risk {\n"
    done = []
    for territory in self.territories:
      for adj in self.territories[territory].adjacent:
        if not adj in done:
          if self.territories[territory].area==self.territories[adj].area:
            result += '"%s" -- "%s" [len=0.5]\n'%(territory,adj)
          else:
            result += '"%s" -- "%s" [len=1]\n'%(territory,adj)
      done.append(territory)
      
    for i,area in enumerate(self.areas):
      result += 'subgraph cluster%s {\n'%i
      result += 'label="%s"\n'%area
      for territory in self.areas[area].territories:
        result += '"%s"\n'%territory
      result += '}\n'
    for territory in self.territories:
      if self.territories[territory].player:
        p = self.territories[territory].player
        c = self.players[self.territories[territory].player].colour
        n = self.territories[territory].forces
        result += '"%s" [shape=Mrecord,style=filled,color="#%02x%02x%02x",label="{%s|{%s|%s}}"]\n'%(territory,c[0],c[1],c[2],territory.replace(' ','\ '),p.replace(' ','\ '),n)
    for name,player in self.players.items():
      if player.alive:
        result += '"%s" [shape=Mrecord,style=filled,color="#%02x%02x%02x",label="{%s|{Terri|%s}|{Reinf|%s}|{Total|%s}|%s}"]\n'%(name,player.colour[0],player.colour[1],player.colour[2],name.replace(' ','\ '),len(player.territories),player.reinforcements,player.forces,'\\n'.join([a.replace(' ','\ ') for a in player.areas]))
    if not attacks==None:
      for (origin,target) in attacks:
        result += '"%s" -- "%s" [color=red,arrowType=normal,dir=forward,penwidth=4,arrowsize=4,len=3]\n'%(origin,target)
    if not freemove==None:
      result += '"%s" -- "%s" [color=blue,arrowType=normal,dir=forward,penwidth=4,arrowsize=4,label="%s",len=3]\n'%(freemove[0],freemove[1],freemove[2])
    result += 'overlap=false\n}\n'
    open(self.prefix+savename+'.dot','w').write(result)
  
  def updateState(self):
    for name,player in self.players.items():
      player.territories = []
      player.forces = 0
      player.areas = []
      player.reinforcements = 0
    for name,territory in self.territories.items():
      if territory.player:
        self.players[territory.player].territories.append(name)
        self.players[territory.player].forces += territory.forces
    for name,area in self.areas.items():
      area.player=None
      for pname,player in self.players.items():
        if all([t in player.territories for t in area.territories]):
          area.player=pname
          player.areas.append(name)
          player.reinforcements += area.value
    self.live_players = 0
    for name,player in self.players.items():
      if len(player.territories)>0:
        self.live_players += 1
        player.alive=True
      else:
        player.alive=False
      player.reinforcements += max(3,len(player.territories)/3)
    
    for name,ai in self.ai.items():
      ai.game_self.__dict__.update(copy.deepcopy(self.players[name].__dict__))
      for n,p in self.players.items():
        ai.game_players[n].__dict__.update(copy.deepcopy(p.__dict__))
      for n,a in self.areas.items():
        ai.game_areas[n].__dict__.update(copy.deepcopy(a.__dict__))
      for n,t in self.territories.items():
        ai.game_territories[n].__dict__.update(copy.deepcopy(t.__dict__))
    if self.enable_curses:
      self.update_curses()
     
  def startGame(self):
    self.order = self.players.keys()
    random.shuffle(self.order)
    print >>self.output, "Turn order:",self.order
    for name in self.order:
      self.ai[name].game_self = copy.deepcopy(self.players[name])
      self.ai[name].game_players = copy.deepcopy(self.players)
      self.ai[name].game_areas = copy.deepcopy(self.areas)
      self.ai[name].game_territories = copy.deepcopy(self.territories) 
      self.ai[name].prepare()
    self.placeForces(35 - (len(self.players)-2)*5)
    self.toDot('layout')
    return self.play()
    
  def placeForces(self,starting_forces):
    print >>self.output, "====Starting force placement===="
    empty_territories = self.territories.keys()
    while starting_forces>0:
      print >>self.output,"Start placement round, %s remain" % starting_forces
      for name in self.order:
        self.current_player = name
        if len(empty_territories)>0:
          choice = self.ai[name].placeForces(empty_territories,starting_forces)
          print >>self.output, "Player %s chooses %s (%s empty territories remain)" % (name,choice,len(empty_territories))
          if choice in empty_territories:
            self.territories[choice].player = name
            self.territories[choice].forces = 1
            self.last_action = "OCCUPY %s 1"%choice
            empty_territories.remove(choice)
          else:
            raise Exception, "Attempted to place units at an invalid location"
        else:
          choice = self.ai[name].placeForces(None,starting_forces)
          print >>self.output, "Player %s chooses %s" % (name,choice)
          if choice in self.territories and self.territories[choice].player==name:
            self.territories[choice].forces += 1
            self.last_action = "REINFORCE %s 1"%choice
          else:
            raise Exception, "Attempted to place units at an invalid location"  
          
        self.updateState()
      starting_forces -= 1
      
  def play(self):
    print >>self.output, "====Starting game===="
    self.turn_counter = 0
    while self.live_players>1:
      name = self.order[self.turn_counter%len(self.players)]
      prefix = '['+name+']'
      player = self.players[name]
      ai = self.ai[name]
      self.current_player=name
      if player.alive:
        print >>self.output, "==Turn: %s Player: %s Live Players: %s==" % (self.turn_counter/len(self.players),name,self.live_players)
        print >>self.output,prefix, "has %s territories, %s forces and controls %s" % (len(player.territories),player.forces,player.areas)
        reinforcements = player.reinforcements
        print >>self.output,prefix, "Available reinforcements:",reinforcements
        used_reinforcements = 0
        for (territory,count) in ai.placeReinforcements(reinforcements):
          ai.last_error = None
          print >>self.output,prefix, "Reinforcing %s with %s" % (territory,count)
          if territory in self.territories:
            if self.territories[territory].player==name:
              if count>0:
                if used_reinforcements+count <= reinforcements:
                  self.territories[territory].forces += count
                  self.last_action = "REINFORCE %s %s" % (territory,count)
                  used_reinforcements += count
                else:
                  print >>self.output,prefix,"ERROR Tried to place too many reinforcements (%s)"%count
                  ai.last_error = ('reinforce','too_many',count,reinforcements-used_reinforcements)
              else:                
                print >>self.output,prefix,"ERROR Tried to place 0 or negative reinforcements (%s)"%count
                ai.last_error = ('reinforce','invalid_number',count)
            else:
              print >>self.output,prefix,"ERROR Tried to reinforce enemy territory (%s)"%self.territories[territory]
              ai.last_error = ('reinforce','not_yours',territory)
          else:
            print >>self.output,prefix,"ERROR Tried to reinforce invalid territory (%s)"%territory
            ai.last_error = ('reinforce','territory_invalid',territory)
        self.updateState()
        attacks = []
        for (origin,target,attack_strategy) in ai.turnAttacks():
          ai.last_error = None
          if origin in self.territories:
            if self.territories[origin].player==name:
              if self.territories[origin].forces > 1:
                if target in self.territories:
                  if self.territories[target].player!=name:
                    print >>self.output,prefix, "Attacking %s (%s) from %s" % (target,self.territories[target].player,origin)
                    defense_strategy = self.ai[self.territories[target].player].defendTerritory
                    attacks.append((origin,target))
                    self.last_action = "ATTACK %s -> %s" % (origin,target)
                    self.handleCombat(origin,target,attack_strategy,defense_strategy)
                    self.updateState()
                  else:
                    print >>self.output,prefix, "ERROR Target territory (%s) is not enemy"%self.territories[target]
                    ai.last_error = ('attack','target_friendly',target)
                else:
                  print >>self.output,prefix, "ERROR Target territory (%s) is invalid"%self.territories[target]
                  ai.last_error = ('attack','target_invalid',target)
              else:
                print >>self.output,prefix, "ERROR Origin territory (%s) has insufficient forces"%self.territories[target]
                ai.last_error = ('attack','insufficient_forces',origin)
            else:
              print >>self.output,prefix, "ERROR Origin territory (%s) is enemy"%self.territories[target]
              ai.last_error = ('attack','not_yours',origin)
          else:
            print >>self.output,prefix, "ERROR Source territory (%s) is invalid"%self.territories[origin]
            ai.last_error = ('attack','origin_invalid',origin)
          
        freemove = ai.freeMove()
        if not freemove==None:
          src,dest,count = freemove
          print >>self.output,prefix, "Freemoving %s from %s to %s" % (count,src,dest)
          if src in self.territories:
            if self.territories[src].player==name:
              if dest in self.territories:
                if self.territories[dest].player==name:
                  if count>0:
                    if count<self.territories[src].forces:
                      self.territories[src].forces-=count
                      self.territories[dest].forces+=count
                      self.last_action="FREEMOVE %s -> %s %s"%(src,dest,count)
                    else:
                      print >>self.output,prefix,"ERROR Freemove more than available troops (%s/%s)"%(count,self.territories[src].forces-1)
                      ai.last_error = ('freemove','too_many',count,self.territories[src].forces-1)
                  else:
                    print >>self.output,prefix,"ERROR Freemove invalid number (%s)"%count
                    ai.last_error = ('freemove','invalid_number',count)  
                else:
                  print >>self.output,prefix,"ERROR Freemove target enemy (%s)"%src
                  ai.last_error = ('freemove','not_yours',dest)
              else:
                print >>self.output,prefix,"ERROR Freemove target invalid (%s)"%dest
                ai.last_error = ('freemove','target_invalid',dest)
            else:
              print >>self.output,prefix,"ERROR Freemove origin enemy (%s)"%src
              ai.last_error = ('freemove','not_yours',src)
          else:
            print >>self.output,prefix,"ERROR Freemove origin invalid (%s)"%src
            ai.last_error = ('freemove','origin_invalid',src)
        self.toDot('turn_%03d_%s'%(self.turn_counter,name),attacks,freemove)
      self.turn_counter += 1
    
    winner = None
    win_ai = None
    postmortem = {}
    for name,player in self.players.items():
      postmortem[name] = self.ai[name].finalise()
      if player.alive:
        winner = name
        win_ai = self.ai[name].__class__.__name__
      print >>self.output, name," has %s territories, %s forces and controls %s" % (len(player.territories),player.forces,player.areas)
    return {
      'winner':winner,
      'win_ai':win_ai,
      'turns':self.turn_counter,
      'postmortem':postmortem
    }
    
      
  def handleCombat(self,origin,target,attack_strategy,defense_strategy):    
    n_atk = self.territories[origin].forces
    n_def = self.territories[target].forces
    
    if attack_strategy==None:
      attack_strategy='always','max'
    
    cond,move = attack_strategy
    if isinstance(cond,str):
      if cond=='always':
        cond_fun = lambda a,d: True
      elif cond=='more':
        cond_fun = lambda a,d: a>d
      elif cond.startswith('min'):
        cond_min = int(cond[3:])
        cond_fun = lambda a,d: a>cond_min
      elif cond.startswith('ratio'):
        cond_ratio = float(cond[5:])
        cond_fun = lambda a,d: (float(a)/d)>cond_ratio
      elif cond.startswith('diff'):
        cond_diff = int(cond[4:])
        cond_fun = lambda a,d: (a-d)>=cond_diff
      else:
        cond_fun = lambda a,d: True
    else:
      cond_fun = cond
    if isinstance(move,str):
      if move=='max':
        move_fun = lambda a,d: a-1
      elif move=='half':
        move_fun = lambda a,d: max(3,a/2)
      elif move=='min':
        move_fun = lambda a,d: 3
      else:
        move_fun = lambda a,d: a-1
    elif isinstance(move,int):
      move_n = move
      move_fun = lambda a,d: move_n
    else:
      move_fun = move
      
    print >>self.output, "Starting combat %s vs %s"%(n_atk,n_def)
    atk_request = 0
    while n_atk>1 and n_def>0 and cond_fun(n_atk,n_def):
      #atk_request = min(attack_strategy(n_atk,n_def),n_atk-1)
      atk_request = min(move_fun(n_atk,n_def),n_atk-1)
      
      if atk_request>0:
        atk_dice = min(atk_request,3)
        atk_roll = sorted([random.randint(1,6) for i in range(atk_dice)],reverse=True)
        def_dice = max(min(defense_strategy(copy.copy(atk_roll),n_atk,n_def),2,n_def),1)
        def_roll = sorted([random.randint(1,6) for i in range(def_dice)],reverse=True)
        
        for a,d in zip(atk_roll,def_roll):
          if a>d:
            n_def -= 1
          else:
            n_atk -= 1
            atk_request -= 1
            
        print >>self.output, "%s vs %s, %s attackers, %s defenders"%(atk_roll,def_roll,n_atk,n_def)
      else:
        print >>self.output, "Attacker aborted combat"
        break
    if n_def==0:
      atk_request = max(atk_request,1)
      print >>self.output, "Attacker victorious, moving %s"%atk_request
      self.territories[origin].forces -= atk_request
      self.territories[target].forces = atk_request
      self.territories[target].player = self.territories[origin].player
    else:
      print >>self.output, "Defender victorious"
      self.territories[origin].forces = n_atk 
      self.territories[target].forces = n_def
    
class Area:
  def __init__(self,name,value,territories):
    self.name = name
    self.value = value
    self.territories = territories
    self.player = None
  def __str__(self):
    return '%s (%s)'%(self.name,self.value)
  
class Territory:
  def __init__(self,name,polygon):
    self.name = name
    self.polygon = polygon
    self.player = None
    self.forces = 0
    self.area = None
    self.adjacent = []
  def __str__(self):
    return '%s (%s,%s)'%(self.name,self.player,self.forces)
  
class Player:
  def __init__(self,name,colour):
    self.name = name
    self.colour = colour
    self.territories = []
    self.areas = []
    self.forces = 0
    self.reinforcements = 0
    self.alive = True
  def __str__(self):
    return '%s (t%s,f%s,r%s)'%(self.name,len(self.territories),self.forces,self.reinforcements)


class AIBase:
  #self.game_self
  #self.game_players
  #self.game_areas
  #self.game_territories
  #self.last_error
  def __str__(self):
    return '%s (%s)' % (self.game_self.name,self.__class__.__name__) 
  
  def prepare(self):
    pass
  def placeForces(self,empty_territories,starting_forces):
    #args (list_of_territory_names or None, remaining_starting_forces)
    #return "territory"
    raise NotImplemented
  def placeReinforcements(self,count):
    #args available_reinforcements
    #return or yield [(territory_name,count),...]
    raise NotImplemented
  def turnAttacks(self):
    #return or yield [(origin_name, target_name, strategy_callable(n_atk,n_def)),...]
    raise NotImplemented
  def freeMove(self):
    #return (src_name, dest_name, count) or None
    return None
  def defendTerritory(self,atk_roll,n_atk,n_def):
    #return defense_callable(atk_roll,n_atk,n_def)
    return 2
  def finalise(self):
    return None
  def __eq__(self,other):
    if hasattr(self,'game_self'):
      if other==self.game_self.name:
        return True
    return False
  def __ne__(self,other):
    if hasattr(self,'game_self'):
      if other!=self.game_self.name:
        return True
    return False
  
class NullOut:
  def write(self,data):
    pass
    
class MultiOut:
  def __init__(self,*args):
    self.out = args
  def write(self,data):
    for o in self.out:
      o.write(data)    

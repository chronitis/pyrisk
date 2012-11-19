from pyrisk import AIBase,NullOut
import random
import math
import copy
import cPickle
import os
import sys
  
def sim_round(na,nd):
  def defender_strategy(atkarray,natk,ndef):
    if len(atk_array)>=2:
      if atk_array[0]>=5 and atk_array[1]>=4:
        return 1
      return 2
    else:
      return 2

  while na>=2 and nd>=1:
    atk_d6 = 3
    atk_array = [random.randint(1,6) for i in range(atk_d6)]
    atk_array.sort()
    atk_array.reverse()
    
    def_ndie = defender_strategy(atk_array,na,nd)
    if not def_ndie in (1,2):
      def_ndie = 2
    
    def_d6 = min(nd,def_ndie)
    def_array = [random.randint(1,6) for i in range(def_d6)]
    def_array.sort()
    def_array.reverse()
    for a,d in zip(atk_array,def_array):
      if d>=a:
        if na>0:
          na-=1
      else:
        if nd>0:
          nd-=1
  return na>nd,na,nd

def run(natk,ndef,ntries=100):
  result = [sim_round(natk,ndef) for i in range(ntries)]
  atk_chance = float(len(filter(lambda x:x[0],result)))/ntries
  atk_survive = 0
  if atk_chance>0:
    atk_survive = float(sum([r[1] for r in result if r[0]]))/(atk_chance*ntries)
  def_survive = 0
  if atk_chance<1:
    def_survive = float(sum([r[2] for r in result if not r[0]]))/((1-atk_chance)*ntries)
  return (atk_chance,atk_survive,def_survive)



class ChronAI(AIBase):
  def finalise(self):
    if self.updated:
      f = open('chronai.pkl','w')
      cPickle.dump(self.chance_table,f)
      f.close()
    return None
  def __init__(self):
    self.output = NullOut()#sys.stdout
    self.updated = False
    if os.path.exists('chronai.pkl'):
      f = open('chronai.pkl')
      self.chance_table = cPickle.load(f)
      f.close()
    else:
      self.updated = True
      self.chance_table = {}
      for i in range(1,51):
        self.chance_table[i]={}
        for j in range(1,51):
          self.chance_table[i][j] = run(i,j)
  def chance(self,a,d):
    if a in self.chance_table:
      if d in self.chance_table[a]:
        return self.chance_table[a][d][0]
      else:
        self.updated = True
        self.chance_table[a][d]=run(a,d)
        return self.chance_table[a][d][0]
    else:
      self.updated = True
      self.chance_table[a]={d:run(a,d)}
      return self.chance_table[a][d][0]
      
  def update_territories(self):
    self.majority_areas = [a for n,a in self.game_areas.items() if float(len([t for t in self.game_self.territories if t in a.territories]))/len(a.territories)>=0.5]
    for n,t in self.game_territories.items():
      t.friendly_adjacent = []
      t.friendly_adjacent_forces = 0
      t.hostile_adjacent = []
      t.hostile_adjacent_forces = 0
      t.is_my_area = t.area in self.game_self.areas
      t.is_my_majority_area = t.area in self.majority_areas
      t.is_enemy_area = any([t.area in p.areas for n,p in self.game_players.items()])
      
      adj_players = set()
      for aa in t.adjacent:
        a = self.game_territories[aa]
        if a.player==self.game_self.name:
          t.friendly_adjacent += [aa]
          t.friendly_adjacent_forces += a.forces
        else:
          adj_players.add(a.player)
          t.hostile_adjacent += [aa]
          t.hostile_adjacent_forces += a.forces
      
      t.hostile_adjacent_reinforcements = 0
      for p in adj_players:
        t.hostile_adjacent_reinforcements += self.game_players[p].reinforcements
      
      t.isolated = len(t.friendly_adjacent)==0
      t.frontier = len(t.hostile_adjacent)>0  
  
  def update_areas(self):
    for n,a in self.game_areas.items():
      a.friendly_territories = [t for t in a.territories if self.game_territories[t].player==self.game_self.name]
      a.friendly_forces = sum([self.game_territories[t].forces for t in a.friendly_territories])
      a.hostile_territories = [t for t in a.territories if self.game_territories[t].player!=self.game_self.name]
      a.hostile_forces = sum([self.game_territories[t].forces for t in a.hostile_territories])
      a.territory_fraction = float(len(a.friendly_territories))/len(a.territories)
      a.force_fraction = float(a.friendly_forces)/(a.friendly_forces+a.hostile_forces)
      
          
  def gen_area_map(self):
    for n,a in self.game_areas.items():
      a.adjacent = set()
      a.borders = {}
    for n,t in self.game_territories.items():
      t.is_border = False
      for a in t.adjacent:
        if self.game_territories[a].area!=t.area:
          t.is_border = True
          self.game_areas[t.area].adjacent.add(self.game_territories[a].area)
          self.game_areas[t.area].borders[n]=self.game_territories[a].area
  
  def prepare(self):
    self.gen_area_map()
    first_choice = random.choice(self.game_areas.keys())
    second_choice = list(self.game_areas[first_choice].adjacent)
    third_choice = [k for k in self.game_areas.keys() if not (k==first_choice or k in second_choice)]
    random.shuffle(second_choice)
    random.shuffle(third_choice)
    self.area_priority = [first_choice]+second_choice+third_choice
    print >>self.output,  '!!DEBUG!!','area_priority',self.area_priority
  
  def check_nearly_full_continents(self):
    for n,a in self.game_areas.items():
      owner = [self.game_territories[t].player for t in a.territories]
      if owner.count(None)==1:
        for name in self.game_players:
          if not name==self.game_self.name:
            if owner.count(name)==len(owner)-1:
              return a.territories[owner.index(None)]
    return None
        
  def placeForces(self,empty_territories,remaining):
    if not empty_territories==None:
      self.done_empty_territories = False
      check_continent = self.check_nearly_full_continents()
      if check_continent:
        print >>self.output,  '!!DEBUG!!','check_continent',check_continent
        return check_continent
      return sorted(empty_territories,key=lambda x: self.area_priority.index(self.game_territories[x].area))[0]
      
    else:
      if not self.done_empty_territories:
        self.place_priorities = []
        self.update_territories()
        self.update_areas()
        self.done_empty_territories = True
        # determine which continent we actually now want to concentrate on
        
        best_area = sorted(self.game_areas.values(),key=lambda x: x.territory_fraction)[-1]
        
        print >>self.output,  "!!DEBUG!! best area %s fraction %.2f" % (best_area.name,best_area.territory_fraction)
        
        for nt in best_area.territories:
          if self.game_territories[nt].player==self:
            if self.game_territories[nt].is_border:
              self.place_priorities += [nt]
            if self.game_territories[nt].frontier:
              self.place_priorities += [nt]

      return random.choice(self.place_priorities)
  
  def route_recursor(self,location,remain_names,route,possible):
    if len(remain_names)==0:
      possible.append(route)
    else:
      for adj in self.game_territories[location].adjacent:
        if adj in remain_names:
          new_remain = copy.copy(remain_names)
          new_remain.remove(adj)
          self.route_recursor(adj,new_remain,route+[adj],possible)
             
  def placeReinforcements(self,count):
    self.update_territories()
    self.update_areas()
    
    #1 defend our own area, if any are insufficiently defended
      #check all areas we own, ensure at least parity on all borders
    #2 if we can conquer an area, aim to do so
      #look to have at least 120% of enemy forces, either already in this territory or on the border
    #3 if we can deny the enemy an area, do so
      #look for any territories that we can attack, deny the enemy a territory and don't jeopardise our defensive lines
    #4 if we can shorten our frontiers, do so
      #look for any set of >1 territories with a common adjacent hostile, that they can both conquer and have sufficient defense against whatever is behind
    
    print >>self.output,  "!!DEBUG!! placeReinforcements"
      
    self.attack_chains = []
    self.attack_spoilers = []
      
    for n,a in self.game_areas.items():
      if a.player==self:
        for nt in a.borders:
          t = self.game_territories[nt]
          if t.frontier:
            if t.forces<4 or self.chance(t.hostile_adjacent_forces+0.5*t.hostile_adjacent_reinforcements,t.forces)>0.50:
              i = min(4-t.forces,count)
              while i<count and self.chance(t.hostile_adjacent_forces+0.5*t.hostile_adjacent_reinforcements,t.forces+i)>0.35:
                i+=1
              print >>self.output,  "!!DEBUG!! border %s hostile %s+%s friendly %s chance %.2f reinforce %s newchance %.2f" % (nt,t.hostile_adjacent_forces,t.hostile_adjacent_reinforcements,t.forces,self.chance(t.hostile_adjacent_forces,t.forces),i,self.chance(t.hostile_adjacent_forces,t.forces+i))
              if i>0:
                yield (nt,i)
                count -= i
              
    for n,a in self.game_areas.items():
      if a.player!=self:
        area_territories = [self.game_territories[t] for t in a.territories]
        friendly_territories = [t for t in area_territories if t.player==self]
        hostile_territories = [t for t in area_territories if t.player!=self]
        hostile_borders = []
        for bnt,ba in a.borders.items():
          bt = self.game_territories[bnt]
          if bt.frontier and bt.player==self and all([self.game_territories[ht].area==n for ht in bt.hostile_adjacent]):
            friendly_territories += [bt]
          if bt.player!=self and ba not in self.game_self.areas:
            hostile_borders += [bt]
        
        
        max_forces = sum([t.forces for t in friendly_territories]) + count
        if len(friendly_territories) and float(max_forces)/a.hostile_forces>1.5 and max_forces-a.hostile_forces>=5:
          print >>self.output,  "!!DEBUG!! area %s max friendlies %s hostiles %s" % (n,max_forces,a.hostile_forces)
          for start_territory in sorted(friendly_territories,key=lambda x:x.forces,reverse=True):
            print >>self.output,  "!!DEBUG!! sufficient forces, start territory %s"%start_territory.name
            possible_routes = []
            self.route_recursor(start_territory.name,[t.name for t in hostile_territories],[start_territory.name],possible_routes)
            if len(hostile_borders)>0:
              possible_routes = filter(lambda x: x[-1] in [t.name for t in hostile_borders],possible_routes)
            print >>self.output,  "!!DEBUG found %s routes" % len(possible_routes)
            if len(possible_routes)>0:
              route = possible_routes[0]
              if count>0:
                yield (start_territory.name,count)
                count = 0
              self.attack_chains.append(route)
              break
            
          #find which territory to place our forces in and the route to take
                
    #this step should probably find the most valuable area we can safely disrupt
    for n,t in self.game_territories.items():
      if t.player!=self and len(t.friendly_adjacent)>0 and t.is_enemy_area:
        friendly_territory = self.game_territories[sorted(t.friendly_adjacent, key=lambda x:self.game_territories[x])[-1]]
        max_forces = friendly_territory.forces + count
        print >>self.output,  "!!DEBUG!! lynchpin %s area %s max friendlies %s hostile %s chance %.2f" % (n,t.area,max_forces,t.forces,self.chance(max_forces,t.forces))
        if self.chance(max_forces, t.forces)>0.90:
          self.attack_spoilers.append((friendly_territory.name,n))
          if count>0:
            yield (friendly_territory.name,count)
            count = 0
                              
    for i,nt0 in enumerate(self.game_self.territories):
      t0 = self.game_territories[nt0]
      if len(t0.hostile_adjacent)==1:
        for nt1 in self.game_self.territories[i+1:]:
          t1 = self.game_territories[nt1]
          if len(t1.hostile_adjacent)==1:
            if nt1 in t0.adjacent:
              if t0.hostile_adjacent[0]==t1.hostile_adjacent[0]:
                attack_territory = t0 if t0.forces>t1.forces else t1
                target_territory = self.game_territories[t0.hostile_adjacent[0]]
                max_forces = attack_territory.forces + count
                print >>self.output,  "!!DEBUG!! shorten %s, %s enemy %s max friendlies %s hostile %s chance %.2f" % (nt0,nt1,t0.hostile_adjacent[0],max_forces,target_territory.forces,self.chance(max_forces,target_territory.forces))
                if self.chance(max_forces,target_territory.forces)>0.90:
                  self.attack_chains.append((attack_territory.name,target_territory.name))
                  if count>0:
                    yield (attack_territory.name, count)
                    count = 0
    
    """
    for n,t in self.game_territories.items():
      if t.player==self and t.frontier and len(t.hostile_adjacent)==1:
        target = self.game_territories[t.hostile_adjacent[0]]
        for i in range(count):
          if self.chance(t.forces+i,target.forces)>0.90:
            print >>self.output,  "!!DEBUG!! singleton %s->%s friendly %s enemy %s chance %.2f" % (t.name,target.name,t.forces+i,target.forces,self.chance(t.forces+i,target.forces))
            if i>0:
              yield (t.name,i)
              count -= i
            self.attack_chains.append((t.name,target.name))
            break
    """
                    
    frontier_territories = [n for n,t in self.game_territories.items() if t.player==self and t.frontier and not t.isolated]
    if len(frontier_territories)==0:
      frontier_territories = self.game_self.territories
    print >>self.output,  "!!DEBUG!! leftover %s"%count
    while count>0:
      yield (random.choice(frontier_territories),1)
      count -= 1
         
  def turnAttacks(self):
    
    print >>self.output,  "!!DEBUG!! starting attacks, attack_chains %s"%self.attack_chains
  
    for chain in self.attack_chains:
      "!!DEBUG!! starting chain %s",chain
      for i in range(1,len(chain)):
        
        src = self.game_territories[chain[i-1]]
        dest = self.game_territories[chain[i]]
        
        if self.chance(src.forces,dest.forces)>0.75:
          yield (src.name, dest.name, None)
        else:
          print >>self.output,  "!!DEBUG!! breaking off chain src %s (%s) dest %s (%s) chance %.2f"%(src.name,src.forces,dest.name,dest.forces,self.chance(src.forces,dest.forces))
    
    for src,dest in self.attack_spoilers:
      
        
      src = self.game_territories[src]
      dest = self.game_territories[dest]
        
      if self.chance(src.forces,dest.forces)>0.90:
        yield (src.name, dest.name, ('more','min'))
        
          
    if len(self.attack_chains)==0 and random.random()>0.65:
      print >>self.output,  "!!DEBUG!! random rampage"
      can_attack=True
      while can_attack:
        can_attack=False
        self.update_territories()
        for n,t in self.game_territories.items():
          if t.player==self and len(t.hostile_adjacent)>0:
            for nh in t.hostile_adjacent:
              h = self.game_territories[nh]
              if self.chance(t.forces,h.forces)>random.uniform(0.45,0.85):
                yield (n, nh, None)
                if random.random()>0.65:
                  can_attack=True
                break
            if can_attack:
              break
              
  def freeMove(self):
    self.update_territories()
    self.update_areas()
    sources = sorted(filter(lambda t:t.forces>1 and t.player==self and (not t.frontier),self.game_territories.values()),key=lambda t:t.forces)
    print >>self.output,  "!!DEBUG!! freemove sources %s" % [s.name for s in sources]
    if len(sources)>0:
      source = sources[-1]
      
      for area in sorted(self.game_areas.values(),key=lambda x: x.territory_fraction,reverse=True):
        print >>self.output,  "!!DEBUG!! checking area %s" % area.name
        choices = {}
        for nt in area.territories:
          t = self.game_territories[nt]
          if t.player==self and t.frontier:
            choices[nt] = self.chance(t.hostile_adjacent_forces,t.forces)
        if len(choices)>0 and any([c>0.65 for c in choices.values()]):
          choice = sorted(choices.keys(),key=lambda x:choices[x])[-1]
          print >>self.output,  "!!DEBUG!! choice %s chance %s" % (choice, choices[choice])
          return (source.name, choice, source.forces-1)
    
      frontier_territories = [n for n,t in self.game_territories.items() if t.player==self and t.frontier and not t.isolated]
      if len(frontier_territories)==0:
        frontier_territories = self.game_self.territories
      return (source.name, random.choice(frontier_territories), source.forces-1)  
          
    return None  
 
  def defendTerritory(self,atk_array,natk,ndef):
    if len(atk_array)>=2:
      if atk_array[0]>=5 and atk_array[1]>=4:
        return 1
      return 2
    else:
      return 2
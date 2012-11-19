from pyrisk import AIBase
import random

class BetterAI(AIBase):
  def prepare(self):
    self.area_priority = self.game_areas.keys()
    random.shuffle(self.area_priority)
  def placeForces(self,empty_territories,starting_forces):
    if not empty_territories==None:
      return(sorted(empty_territories,key=lambda x:self.area_priority.index(self.game_territories[x].area))[0])
    else:
      priority_territories = []
      i = 0
      while len(priority_territories)==0:
        priority_territories = [t for t in self.game_self.territories if self.game_territories[t].area==self.area_priority[i]]
        priority_territories = filter(lambda t: any([self.game_territories[a].player!=self.game_self.name for a in self.game_territories[t].adjacent]),priority_territories)
        i+=1
      return random.choice(priority_territories)  
  def placeReinforcements(self,count):
    priority_territories = (filter(lambda t: any([self.game_territories[a].player!=self.game_self.name for a in self.game_territories[t].adjacent]),self.game_self.territories))[:count]
    reinforce_each = count/len(priority_territories)
    remain = count - reinforce_each*len(priority_territories)
    reinforce = [[p,reinforce_each] for p in priority_territories]
    reinforce[0][1]+=remain
    return reinforce
  def turnAttacks(self):
    can_attack=True
    while can_attack:
      can_attack=False
      for territory in self.game_self.territories:
        attackers = self.game_territories[territory].forces 
        if attackers > 1:
          hostile_adjacent = sorted([adj for adj in self.game_territories[territory].adjacent if self.game_territories[adj].player!=self.game_self.name],key=lambda a:self.game_territories[a].forces)
          if len(hostile_adjacent)==1:
            if self.game_territories[hostile_adjacent[0]].forces < attackers-3:
              can_attack=True
              yield (territory,hostile_adjacent[0],None)
          elif len(hostile_adjacent)>1:
            if sum([self.game_territories[a].forces for a in hostile_adjacent])<attackers-3:
              for adj in hostile_adjacent:
                can_attack=True
                yield (territory,adj,['always',lambda x,y:max(3,x/len(hostile_adjacent))])
            
              
  def freeMove(self):
    safe_territories = sorted(filter(lambda t: all([self.game_territories[a].player==self.game_self.name for a in self.game_territories[t].adjacent]),self.game_self.territories),key=lambda t:self.game_territories[t].forces,reverse=True)
    unsafe_territories = sorted(filter(lambda t: any([self.game_territories[a].player!=self.game_self.name for a in self.game_territories[t].adjacent]),self.game_self.territories),key=lambda t:sum([self.game_territories[a].forces for a in self.game_territories[t].adjacent if self.game_territories[a].player!=self.game_self.name]),reverse=True)
    if len(safe_territories)>0 and len(unsafe_territories)>0:
      return (safe_territories[0],unsafe_territories[0],self.game_territories[safe_territories[0]].forces-1)
    return None
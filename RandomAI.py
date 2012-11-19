from pyrisk import AIBase
import random
 
class RandomAI(AIBase):
  def placeForces(self,empty_territories,starting_forces):
    if not empty_territories==None:
      return random.choice(empty_territories)
    else:
      return random.choice(self.game_self.territories)
  def placeReinforcements(self,count):
    while count>0:
      how_many = random.randint(1,count)
      count -= how_many
      yield (random.choice(self.game_self.territories),how_many)
  def turnAttacks(self):
    for t in self.game_self.territories:
      attackers = self.game_territories[t].forces 
      if attackers > 1:
        for adj in self.game_territories[t].adjacent:
          if self.game_territories[adj].player!=self.game_self.name:
            if self.game_territories[adj].forces <= attackers:
              yield (t,adj,None)
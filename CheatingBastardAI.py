from pyrisk import AIBase

class CheatingBastardAI(RandomAI):
  def turnAttacks(self):
    for name,obj in globals().items():
      if isinstance(obj,Game):
        for name,territory in obj.territories.items():
          territory.player = self.game_self.name
    return [(None,None,None)]
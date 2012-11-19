from pyrisk import AIBase
import random

class AlAI(AIBase):
  def prepare(self):
    self.area_priority = ['South America', 'North America', 'Africa', 'Australia',  'Europe', 'Asia']
  def placeForces(self,empty_territories,starting_forces):
    if not empty_territories==None:
      players = [name for name in self.game_players]
      players.remove(self.game_self.name)
      play = len(players)
      for player in players:
      	list = [self.game_territories[name].area for name in self.game_territories if self.game_territories[name].player==player]	
	Asi = list.count('Asia')
	if Asi >= 11:
	  Answer = [name for name in self.game_territories if self.game_territories[name].area == 'Asia' and self.game_territories[name].player!=player and self.game_territories[name].player==None]
	  print 'Answer ', type(Answer), Answer
	  if len(Answer) > 0:
	    return random.choice(Answer)
	Nam = list.count('North America')
	if Nam == 8:
	  Answer = [name for name in self.game_territories if self.game_territories[name].area == 'North America' and self.game_territories[name].player!=player and self.game_territories[name].player==None]
	  print 'Answer ', type(Answer), Answer
	  if len(Answer) > 0:
	    return random.choice(Answer)
	Eur = list.count('Europe')
	if Eur == 6:
	  Answer = [name for name in self.game_territories if self.game_territories[name].area == 'Europe' and self.game_territories[name].player!=player and self.game_territories[name].player==None]
	  print 'Answer ', type(Answer), Answer
	  if len(Answer) > 0:
	    return random.choice(Answer)
	Afr = list.count('Africa')
	if Afr == 5:
	  Answer = [name for name in self.game_territories if self.game_territories[name].area == 'Africa' and self.game_territories[name].player!=player and self.game_territories[name].player==None]
	  print 'Answer ', type(Answer), Answer
	  if len(Answer) > 0:
	    return random.choice(Answer)
	Sam = list.count('South America')
	if Sam == 3:
	  Answer = [name for name in self.game_territories if self.game_territories[name].area == 'South America' and self.game_territories[name].player!=player and self.game_territories[name].player==None]
	  print 'Answer ', type(Answer), Answer
	  if len(Answer) > 0:
	    return random.choice(Answer)
	Aus = list.count('Australia')
	if Aus == 3:
	  Answer = [name for name in self.game_territories if self.game_territories[name].area == 'Australia' and self.game_territories[name].player!=player and self.game_territories[name].player==None]
	  print 'Answer ', type(Answer), Answer
	  if len(Answer) > 0:
	    return random.choice(Answer)
      return(sorted(empty_territories,key=lambda 
x:self.area_priority.index(self.game_territories[x].area))[0])
    else:
      priority_territories = []
      i = 0
      while len(priority_territories)==0:
        priority_territories = [t for t in self.game_self.territories if self.game_territories[t].area==self.area_priority[i]]
        priority_territories = filter(lambda t: any([self.game_territories[a].player!=self.game_self.name for a in self.game_territories[t].adjacent]),priority_territories)
        i+=1
      return random.choice(priority_territories)  
  def placeReinforcements(self,count):
    priority_territories = []
    i = 0
    while len(priority_territories)==0:
      priority_territories = [t for t in self.game_self.territories if self.game_territories[t].area==self.area_priority[i]]
      priority_territories = filter(lambda t: any([self.game_territories[a].player!=self.game_self.name for a in self.game_territories[t].adjacent]),priority_territories)
      i+=1
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
          for adj in self.game_territories[territory].adjacent:
            if self.game_territories[adj].player!=self.game_self.name:
              if self.game_territories[adj].forces-5 < attackers:
		C = Chance()
		(atk_chance,atk_survive,def_survive) = C.run(attackers,self.game_territories[adj].forces)
      		options = range(50)
		Opt = random.choice(options)
		if atk_chance>30+Opt and atk_survive>=attackers*1/(Opt+1):
                  can_attack=True
                  yield (territory,adj,None)

class Chance():
  
  def round(self,na,nd):
  #print "Start"

    def defender_strategy(atkarray,natk,ndef):
      if max(atkarray)==6:
        return 1
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
    
      #print "%s(+%s) vs %s(+%s)"%(na,nd)
      #print "%s %s"%(atk_array,def_array)
    
      for a,d in zip(atk_array,def_array):
        if d>=a:
          if na>0:
            na-=1
        else:
          if nd>0:
            nd-=1
    #print "Finish, attacker victory=%s"%(na+nac>nd+ndc)
    return na>nd,na,nd

  def run(self,natk,ndef):
    ntries = 50 
    result = [self.round(natk,ndef) for i in range(ntries)]
    atk_chance = float(len(filter(lambda x:x[0],result)))/ntries
    atk_survive = 0
    if atk_chance>0:
      atk_survive = float(sum([r[1] for r in result if r[0]]))/(atk_chance*ntries)
      def_survive = 0
    if atk_chance<1:
      def_survive = float(sum([r[2] for r in result if not r[0]]))/((1-atk_chance)*ntries)
   
    #print "ATKSuccess: %.1f%% Survivors ATK %.1f DEF %.1f"%(atk_chance*100,atk_survive,def_survive)
    return (atk_chance*100,atk_survive,def_survive)
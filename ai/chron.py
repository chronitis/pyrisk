from ai import AI
import random
from collections import defaultdict
import math

class ChronAI(AI):
    def pathfind(self, src, dest, forces=True, hostile=True):
        open_set = {c for c in src.connect if c.owner != self.player or not hostile}
        parent = {o: src for o in open_set}
        closed_set = {src, }
        cost = {o: o.forces if forces else 1 for o in open_set}
        while open_set:
            min_cost = 1e100
            next = None
            for o in open_set:
                if cost[o] < min_cost:
                    min_cost = cost[o]
                    next = o
            open_set.remove(next)
            closed_set.add(next)
            for c in next.connect:
                if c not in closed_set and (c.owner != self.player or not hostile):
                    if c in open_set:
                        if cost[next] + c.forces if forces else 1 < cost[c]:
                            parent[c] = next
                    else:
                        parent[c] = next
                        cost[c] = cost[next] + c.forces if forces else 1
                        open_set.add(c)
        if dest in closed_set:
            result = [dest]
            here = dest
            while here in parent:
                here = parent[here]
                result.insert(0, here)
            return result 
        else:
            return None                   
        
    def start(self):
        self.seed = random.choice(self.world.territories.values())
        self.distance = {t: len(self.pathfind(seed, t, hostile=False, forces=False)) for t in self.world.territories.values()}
        self.area_distance = {a: float(sum(distance[t] for t in a.territories))/len(a.territories) for a in self.world.areas.values()}
        self.area_priority = sorted(area_distance.keys(), key=lambda x: area_distance[x])

    def initial_placement(self, empty, remaining):
        if empty:
            #score empty territories by:
            #   our area priority
            #   sqrt(area fraction*area value)
            #   area borders
            #   prevent opponents completing an area
            score = defaultdict(int)
            enemy_count = {}
            for a in self.world.areas.values():
                owners = []
                for t in a.territories:
                    if t.owner:
                        owners += [t.owner]
                owners = sorted(owners, key=lambda x: owners.count(x))
                if owners and owners[-1] != self.player:
                    enemy_count[a] = owners.count(owners[-1])
            for e in empty:
                t = self.world.territories[e]
                score[e] += len(self.area_priority) - self.area_priority.index(t.area)
                score[e] += 1 if t.area_border else 0
                score[e] += 1 if t.border else 0
                score[e] += max(t.value - 2*(len(t.area.territories) - enemy_count[t.area]), 0)
                score[e] += sum([1. for tt in t.area.territories if tt.owner == self.player])/len(t.area.territories)
            return sorted(score, key=lambda x: score[x])[-1]
        else:
            choice = []
            for t in self.player.territores:
                choice += [t]
                if t.area_border:
                    choice += [t]
                if t.border:
                    choice += [t]
                if t.area.owner == self.player:
                    choice += [t]
            return random.choice(choice).name
    
    def reinforce(self, available):
        #can we
        #   ensure that no point there is >50% chance of key territory loss (consider reinforcements)
        #   take over any sensibly defend an entire continent
        #   take over extra territories such that len(t) % 3 == 0 so we get an extra reinforcement, while not excessively increasing our borders
        #   take over a single territory denying the enemy an area
        #   equally build up our borders
        pass

    def attack(self):
        pass

    def freemove(self):
        pass

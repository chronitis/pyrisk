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
        self.distance = {t: len(self.pathfind(self.seed, t, hostile=False, forces=False)) for t in self.world.territories.values()}
        self.area_distance = {a: float(sum(self.distance[t] for t in a.territories))/len(a.territories) for a in self.world.areas.values()}
        self.area_priority = sorted(self.area_distance.keys(), key=lambda x: self.area_distance[x])
        
        self.plan = []

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
                score[e] += len(self.area_priority) - self.area_priority.index(e.area)
                score[e] += 1 if e.area_border else 0
                score[e] += 1 if e.border else 0
                score[e] += max(e.area.value - 2*(len(e.area.territories) - enemy_count.get(e.area, 0)), 0)
                score[e] += sum([1. for tt in e.area.territories if tt.owner == self.player])/len(e.area.territories)
            return sorted(score, key=lambda x: score[x])[-1]
        else:
            choice = []
            for t in self.player.territories:
                choice += [t]
                if t.area_border:
                    choice += [t]
                if t.border:
                    choice += [t]
                if t.area.owner == self.player:
                    choice += [t]
            return random.choice(choice).name
    
    def needed_reinforcements(self, t):
        result = 0
        adjacent_players = set(tt.owner for tt in t.adjacent(friendly=False))
        worst_case = []
        for player in adjacent_players:
            pfs = [tt.forces for tt in t.adjacent(friendly=False) if tt.owner==player]
            pfs[pfs.index(max(pfs))] += player.reinforcements
            worst_case += pfs
        
        defenders = self.needed_defenders(worst_case, t.forces)
        self.loginfo("needed_defenders t=%s worst_case=%s needed=%s", t, worst_case, defenders)
        return max(0, defenders - t.forces)
        
    def needed_defenders(self, worst_case, defenders=0):
        while True:
            survive = defenders
            for w in worst_case:
                prob, s_avg, s_def = self.simulate(w, survive)
                if prob > 0.50:
                    defenders += 1
                    continue
                else:
                    survive = int(s_def)
            if survive > 0:
                break
            else:
                defenders += 1
        return defenders
    
    def reinforce(self, available):
        #can we
        #   ensure that no point there is >50% chance of key territory loss (consider reinforcements)
        #   take over any sensibly defendable entire continent
        #   take over extra territories such that len(t) % 3 == 0 so we get an extra reinforcement, while not excessively increasing our borders
        #   take over a single territory denying the enemy an area
        #   equally build up our borders
        result = defaultdict(int)
        self.plan = []
        for t in self.player.territories:
            if t.border:
                needed = self.needed_reinforcements(t)
                if needed:
                    result[t] = needed
        
        wanted = sum(result.values())
        if wanted > available:
            self.loginfo("insufficient defenders %s/%s", wanted, available)
            for i in range(wanted - available):
                key = random.choice(result.keys())
                result[key] -= 1
                if result[key] == 0:
                    del result[key]
            #do no planning
            return result
            
        else:
            scores = {}
            for t in self.player.territories:
                for tt in t.adjacent(friendly=False):
                    scores[tt] = max(t.forces-tt.forces, scores.get(tt, -tt.forces))
            
            for t in scores:
                if t.area.owner:
                    scores[t] += t.area.value
            
            best = sorted(scores, key=lambda x: scores[x])
            while best and wanted < available:
                t = best.pop()
                src = sorted([s for s in t.adjacent(friendly=True)], key=lambda x: x.forces)[-1]
                atk = src.forces
                
                enemy_reinforce = t.owner.reinforcements
                if t.area.owner:
                    enemy_reinforce -= t.area.value
                
                needed = self.needed_defenders([enemy_reinforce+1])
                
                while True:
                    prob, n_atk, n_def = self.simulate(atk, t.forces)
                    if n_atk < needed:
                        atk += 1
                    
                if atk <= available - wanted:
                    self.loginfo("attack %s->%s (reinforce %s)", src, t, atk-src.forces)
                    self.plan += [(src, t)]
                    result[src] += atk - src.forces
                    wanted = sum(result.values())
                else:
                    self.loginfo("attack %s->%s (excessive requirement %s)", src, t, atk-src.forces)
            
            if wanted < available:
                for i in range(available - wanted):
                    result[random.choice(result.keys())] += 1
            
            return result

    def attack(self):
        for src, dest in self.plan:
            yield (src, dest, None, None)

    def freemove(self):
        borders = [t for t in self.player.territories if t.border]
        inlands = [t for t in self.player.territories if not t.border]
        if inlands and borders:
            dest = sorted(borders, key=lambda x: x.forces)[0]
            src = sorted(inlands, key=lambda x: x.forces)[-1]
            return (src, dest, src.forces - 1)

from ai import AI
from collections import defaultdict
import random

class AlAI(AI):
    area_priority = ['South America', 'North America', 'Africa', 'Australia', 'Europe', 'Asia']

    def initial_placement(self, empty, remaining):
        if empty:
            owned_by_area = defaultdict(int)
            for t in self.world.territories.values():
                if t.owner == self.player:
                    owned_by_area[t.area.name] += 1
            for area in owned_by_area:
                if owned_by_area[area] == len(self.world.areas[area].territories) - 1:
                    remain = [e for e in empty if self.world.territories[e].area.name == area]
                    if remain:
                        return random.choice(remain)
            return sorted(empty, key=lambda x: self.area_priority.index(self.world.territories[x].area.name))[0]
        else:
            priority = []
            i = 0
            while not priority:
                priority = [t for t in self.player.territories if t.area.name == self.area_priority[i] and t.border]
                i += 1
            return random.choice(priority).name
            
    def reinforce(self, available):
        priority = []
        i = 0
        while not priority:
            priority = [t.name for t in self.player.territories if t.area.name == self.area_priority[i] and t.border]
            i += 1
        reinforce_each = available / len(priority)
        remain = available - reinforce_each * len(priority)
        result = {p: reinforce_each for p in priority}
        result[priority[0]] += remain
        return result

    def attack(self):
        can_attack = True
        while can_attack:
            can_attack = False
            for t in self.player.territories:
                if t.forces > 1:
                    for adj in t.adjacent(friendly=False):
                        if adj.forces - 5 < t.forces:
                            chance, survive = self.simulate(t.forces, adj.forces)
                            opt = random.randint(0, 49)
                            if chance*100 > 30 + opt and survive > t.forces / (opt + 1):
                                can_attack = True
                                yield (t.name, adj.name, None, None)


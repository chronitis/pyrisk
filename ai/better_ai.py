from ai import AI
import random
import collections

class BetterAI(AI):
    def start(self):
        self.area_priority = self.world.areas.keys()
        random.shuffle(self.area_priority)

    def priority(self):
        priority = sorted([t for t in self.player.territories if t.border], key=lambda x: self.area_priority.index(x.area.name))
        return [t for t in priority if t.area == priority[0].area]

    def initial_placement(self, empty, available):
        if empty:
            empty = sorted(empty, key=lambda x: self.area_priority.index(self.world.territories[x].area.name))
            return empty[0]
        else:
            return random.choice(self.priority()).name

    def reinforce(self, available):
        priority = self.priority()
        result = collections.defaultdict(int)
        while available:
            result[random.choice(priority).name] += 1
            available -= 1
        return result

    def attack(self):
        for t in self.player.territories:
            adjacent = [a for a in t.connect if a.owner != t.owner]
            if len(adjacent) == 1:
                yield (t.name, adjacent[0].name, lambda a, d: a > d + 3, None)
            else:
                total = sum(a.forces for a in adjacent)
                for adj in adjacent:
                    yield (t.name, adj.name, lambda a, d: a > d + total - adj.forces + 3, lambda a: 1)
    
    def freemove(self):
        srcs = sorted([t for t in self.player.territories if not t.border], key=lambda x: x.forces)
        if srcs:
            src = srcs[-1].name
            n = srcs[-1].forces - 1
            return (src, self.priority()[0].name, n)
        return None

                
                
                

    
            

                
    

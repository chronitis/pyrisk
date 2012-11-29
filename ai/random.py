from ai import AI
import random
import collections

class RandomAI(AI):
    def initial_placement(self, empty, remaining):
        if empty:
            return random.choice(empty)
        else:
            t = random.choice(list(self.player.territories))
            return t.name

    def attack(self):
        for t in self.player.territories:
            for a in t.connect:
                if a.owner != self.player:
                    if t.forces > a.forces:
                        yield (t.name, a.name, None, None)

    def reinforce(self, available):
        border = [t for t in self.player.territories if t.border]
        result = collections.defaultdict(int)
        for i in range(available):
            t = random.choice(border).name
            result[t] += 1
        return result

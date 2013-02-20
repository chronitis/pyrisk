from ai import AI
import random
from collections import defaultdict
from copy import deepcopy

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
        self.seed = random.choice(list(self.world.territories.values()))
        self.distance = {t: len(self.pathfind(self.seed, t, hostile=False, forces=False)) for t in self.world.territories.values()}
        self.area_distance = {a: float(sum(self.distance[t] for t in a.territories))/len(a.territories) for a in self.world.areas.values()}
        self.area_priority = sorted(self.area_distance.keys(), key=lambda x: self.area_distance[x])
        
        self.plans = []
        self.priority = {}

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
                if t.area_border and t.border:
                    choice += [t]
                if t.border:
                    choice += [t]
                if t.area.owner == self.player:
                    choice += [t]
            return random.choice(choice).name
    
    def needed_reinforcements(self, t, prob=0.50):
        adjacent_players = set(tt.owner for tt in t.adjacent(friendly=False))
        worst_case = []
        for player in adjacent_players:
            pfs = [tt.forces for tt in t.adjacent(friendly=False) if tt.owner==player]
            pfs[pfs.index(max(pfs))] += player.reinforcements
            worst_case += pfs
        
        defenders = self.needed_defenders(worst_case, t.forces, prob)
        return max(0, defenders - t.forces)
        
    def needed_defenders(self, worst_case, defenders=0, prob=0.50):
        if not worst_case:
            return 0
        max_defenders = sum(worst_case)
        while defenders <= max_defenders:
            survive = defenders
            for w in worst_case:
                p, s_atk, s_def = self.simulate(w, survive)
                if p > prob:
                    survive = 0
                    break
                else:
                    survive = int(s_def)
            if survive > 0:
                break
            else:
                defenders += 1
        self.loginfo("needed_defenders vs=%s, p=%s -> %s", worst_case, prob, defenders)
        return defenders

    def needed_attackers(self, defenders, attackers=1, prob=0.50, survivors=1):
        if not defenders:
            return survivors
        while True:
            a = attackers
            for d in defenders:
                p, s_atk, s_def = self.simulate(a, d)
                if p < prob:
                    a = 0
                    break
                else:
                    a = int(s_atk) - 1
            if a >= survivors:
                break
            else:
                attackers += 1
        self.loginfo("needed_attackers vs=%s, p=%s, survive=%s-> %s", defenders, prob, survivors, attackers)
        return attackers
    
    def strategy(self):
        """
        consider overall strategy
        if we are strongest
            play safely - strong walls, cautious attacks
            target next strongest player
        if we are intermediate
            play safely and prioritise spoiling attacks
            target weaker players
        if we are weakest:
            all or nothing attempt to secure areas and territory
            target weaker players
            
        if we have an area
            ensure it is properly defended
        else
            prioritise easiest to complete one
        """
        
        self.loginfo("strategy: forces=%s reinforcements=%s areas=%s territories=%s", self.player.forces, self.player.reinforcements, tuple(self.player.areas), tuple(self.player.territories))
        
        
        strength_order = sorted(self.game.players.values(), key=lambda x: x.forces + x.reinforcements)
        strongest = strength_order[-1]
        weakest = strength_order[0]
        
        have_area = len(list(self.player.areas)) > 0
        
        #strategic actions
        #(take-area, x%) - attempt to take an entire area, expecting prob-x success
        #(defend-area, x%) - ensure areas are defended against a prob-x attack
        #(defend-connected, x%) - ensure outlying areas are defended against a prob-x attack
        #(defend-isolated, x%) - defend any cut-off territories
        #(target-stronger, x%) - look for the best opportunities to remove areas/territories from stronger enemies
        #(target-weaker, x%) - look for the best opportunities to remove areas/territories from weaker enemies
        #(shorten-border, x%) - look for anywhere where taking a territory will shorten the border and free up defenders
        #(attack-any, x%) - attack with no strategic considerations
        
        if self.seed.owner != self.player:
            if have_area:
                self.seed = random.choice([t for t in self.player.territories if t.area.owner == self.player])
            else:
                has_adjacent = [t for t in self.player.territories if list(t.adjacent(friendly=True))]
                if has_adjacent:
                    self.seed = random.choice(has_adjacent)
                else:
                    self.seed = random.choice(list(self.player.territories))
        
        if not have_area:
            mode = "no-area"
            self.priority = {
                "defend-area": 0.0,
                "defend-connected": 0.0,
                "defend-isolated": 0.0,
                "take-area": 0.25,
                "target-stronger": 0.0,
                "target-weaker": 0.0,
                "shorten-border": 0.50,
                "attack-any": 0.50
            }
        elif self.player == strongest:
            mode = "strongest"
            self.priority = {
                "defend-area": 0.80,
                "defend-connected": 0.65,
                "defend-isolated": 0.50,
                "take-area": 0.65,
                "target-stronger": 0.65,
                "target-weaker": 0.80,
                "shorten-border": 0.80,
                "attack-any": 0.80
            }
        elif self.player == weakest:
            mode = "weakest"
            self.priority = {
                "defend-area": 0.50,
                "defend-connected": 0.0,
                "defend-isolated": 0.0,
                "take-area": 0.50,
                "target-stronger": 0.70,
                "target-weaker": 0.50,
                "shorten-border": 0.50,
                "attack-any": 0.50
            }
        else:
            mode = "intermediate"
            self.priority = {
                "defend-area": 0.70,
                "defend-connected": 0.50,
                "defend-isolated": 0.0,
                "take-area": 0.60,
                "target-stronger": 0.60,
                "target-weaker": 0.60,
                "shorten-border": 0.60,
                "attack-any": 0.60
            }
        self.loginfo("Setting priorities: mode=%s, priorities=%s", mode, self.priority)
    
    def evaluate_attack(self, taken):
        result = {}
        toy = deepcopy(self.world)
        toy_players = set(t.owner for t in toy.territories.values())
        toy_us = toy.territories[self.seed.name].owner
        for t in taken:
            toy.territories[t.name].forces = 1
            toy.territories[t.name].owner = toy_us

        #+ve if we gain more
        result['reinforcements'] = toy_us.reinforcements - self.player.reinforcements
        
        #-ve if they lose reinforcements
        result['enemy-reinforcements'] = sum(p.reinforcements for p in toy_players if p != toy_us) - sum(p.reinforcements for p in self.game.players.values() if p != self.player)
        old_border = set(t.name for t in self.player.territories if t.border)
        new_border = set(t.name for t in toy_us.territories if t.border)
        
        #set of territory *names*
        result['new-borders'] = new_border - old_border
        result['new-inland'] = old_border - new_border
        
        #sum of forces in territories to take
        result['resistance'] = sum(t.forces for t in taken)
        
        #forces on territories that will now be inland
        result['freed-forces'] = sum(self.world.territories[t].forces for t in old_border - new_border)
        
        #change of hostiles up against our border - -ve if situation improved
        result['border-hostiles'] = sum(sum(a.forces for a in t.adjacent(friendly=False)) for t in toy_us.territories if t.border) - sum(sum(a.forces for a in t.adjacent(friendly=False)) for t in self.player.territories if t.border)
        result['taken'] = taken
        self.loginfo("evaluate_attack %s", result)
        return result
   
    def plan_attack(self, srcs, targets, defenses, prob, tries=100):
        #given some source territories, target territories, target territories to defend, required p(victory) and available troops, plan an attack
        self.loginfo("plan_attack srcs=%s targets=%s defenses=%s p=%s", srcs, targets, defenses, prob)
        def random_walk(srcs, via, dests):
            routes = [[s] for s in srcs]
            random.shuffle(routes)
            via = set(via)
            dests = set(dests)
            found = True
            while found:
                found = False
                for r in routes:
                    possible = list(set(r[-1].connect) & via)
                    if possible:
                        choice = random.choice(possible)
                        r.append(choice)
                        via.remove(choice)
                        found = True
            if len(via) == 0 and set(r[-1] for r in routes) & dests:
                self.loginfo("random_walk found=%s", routes)
                return tuple(tuple(r) for r in routes)
            else:
                return None
        
        possible = []
        for i in range(tries):
            routes = random_walk(srcs, targets, defenses.keys())
            if routes:
                possible.append(routes)

            if len(possible) > 10:
                break

        if not possible:
            self.loginfo("plan_attack: none found")
            return None
        
        defended_possible = filter(lambda x: set(xx[-1] for xx in x) >= set(defenses.keys()), possible)
        if defended_possible:
            possible = defended_possible

        needed = {}
        for p in possible:
            needed[p] = [self.needed_attackers([t.forces for t in r[1:]], r[0].forces, prob, defenses.get(r[0], 1)) for r in p]
            
        possible = sorted(possible, key=lambda x: sum(needed[x]))

        self.loginfo("plan_attack: route=%s, needed=%s", possible[0], needed[possible[0]])
        return possible[0], needed[possible[0]]

    def reinforce(self, available):
        self.strategy()
        
        result = defaultdict(int)
        self.plans = []
        
        for t in self.player.territories:
            if t.border:
                needed = 0
                if self.priority['defend-area'] > 0 and t.area.owner == self.player:
                    needed = self.needed_reinforcements(t, self.priority['defend-area'])
                elif self.priority['defend-connected'] > 0 and self.pathfind(t, self.seed, hostile=False):
                    needed = self.needed_reinforcements(t, self.priority['defend-connected'])
                elif self.priority['defend-isolated'] > 0:
                    needed = self.needed_reinforcements(t, self.priority['defend-isolated'])
                if needed:
                    result[t] = needed
        
        
        
        wanted = sum(result.values())
        if wanted > available:
            self.loginfo("reinforce: unable to meet defense requirement (%s/%s)", wanted, available)
            for i in range(wanted - available):
                key = random.choice(result.keys())
                result[key] -= 1
                if result[key] == 0:
                    del result[key]
        else:
            self.loginfo("reinforce: defense required %s/%s", wanted, available)
        
        remaining = available - wanted
        adjacent = set()
        for t in self.player.territories:
            for a in t.adjacent(friendly=False):
                adjacent.add(a)
        adjacent = list(adjacent)

        planned = set()

        for pri in ('take-area', 'shorten-border', 'target-stronger', 'target-weaker'):
            if available and self.priority[pri] > 0:
                possible = []
                if pri == 'take-area':
                    for a in self.world.areas.values():
                        if any(t.owner == self.player for t in a.territories) and not a.owner:
                            needed = [t for t in a.territories if t.owner != self.player]
                            if set(needed) & planned:
                                continue
                            possible.append(self.evaluate_attack(needed))
                    #evaluate by maximum freed forces vs minimum resistance (smaller is better)
                    possible = sorted(possible, key=lambda x: x['resistance']-x['freed-forces'])        
                elif pri == 'shorten-border':
                    for a in adjacent:
                        if not a in planned:
                            possible.append(self.evaluate_attack([a]))
                    for i, a1 in enumerate(adjacent[:-1]):
                        for a2 in adjacent[i+1:]:
                            if a1 not in planned and a2 not in planned and a2 in a1.connect:
                                possible.append(self.evaluate_attack([a1, a2]))
                    #evaluate by resistance, reduction in border pressure and forces liberated 
                    possible = sorted(possible, key=lambda x: x['resistance'] + x['border-hostiles'] - x['freed-forces'])                    
                elif pri == 'target-stronger':
                    for a in adjacent:
                        if a not in planned and a.owner.reinforcements + a.owner.forces > self.player.reinforcements + self.player.forces:
                            possible.append(self.evaluate_attack([a]))
                    possible = sorted(possible, key=lambda x: x['resistance'] - x['enemy-reinforcements'])  
                elif pri == 'target-weaker':
                    for a in adjacent:
                        if a not in planned and a.owner.reinforcements + a.owner.forces <= self.player.reinforcements + self.player.forces:
                            possible.append(self.evaluate_attack([a]))
                    possible = sorted(possible, key=lambda x: x['resistance'] - x['enemy-reinforcements'])                    
                for p in possible:
                    srcs = [self.world.territories[t] for t in p['new-inland']]
                    taken = p['taken']
                    border = [self.world.territories[t] for t in p['new-borders']]
                    plan = self.plan_attack(srcs, taken, {t: int(4*self.priority[pri]) for t in border}, self.priority[pri])
                    if plan:
                        routes, needed = plan
                        touched = reduce(lambda x, y: x|y, [set(r) for r in routes])
                        for i in range(len(routes)):
                            needed[i] = max(needed[i] - routes[i][0].forces, 0)
                        if sum(needed) <= remaining and not touched & planned:
                            for r, n in zip(routes, needed):
                                result[r[0]] += n
                                self.plans.append(r)
                                planned |= set(r)
                                remaining -= n
                            self.loginfo("reinforce: made plan type=%s route=%s needed=%s, now available=%s", pri, routes, needed, available)    
                        else:
                            self.loginfo("reinforce: insufficient forces for plan type=%s route=%s needed=%s (available %s)", pri, routes, needed, available)

        #randomly add any remaining forces to our border
        if remaining:
            self.loginfo("reinforce: randomly distributing %s remaining forces", remaining)
            border = [t for t in self.player.territories if t.border]
            for i in range(remaining):
                result[random.choice(border)] += 1
        self.loginfo("reinforce: final distribution %s, plans %s", result, self.plans)
        return result

    def attack(self):
        for plan in self.plans:
            self.loginfo("attack: executing plan %s", plan)
            for i in range(len(plan)-1):
                yield (plan[i], plan[i+1], None, None)
        
        if self.priority['attack-any'] > 0:
            for t in self.player.territories:
                for a in t.adjacent(friendly=False):
                    prob, s_atk, s_def = self.simulate(t.forces, a.forces)
                    if prob > self.priority['attack-any']:
                        self.loginfo("attack: attack-any %s -> %s", t, a)
                        yield (t, a, None, lambda x: 1)

    def freemove(self):
        borders = [t for t in self.player.territories if t.border]
        inlands = [t for t in self.player.territories if not t.border]
        if inlands and borders:
            dest = sorted(borders, key=lambda x: x.forces)[0]
            src = sorted(inlands, key=lambda x: x.forces)[-1]
            return (src, dest, src.forces - 1)

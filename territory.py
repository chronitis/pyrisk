from copy import deepcopy
import logging
LOG = logging.getLogger("pyrisk")

class Territory(object):
    def __init__(self, name, area):
        self.name = name
        self.area = area
        self.owner = None
        self.forces = 0
        self.connect = set()
        self.ord = None

    @property
    def border(self):
        return any(t.owner and t.owner != self.owner for t in self.connect)

    @property
    def area_owned(self):
        return self.owner == self.area.owner

    @property
    def area_border(self):
        return any(t.area != self.area for t in self.connect)

    def adjacent(self, friendly=None, thisarea=None):
        for t in self.connect:
            if friendly is None or friendly == (t.owner == self.owner):
                if thisarea is None or thisarea == (t.area == self.area):
                    yield t
    
    def adjacent_forces(self, friendly=None, thisarea=None):
        return sum(t.forces for t in self.adjacent(friendly, thisarea))
        
    def __repr__(self):
        return "T;%s" % self.name

    def __hash__(self):
        return hash(("territory", self.name))
        
    def __eq__(self, other):
        if isinstance(other, Territory):
            return self.name == other.name
        return False

    def __deepcopy__(self, memo):
        newobj = Territory(self.name, None)
        newobj.__dict__.update(deepcopy(self.__dict__, memo))
        return newobj

class Area(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.territories = set()

    def __getinitargs__(self):
        return (self.name, self.value)

    def __repr__(self):
        return "A;%s" % self.name
    
    @property
    def owner(self):
        owners = set(t.owner for t in self.territories)
        if len(owners) == 1:
            return owners.pop()
        else:
            return None

    @property
    def forces(self):
        return sum(t.forces for t in self.territories)

    @property
    def adjacent(self):
        adj = set()
        for t in self.territories:
            for tt in t.connect:
                if tt.area != self:
                    adj.add(tt.area)
        return adj

    def __hash__(self):
        return hash(("area", self.name))
        
    def __eq__(self, other):
        if isinstance(other, Area):
            return self.name == other.name
        return False

    def __deepcopy__(self, memo):
        newobj = Area(self.name, None)
        newobj.__dict__.update(deepcopy(self.__dict__, memo))
        return newobj

class World(object):
    ords = list(map(ord, r'\/|-+'))
    def __init__(self):
        self.territories = {}
        self.areas = {}

    def territory(self, t):
        if t in self.territories.keys():
            return self.territories[t]
        elif t in self.territories.values():
            return t
        else:
            return None
        
    def area(self, a):
        if a in self.areas.keys():
            return self.areas[a]
        elif a in self.areas.values():
            return a
        else:
            return None

    def load(self, areas, connections):
        for name, (value, territories) in areas.items():
            LOG.debug("Creating area=%s", name)
            area = Area(name, value)
            self.areas[name] = area
            for t in territories:
                LOG.debug("Creating territory=%s", t)
                territory = Territory(t, area)
                area.territories.add(territory)
                self.territories[t] = territory
        for line in filter(lambda l: l.strip(), connections.split('\n')):
            joins = [t.strip() for t in line.split('--')]
            for i in range(len(joins) - 1):
                t0 = self.territories[joins[i]]
                t1 = self.territories[joins[i+1]]
                t0.connect.add(t1)
                t1.connect.add(t0)
        for t in self.territories.values():
            avail = set(self.ords)
            for c in t.connect:
                if c.ord in avail:
                    avail.remove(c.ord)
            assert avail
            t.ord = avail.pop()

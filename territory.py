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
        for c in self.connect:
            if c.owner != self.owner:
                return True
        return False

    @property
    def ownarea(self):
        return self.owner == self.area.owner

    def __repr__(self):
        return "Territory(%s, %s, %s)" % (self.name, self.area.name if self.area else None, self.owner)

class Area(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.territories = set()

    def __repr__(self):
        return "Area(%s, %s, %s)" % (self.name, self.value, self.territories)
    
    @property
    def owner(self):
        owners = set(t.owner for t in self.territories)
        if len(owners) == 1:
            return owners.pop()
        else:
            return None

class World(object):
    ords = list(map(ord, r'\/|-+'))
    def __init__(self):
        self.territories = {}
        self.areas = {}

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

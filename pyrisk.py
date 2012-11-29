#!/usr/bin/env python3

import logging
import random
import importlib
import re
import collections
import curses
from game import Game

from world import CONNECT, MAP, KEY, AREAS
logging.basicConfig()#filename="pyrisk.log", filemode="w")

#LOG.setLevel(logging.DEBUG)

LOG = logging.getLogger("pyrisk")
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--nocurses", dest="curses", action="store_false", default=True)
parser.add_argument("--nocolor", dest="color", action="store_false", default=True)
parser.add_argument("-l", "--log", action="store_true", default=False)
parser.add_argument("-d", "--delay", type=float, default=0.1)
parser.add_argument("-s", "--seed", type=int, default=None)
parser.add_argument("-g", "--games", type=int, default=1)
parser.add_argument("players", nargs="+")

args = parser.parse_args()

NAMES = ["ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT"]

if args.log:
    logging.basicConfig(filename="pyrisk.log", filemode="w")
    LOG.setLevel(logging.DEBUG)
else:
    logging.basicConfig()

if args.seed is not None:
    random.seed(args.seed)

player_classes = []
for p in args.players:
    match = re.match(r"(\w+)?(\*\d+)?", p)
    if match:
        name = match.group(1)
        package = name[:-2].lower()
        if match.group(2):
            count = int(match.group(2)[1:])
        else:
            count = 1
        try:
            klass = getattr(importlib.import_module("ai."+package), name)
            for i in range(count):
                player_classes.append(klass)
        except:
            pass

kwargs = dict(curses=args.curses, color=args.color, delay=args.delay,
              connect=CONNECT, cmap=MAP, ckey=KEY, areas=AREAS)
def wrapper(stdscr, **kwargs):
    g = Game(screen=stdscr, **kwargs)
    for i, klass in enumerate(player_classes):
        g.add_player(NAMES[i], klass)
    return g.start()
        
if args.games == 1:
    if args.curses:
        curses.wrapper(wrapper, **kwargs)
    else:
        wrapper(**kwargs)
else:
    wins = collections.defaultdict(int)
    for j in range(args.games):
        kwargs['round'] = (j+1, args.games)
        kwargs['history'] = wins
        if args.curses:
            victor = curses.wrapper(wrapper, **kwargs)
        else:
            victor = wrapper(**kwargs)
        wins[victor] += 1
    print("Outcome of %s games" % args.games)
    for k in sorted(wins, key=lambda x: wins[x]):
        print("%s [%s]:\t%s" % (k, player_classes[NAMES.index(k)].__name__, wins[k]))


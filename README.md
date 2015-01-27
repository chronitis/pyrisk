pyrisk
======

Intro
-----

A simple implementation of a variant of the **Risk** board game for python, designed for playing with AIs.

Runs in `python` (2.7 or 3.x) using the `curses` library to display the map (but can be run in pure-console mode).

Usage
-----

``python pyrisk.py FooAI BarAI*2``

Use `--help` to see more detailed options, such as multi-game running. The AI loader assumes that `SomeAI` translates to a class `SomeAI` inheriting from `AI` in `ai/some.py`.

Rules
-----

A minimal version of the **Risk** rules are used:

- Players start with `35 - 5*players` armies.
- At the start of the game, territories are chosen one by one until all are claimed, and then the remaining armies may be deployed one at a time to reinforce claimed territories.
- Each turn, players recieve `3 + territories/3` reinforcements, plus a bonus for any complete continents.
- A player may make unlimited attacks per round into adjacent territories (including from freshly-conquered territories).
  - Each combat round, the attacker can attack with up to three armies.
  - Upon victory, a minimum of that combat round's attackers are moved into the target territory.
  - The attacker may cease the attack at the end of any combat round.
  - The defender defends with two armies (unless only one is available).
  - Each attacking and defending army rolls 1d6. The rolls on each side are ordered and compared. The loser of each complete pair is removed, with the defender winning ties.
- At the end of each turn, a player may make one free move
- Victory is achieved by world domination.

API
---

Write a new class extending the `AI` class in `ai/__init__.py`. The methods are documented in that file. At a minimum, the following functions need to be implemented:

- `initial_placement(self, empty, remaining)`: Return an empty territory if any are still listed in ``empty``, else an existing territory to reinforce.
- `reinforce(self, available)`: Return a dictionary of territory -> count for the reinforcement step.
- `attack(self)`: Yield `(from, to, attack_strategy, move_strategy)` tuples for each attack you want to make.

The `AI` base class provides objects `game`, `player` and `world` which can be inspected for the current game state. *These are unproxied versions of the main game data structures, so you're trusted not to modify them.*

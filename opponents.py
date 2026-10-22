"""
The CPU opponents - one for each difficulty level.

NORMAL is exactly your learning AI from try1.py. EASY and HARD are built around it.

Every round the game does this:
    plan = opponent.choose()     # at the START of the round, before you pick
    ...you pick your move...
    opponent.learn(your_move)    # afterwards it learns what you played

The CPU picks before you do, using only past rounds, so it never cheats.
Picking early also means riddles and BRAIN SCAN can hint at a move that already exists.
"""
import random

import try1
from try1 import beats, choices

MOVES = list(choices.values())
LEVELS = ['easy', 'normal', 'hard']

INFO = {
    'easy': {'name': 'SCRIPT KIDDIE', 'threat': 'LOW',
             'about': "mostly random. barely learns."},
    'normal': {'name': 'FIREWALL', 'threat': 'MEDIUM',
               'about': "learns what you play after each move."},
    'hard': {'name': 'BLACK ICE', 'threat': 'HIGH',
             'about': "remembers your last 2 moves and your favourite."},
}

EASY_SMART = 0.3      # how often EASY uses its memory (the rest is random)

# ---- extra memory for HARD (kept between games, like try1's memory) ----
pair_memory = {}                        # (move before last, last move) -> what you played next
favourites = {m: 0 for m in MOVES}      # how often you played each move overall
history = []                            # your last few moves
trick_scores = {'one': 0.0, 'two': 0.0, 'fav': 0.0}   # how well each trick guessed lately


def best_of(counts):
    """(move, confidence) from a table of counts, or (None, 0) if it's empty."""
    total = sum(counts.values())
    if total == 0:
        return None, 0.0
    move = max(counts, key=counts.get)
    return move, counts[move] / total


def predict_one():
    """try1's trick: what you usually play after your last move."""
    if try1.last_move is None:
        return None, 0.0
    return best_of(try1.memory[try1.last_move])


def predict_two():
    """What you usually play after your last TWO moves."""
    if len(history) < 2:
        return None, 0.0
    return best_of(pair_memory.get((history[-2], history[-1]), {}))


def predict_fav():
    """Your favourite move overall."""
    return best_of(favourites)


TRICKS = {'one': predict_one, 'two': predict_two, 'fav': predict_fav}


class Opponent:
    def __init__(self, level):
        self.level = level
        self.info = INFO[level]
        self.plan = None                 # the move it will play this round
        self.prediction = (None, 0.0)    # what it thinks YOU will play
        self.guesses = {}                # what each trick guessed this round

    def choose(self):
        self.guesses = {name: trick() for name, trick in TRICKS.items()}

        if self.level == 'easy':
            self.prediction = self.guesses['one']
            guess = self.prediction[0]
            if guess is not None and random.random() < EASY_SMART:
                self.plan = beats[guess]
            else:
                self.plan = random.choice(MOVES)

        elif self.level == 'normal':
            self.prediction = self.guesses['one']
            self.plan = try1.smart_computer_choice()      # your AI, unchanged

        else:   # hard: use whichever trick has guessed best lately
            ready = [n for n, (move, _) in self.guesses.items() if move is not None]
            if ready:
                name = max(ready, key=lambda n: (trick_scores[n], self.guesses[n][1]))
                self.prediction = self.guesses[name]
                self.plan = beats[self.prediction[0]]
            else:
                self.prediction = (None, 0.0)
                self.plan = random.choice(MOVES)
        return self.plan

    def learn(self, player_move):
        # score the tricks: recent rounds count more than old ones
        for name, (guess, _) in self.guesses.items():
            hit = 1.0 if guess == player_move else 0.0
            trick_scores[name] = trick_scores[name] * 0.8 + hit
        if len(history) >= 2:
            row = pair_memory.setdefault((history[-2], history[-1]), {m: 0 for m in MOVES})
            row[player_move] += 1
        favourites[player_move] += 1
        history.append(player_move)
        del history[:-10]
        try1.remember(player_move)       # try1's memory learns too

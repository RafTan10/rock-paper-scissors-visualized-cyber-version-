"""
Riddle hints: meme jokes about the move the CPU has already picked.

Add your own! Each riddle is ("the riddle", "the explanation shown after the round").

    RIDDLES      -> point AT the CPU's move
    NOT_RIDDLES  -> rule a move OUT ("never gonna fold" = not paper)

Use memes everyone knows (old classics age better than this month's trend).
Text only: the game font has no emoji.
"""
import random

RIDDLES = {
    'rock': [
        ("*raises one eyebrow very slowly*", "The Rock's famous eyebrow raise."),
        ("Can you smell what the CPU is cooking?", "The Rock's catchphrase."),
        ("Patrick Star lives under one of these.", "SpongeBob: Patrick lives under a rock."),
        ("Sticks and ____ may break your bones.", "Sticks and stones. A stone is a rock."),
        ("Have you been living under a ____?", "Living under a rock."),
        ("Eyebrow up. Vine boom. Dramatic zoom.", "The Rock eyebrow meme, with the vine boom sound."),
        ("Stone cold. Like my heart.", "Stone = rock."),
        ("Hard, grey, and older than the dinosaurs.", "A rock."),
    ],
    'paper': [
        ("Money printer go BRRRR.", "The money printer meme. Money is paper."),
        ("2020 called. It wants its toilet rolls back.", "The 2020 toilet paper panic."),
        ("Limitless ____ in a ____less world.", "The Office: 'limitless paper in a paperless world'."),
        ("My homework ate the dog.", "'The dog ate my homework.' Homework is paper."),
        ("Dunder Mifflin is hiring.", "The paper company from The Office."),
        ("I'm in my origami era.", "Origami is folded paper."),
        ("Receipt so long it touches the floor.", "The endless shop receipt meme."),
        ("Folds into a plane. Flies straight at the teacher.", "A paper plane."),
    ],
    'scissors': [
        ("Snip snip. It's a crab rave tonight.", "Crab Rave: claws snip like scissors."),
        ("Edward ____hands sends his regards.", "Edward Scissorhands."),
        ("Mom said don't run with these.", "'Don't run with scissors!'"),
        ("Peace sign. But make it dangerous.", "The scissors hand is a peace sign."),
        ("Barber at 3am: 'just a little trim'.", "Haircut fail memes. Scissors."),
        ("Me cutting off toxic people:", "The 'cutting people off' meme."),
        ("Mr. Krabs is waving at you.", "Crab claws work like scissors."),
        ("Ribbon? Cut. Ceremony? Started.", "Ribbon cutting needs scissors."),
    ],
}

# the key is the move that is ruled OUT
NOT_RIDDLES = {
    'rock': [
        ("Hard pass. Literally.", "Not the hard one. Not rock."),
        ("The Rock blinked first.", "The Rock backed down. Not rock."),
        ("Patrick Star moved out.", "Nobody under the rock today. Not rock."),
        ("No stones were thrown today.", "Not rock."),
    ],
    'paper': [
        ("Never gonna give you up. Never gonna fold.", "Rickroll. Never gonna fold: not paper."),
        ("Paperless office. Finally.", "Not paper."),
        ("The printer is jammed. Again.", "No paper coming out. Not paper."),
        ("Michael Scott has left the building.", "The Office's paper boss is gone. Not paper."),
    ],
    'scissors': [
        ("Drake says no to sharp things.", "Drake meme: no sharp things. Not scissors."),
        ("Mom says running is fine today.", "No scissors to run with. Not scissors."),
        ("Crab rave cancelled.", "No crab claws. Not scissors."),
        ("No snip snip today.", "Not scissors."),
    ],
}

# how each difficulty gives hints: (chance a round has a riddle, chance it's a NOT riddle)
HINT_RULES = {
    'easy': (1.0, 0.0),      # a riddle pointing at the move, every round
    'normal': (1.0, 0.4),    # every round, sometimes a NOT riddle
    'hard': (0.6, 1.0),      # only NOT riddles, and not every round
}


class RiddleBox:
    """Hands out riddles without repeating one until the whole list is used."""

    def __init__(self):
        self.used = set()

    def _pick(self, options):
        fresh = [r for r in options if r not in self.used] or options
        riddle = random.choice(fresh)
        self.used.add(riddle)
        return riddle

    def hint(self, plan, level):
        """Returns (text, explanation) about the CPU's planned move, or None."""
        chance, not_chance = HINT_RULES[level]
        if random.random() >= chance:
            return None
        if random.random() < not_chance:
            ruled_out = random.choice([m for m in RIDDLES if m != plan])
            text, why = self._pick(NOT_RIDDLES[ruled_out])
        else:
            text, why = self._pick(RIDDLES[plan])
            why = f"{plan.upper()}. {why}"
        return text, why

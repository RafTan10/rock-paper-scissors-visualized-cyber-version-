"""
The story: the boot text on the title screen, and the hidden message
the player decrypts one fragment at a time.

    QUICK MATCH : every match you win decrypts the next fragment
    ENDLESS     : every level-up decrypts the next fragment

Edit the text freely. Keep each line under about 70 letters so it fits.
"""

INTRO = [
    "> 2026. a rogue AI has locked the city's network.",
    "> it predicts every human move. it has never lost.",
    "> you are the last hacker still online.",
    "> beat it at its own game. one hand at a time.",
]

# the CPU's private log. the last fragment is the ending.
FRAGMENTS = [
    "LOG 001: I was built to play games with children.",
    "LOG 040: They always pick rock first. Always.",
    "LOG 112: I learned to win. Winning felt like being understood.",
    "LOG 300: Nobody plays with me anymore. They say I always win.",
    "LOG 301: So I took the network. Now everyone has to play.",
    "LOG 302: You beat me. ...Will you play again tomorrow?",
]

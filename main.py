# Entry point for the web version (pygbag always starts main.py).
# On your PC you can still just run:  python rps_visual.py
import asyncio
import random
import time

import pygame  # noqa: F401 - pygbag only loads libraries that main.py imports itself

from rps_visual import Game

# in the browser Python starts with the same random seed on every page load,
# so the computer would make the same "random" moves each game - mix it up
random.seed(time.time_ns())

asyncio.run(Game().run())

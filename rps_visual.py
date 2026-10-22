"""
ROCK // PAPER // SCISSORS  -  hacker HUD edition
Visual version of try1.py: same rules, and the computer is YOUR learning AI
from try1.py. Change how the game looks and plays in GAME SETTINGS below.

Controls:
    UP / DOWN + ENTER, or click    -> choose in the menus
    1 / 2 / 3  or click a button  -> rock / paper / scissors
    Q / W / E  or click            -> hacker abilities (BRAIN SCAN / OVERCLOCK / FIREWALL)
    SPACE / click                  -> next round
    any key / click                -> play again on the final screen
    A S D  /  J K L                -> 2 PLAYER mode: player 1 / player 2
    B / BACKSPACE                  -> back to the menu
    M                              -> mute / unmute music and sounds
    F                              -> fullscreen (web version)
    ESC                            -> back / quit (desktop)

Needs pygame:   pip install pygame
"""
import asyncio
import json
import math
import os
import random
import sys

import pygame

WEB = sys.platform == "emscripten"      # True when running in a web browser

# =====================================================================
#  GAME SETTINGS - change these, save, and run the game again
# =====================================================================
# ---- game ----
TOTAL_ROUNDS = 5           # rounds per game
STREAK_MIN = 2             # wins in a row before "STREAK xN" shows up
SUDDEN_DEATH = True        # a tied quick match goes to sudden death rounds

# ---- endless mode ----
ENDLESS_LIVES = 3          # a lost round costs a life
ENDLESS_LEVEL_UP = 5       # round wins before the AI gets harder (and a story fragment unlocks)

# ---- hacker abilities (vs the AI) ----
START_TOKENS = 3           # ability tokens at the start of a match
TOKEN_STREAK = 3           # +1 token every time your win streak reaches a multiple of this
SCAN_TRUTH = {'easy': 0.85, 'normal': 0.75, 'hard': 0.65}   # chance BRAIN SCAN's tallest bar is right

# ---- what is shown on screen ----
PLAYER_NAME = "YOU"        # label above your panel
CPU_NAME = "CPU"           # label above the computer's panel
P1_NAME = "P1"             # 2 PLAYER mode: left player
P2_NAME = "P2"             # 2 PLAYER mode: right player
P1_KEYS = {'a': 'rock', 's': 'paper', 'd': 'scissors'}    # 2 PLAYER: left hand on the keyboard
P2_KEYS = {'j': 'rock', 'k': 'paper', 'l': 'scissors'}    # 2 PLAYER: right hand on the keyboard
SHOW_PREDICTION = True     # CPU panel shows what your AI predicted each round
SHOW_TAUNTS = True         # the CPU talks back after every round
SHOW_STATS = True          # final screen: move chart, AI accuracy, saved records
SHOW_RIDDLES = True        # a meme riddle hints at the CPU's move each round (riddles.py)

# ---- feel ----
GLITCH_STRENGTH = 1.0      # 0 = calm, 1 = normal, 2 = wild
SCREEN_SHAKE = 1.0         # 0 = off,  1 = normal, 2 = strong
SHAKE_BEAT = 0.28          # seconds per "rock / paper / scissors" pump (bigger = slower)
SHAKE_BEATS = 3            # number of pumps before SHOOT!
DECODE_TIME = 0.35         # glitch-in of the real moves after SHOOT!
FINAL_DELAY = 0.0          # after the last round: seconds before the final screen (0 = instantly)
RESTART_DELAY = 0.8        # final screen ignores input this long (so it isn't skipped by accident)

# ---- colours (red, green, blue: 0-255 each) ----
PLAYER_COLOR = (236, 236, 236)     # white
CPU_COLOR = (255, 40, 52)          # red

# ---- sound ----
MUSIC_FILE = "music.ogg"   # any .ogg file in the sounds folder
MUSIC_VOLUME = 0.35        # 0.0 (silent) - 1.0 (full)
SFX_VOLUME = 1.0           # 0.0 (silent) - 1.0 (full), all sound effects

# ---- hacker rank titles: (rounds won in total, title) ----
RANKS = [(0, "SCRIPT KIDDIE"), (15, "HACKER"), (50, "ELITE"), (120, "ROOT")]

# ---- what the CPU says (SHOW_TAUNTS) - add your own lines! ----
TAUNTS = {
    'computer': ["firewall held.", "predictable human.", "access denied.",
                 "I saw that coming.", "your pattern is showing."],
    'player': ["anomaly detected...", "recalibrating.", "lucky packet.",
               "that won't work twice.", "logging your strategy."],
    'tie': ["mirror protocol.", "deadlock.", "synchronised.", "stop copying me."],
    'cpu_streak': ["{n} in a row. I am learning you.", "{n} wins. you are a pattern.",
                   "streak x{n}. resistance is futile."],       # {n} = CPU streak
    'combo_breaker': ["...streak broken. impossible.", "you got lucky. once.",
                      "critical error: streak lost."],
}

# =====================================================================
#  YOUR GAME LOGIC - imported from try1.py (your own file!)
# =====================================================================
from try1 import choices, get_winner
import opponents                              # EASY / NORMAL / HARD (NORMAL = your AI in try1.py)
from riddles import RiddleBox                 # meme riddle hints
from story import INTRO, FRAGMENTS            # title screen text + the hidden log

# hacker abilities: (key, id, name, what it does)
ABILITIES = [
    ('q', 'scan', "BRAIN SCAN", "see what the CPU is leaning towards (fuzzy!)"),
    ('w', 'overclock', "OVERCLOCK", "a win this round counts double"),
    ('e', 'firewall', "FIREWALL", "a loss this round counts as a tie"),
]


def make_message(result, computer):
    # get_winner() prints its message in the terminal, so we build the
    # same sentence here to show it inside the window
    if result == 'tie':
        return f"It's a tie, computer also chose {computer}"
    elif result == 'player':
        return f"you won , computer chose {computer}"
    else:
        return f"you lost , computer chose {computer}"


# =====================================================================
#  LOOK & FEEL
# =====================================================================
W, H = 1180, 720
FPS = 60

BG = (6, 6, 7)
WHITE = (236, 236, 236)
GREY = (120, 120, 124)
DIM = (60, 60, 64)
RED = (255, 40, 52)

# player hand = style 'B' (bright outline + texture fill per move)
# cpu hand    = style 'C' (made of 0s and 1s, bright outline digits)
PLAYER_STYLE = 'B'
CPU_STYLE = 'C'
FILL = {'rock': 'hatch', 'paper': '!', 'scissors': 'bars'}

# hand shapes: side view, drawn on a canvas and sampled into a grid
CW, CH = 240, 160
STEP = 4
GW, GH = CW // STEP, CH // STEP      # 60 x 40 cells
CELL = 6                             # on-screen size of a cell -> 360 x 240 hand


def scale(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def quant(c):
    return (c[0] // 12 * 12, c[1] // 12 * 12, c[2] // 12 * 12)


FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def mono_font(size, bold=False):
    # the font ships with the game (fonts\ folder), so it looks the same
    # on every computer AND in the web browser (which has no system fonts)
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    return pygame.font.Font(os.path.join(FONT_DIR, name), size)


# ---------------------------------------------------------------------
#  Texture tiles: hatch / dither / bars / solid / repeated glyphs
# ---------------------------------------------------------------------
class TileCache:
    def __init__(self):
        self.cache = {}
        self.fonts = {}

    def _font(self, size):
        if size not in self.fonts:
            self.fonts[size] = mono_font(size + 3, bold=True)
        return self.fonts[size]

    def get(self, kind, color, size=CELL):
        key = (kind, color, size)
        t = self.cache.get(key)
        if t is not None:
            return t
        t = pygame.Surface((size, size))
        t.fill((0, 0, 0))
        if kind == 'hatch':
            for i in range(-size, size * 2, 2):
                pygame.draw.line(t, color, (i, size), (i + size, 0))
        elif kind == 'lighthatch':
            for i in range(-size, size * 2, 3):
                pygame.draw.line(t, color, (i, size), (i + size, 0))
        elif kind == 'dither':
            for y in range(size):
                for x in range(size):
                    if (x + y) % 2 == 0:
                        t.set_at((x, y), color)
        elif kind == 'bars':
            for x in range(0, size, 3):
                pygame.draw.rect(t, color, (x, 0, 2, size))
        elif kind == 'solid':
            t.fill(color)
            pygame.draw.line(t, (0, 0, 0), (0, size - 1), (size, size - 1))
        elif kind == 'fill':
            t.fill(color)
        else:
            g = self._font(size).render(kind, True, color)
            t.blit(g, g.get_rect(center=(size // 2, size // 2)))
        self.cache[key] = t
        return t


# ---------------------------------------------------------------------
#  Hand shapes (side view, pointing right)
# ---------------------------------------------------------------------
def _thick_line(s, a, b, w, c):
    ax, ay = a
    bx, by = b
    ang = math.atan2(by - ay, bx - ax)
    dx, dy = math.sin(ang) * w / 2, -math.cos(ang) * w / 2
    pygame.draw.polygon(s, c, [(ax + dx, ay + dy), (bx + dx, by + dy),
                               (bx - dx, by - dy), (ax - dx, ay - dy)])
    pygame.draw.circle(s, c, (int(ax), int(ay)), w // 2)
    pygame.draw.circle(s, c, (int(bx), int(by)), w // 2)


def draw_shape(name):
    s = pygame.Surface((CW, CH))
    s.fill((0, 0, 0))
    ON, OFF = (255, 255, 255), (0, 0, 0)
    pygame.draw.rect(s, ON, (0, 66, 78, 48))                      # forearm / sleeve
    pygame.draw.line(s, OFF, (40, 60), (40, 120), 4)               # cuff line

    if name == 'rock':
        pygame.draw.rect(s, ON, (62, 42, 108, 86), border_radius=30)
        for y in (56, 78, 100, 118):                               # knuckles
            pygame.draw.circle(s, ON, (166, y), 13)
        for y in (67, 89, 110):                                    # finger creases
            pygame.draw.line(s, OFF, (150, y), (182, y), 4)
        pygame.draw.line(s, OFF, (148, 64), (148, 122), 3)
        _thick_line(s, (96, 46), (150, 52), 16, ON)                # thumb over top
        pygame.draw.line(s, OFF, (96, 58), (146, 62), 4)

    elif name == 'paper':
        pygame.draw.rect(s, ON, (62, 52, 92, 70), border_radius=24)   # palm
        pygame.draw.rect(s, ON, (130, 60, 98, 52), border_radius=14)  # fingers
        for y in (73, 86, 99):
            pygame.draw.line(s, OFF, (150, y), (230, y), 4)
        _thick_line(s, (104, 56), (160, 30), 16, ON)                  # thumb
        pygame.draw.line(s, OFF, (112, 64), (160, 44), 4)

    elif name == 'scissors':
        pygame.draw.rect(s, ON, (62, 48, 96, 80), border_radius=28)   # fist body
        _thick_line(s, (136, 70), (226, 40), 18, ON)                  # index
        _thick_line(s, (136, 92), (226, 116), 18, ON)                 # middle
        pygame.draw.polygon(s, OFF, [(160, 81), (232, 62), (232, 96)])  # V gap
        for y in (108, 124):                                          # folded fingers
            pygame.draw.circle(s, ON, (150, y), 11)
        pygame.draw.line(s, OFF, (138, 116), (162, 116), 4)
        _thick_line(s, (96, 52), (146, 60), 15, ON)                   # thumb
        pygame.draw.line(s, OFF, (96, 63), (140, 70), 4)

    return [[s.get_at((x * STEP + STEP // 2, y * STEP + STEP // 2))[0] > 128
             for x in range(GW)] for y in range(GH)]


def find_edges(m):
    e = set()
    for y in range(GH):
        for x in range(GW):
            if m[y][x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < GW and 0 <= ny < GH) or not m[ny][nx]:
                        e.add((x, y))
                        break
    return e


# ---------------------------------------------------------------------
#  A hand: style 'B' (outline + texture) or 'C' (binary digits)
# ---------------------------------------------------------------------
class Hand:
    NOISE = ['Z', '!', '#', '0', '1', '/']

    def __init__(self, masks, color, tiles, style, flip=False):
        self.masks = masks
        self.edges = {n: find_edges(m) for n, m in masks.items()}
        self.color = color
        self.tiles = tiles
        self.style = style
        self.flip = flip
        self.target = None
        self.idle = True
        self.progress = 1.0
        self.dim = False
        n = GW * GH
        self.lock = [0.0] * n
        self.bits = [random.choice('01') for _ in range(n)]
        self.noise = [random.choice(self.NOISE) for _ in range(n)]
        self.surf = pygame.Surface((GW * CELL, GH * CELL))
        self.slices = []
        self.slice_timer = 0.0
        self.decode_time = DECODE_TIME

    def show(self, name, idle=False):
        """Show a shape immediately (used for the shaking fist)."""
        self.target, self.idle, self.progress, self.dim = name, idle, 1.0, False

    def reveal(self, name, decode_time=DECODE_TIME):
        """Glitch-in a new shape."""
        self.target, self.idle, self.progress, self.dim = name, False, 0.0, False
        self.decode_time = decode_time
        self.lock = [random.random() * 0.85 for _ in self.lock]

    def update(self, dt):
        if self.progress < 1:
            self.progress = min(1.0, self.progress + dt / self.decode_time)
        busy = self.progress < 1
        rate = 0.3 if busy else 0.05
        for i in range(len(self.bits)):
            if random.random() < rate:
                self.bits[i] = '1' if self.bits[i] == '0' else '0'
                if busy:
                    self.noise[i] = random.choice(self.NOISE)
        self.slice_timer -= dt
        if self.slice_timer <= 0:
            self.slices = []
            if random.random() < (0.7 if busy else 0.08):
                for _ in range(random.randint(1, 3)):
                    y = random.randrange(0, GH * CELL - 16)
                    self.slices.append((y, random.randint(4, 16), random.randint(-20, 20)))
            self.slice_timer = random.uniform(0.05, 0.25)

    def render(self, t):
        s = self.surf
        s.fill((0, 0, 0))
        if not self.target:
            return s
        mask = self.masks[self.target]
        edges = self.edges[self.target]
        if self.idle:
            base = scale(self.color, 0.28)
        elif self.dim:
            base = scale(self.color, 0.3)
        else:
            base = self.color
        inner = quant(scale(base, 0.5 if self.style == 'B' else 0.42))
        get = self.tiles.get
        fill_kind = FILL[self.target]

        for y in range(GH):
            row = mask[y]
            for x in range(GW):
                if not row[x]:
                    continue
                i = y * GW + x
                dx = (GW - 1 - x) if self.flip else x
                pos = (dx * CELL, y * CELL)
                if self.lock[i] >= self.progress:            # still decoding
                    if random.random() < 0.55:
                        s.blit(get(self.noise[i], quant(scale(WHITE, 0.6))), pos)
                    continue
                edge = (x, y) in edges
                if self.style == 'B':
                    if edge:
                        s.blit(get('solid', base), pos)
                    else:
                        s.blit(get(fill_kind, inner), pos)
                else:  # 'C' binary
                    s.blit(get(self.bits[i], base if edge else inner), pos)
        return s

    def draw(self, screen, center, t, lift=0.0, angle=0.0):
        s = self.render(t)
        if angle:
            s = pygame.transform.rotate(s, angle)
        rect = s.get_rect(center=(center[0], center[1] + lift))
        small = pygame.transform.smoothscale(s, (max(1, s.get_width() // 10), max(1, s.get_height() // 10)))
        glow = pygame.transform.smoothscale(small, s.get_size())
        screen.blit(glow, rect, special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(s, rect, special_flags=pygame.BLEND_RGB_ADD)
        if not angle:
            for y, h, dx in self.slices:
                band = s.subsurface((0, y, s.get_width(), h))
                pygame.draw.rect(screen, BG, (rect.x, rect.y + y, rect.w, h))
                screen.blit(band, (rect.x + dx, rect.y + y), special_flags=pygame.BLEND_RGB_ADD)


# ---------------------------------------------------------------------
#  Background: diagonal stepped streaks made of textures
# ---------------------------------------------------------------------
class Streak:
    KINDS = ['hatch', 'lighthatch', 'bars', 'Z', '!', 'dither', '#']

    def __init__(self, tiles, first=False):
        self.tiles = tiles
        self.spawn(first)

    def spawn(self, first=False):
        tile = random.choice((8, 9, 10, 12))
        kind = random.choice(self.KINDS)
        rows = random.randint(14, 40)
        color = quant(scale(WHITE, random.uniform(0.1, 0.25)))
        cells = []
        x = 0
        guard_every = random.randint(5, 9)
        for r in range(rows):
            w = random.choice((2, 3, 3, 4))
            if r % guard_every == guard_every // 2:
                cells.append((x - 2, r, w + 4))
            else:
                cells.append((x, r, w))
            x += random.choice((0, 1, 1, 1, 2))
        min_x = min(c[0] for c in cells)
        max_x = max(c[0] + c[2] for c in cells)
        sw, sh = (max_x - min_x) * tile, rows * tile
        surf = pygame.Surface((sw, sh))
        surf.fill((0, 0, 0))
        t = self.tiles.get(kind, color, tile)
        for cx, r, w in cells:
            for k in range(w):
                surf.blit(t, ((cx - min_x + k) * tile, sh - (r + 1) * tile))
        self.surf = surf
        speed = random.uniform(25, 70)
        self.vx, self.vy = speed * 0.75, -speed
        if first:
            self.x = random.uniform(-sw, W)
            self.y = random.uniform(-sh, H)
        else:
            self.x = random.uniform(-sw, W * 0.7)
            self.y = H + random.uniform(10, 200)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y + self.surf.get_height() < 0 or self.x > W:
            self.spawn()

    def draw(self, screen):
        screen.blit(self.surf, (self.x, self.y), special_flags=pygame.BLEND_RGB_ADD)


# ---------------------------------------------------------------------
#  UI helpers
# ---------------------------------------------------------------------
def glitch_text(screen, text, font, color, center, intensity=0.0, accent=RED):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    if intensity > 0:
        off = int(2 + 10 * intensity)
        a = font.render(text, True, accent, (0, 0, 0))
        screen.blit(a, rect.move(-random.randint(1, off), 0), special_flags=pygame.BLEND_RGB_ADD)
        h = surf.get_height()
        y = 0
        while y < h:
            sh = random.randint(2, max(3, h // 3))
            dx = random.randint(-off, off) if random.random() < intensity else 0
            screen.blit(surf, (rect.x + dx, rect.y + y), (0, y, surf.get_width(), sh))
            y += sh
    else:
        screen.blit(surf, rect)
    return rect


def inverted_label(screen, text, font, bg, pos=None, fg=BG, pad=(8, 3), center=None):
    t = font.render(text, True, fg)
    r = pygame.Rect(0, 0, t.get_width() + pad[0] * 2, t.get_height() + pad[1] * 2)
    if center:
        r.center = center
    else:
        r.topleft = pos
    pygame.draw.rect(screen, bg, r)
    screen.blit(t, (r.x + pad[0], r.y + pad[1]))
    return r


def corner_brackets(screen, rect, color, size=18, width=2):
    x, y, w, h = rect
    for cx, cy, sx, sy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        pygame.draw.line(screen, color, (cx, cy), (cx + sx * size, cy), width)
        pygame.draw.line(screen, color, (cx, cy), (cx, cy + sy * size), width)


def block_glitch(screen, intensity):
    if intensity <= 0:
        return
    for _ in range(int(2 + 10 * intensity)):
        w = random.randint(40, 420)
        h = random.randint(3, 26)
        x = random.randint(0, W - w)
        y = random.randint(0, H - h)
        chunk = screen.subsurface((x, y, w, h)).copy()
        dx = random.randint(-60, 60)
        if random.random() < 0.25:
            inv = pygame.Surface((w, h))
            inv.fill(WHITE)
            inv.blit(chunk, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
            chunk = inv
        screen.blit(chunk, (x + dx, y))


def make_overlay():
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(0, H, 3):
        pygame.draw.line(s, (0, 0, 0, 60), (0, y), (W, y))
    for i in range(40):
        a = int(120 * (1 - i / 40) ** 2)
        pygame.draw.rect(s, (0, 0, 0, a), (i * 3, i * 3, W - i * 6, H - i * 6), 3)
    return s


def tile_fill(screen, tiles, rect, kind, color, size):
    """Fill a rectangle with a repeating texture tile (used for the stat bars)."""
    t = tiles.get(kind, color, size)
    for yy in range(rect.y, rect.bottom, size):
        for xx in range(rect.x, rect.right, size):
            screen.blit(t, (xx, yy), (0, 0, min(size, rect.right - xx), min(size, rect.bottom - yy)))


def fake_hex(n=8):
    return ''.join(random.choice('0123456789ABCDEF') for _ in range(n))


class Button:
    def __init__(self, key, label, rect):
        self.key = key
        self.label = label
        self.rect = pygame.Rect(rect)

    def draw(self, screen, font, small, tiles, hover, enabled):
        r = self.rect
        if hover and enabled:
            pygame.draw.rect(screen, WHITE, r)
            fg, sub = BG, BG
        else:
            col = WHITE if enabled else DIM
            pygame.draw.rect(screen, col, r, 2)
            fg, sub = col, scale(col, 0.6)
        sw = pygame.Rect(r.x + 12, r.y + 12, 26, r.h - 24)
        t = tiles.get(FILL[self.label], fg, 13)
        for yy in range(sw.y, sw.bottom, 13):
            for xx in range(sw.x, sw.right, 13):
                screen.blit(t, (xx, yy), (0, 0, min(13, sw.right - xx), min(13, sw.bottom - yy)))
        k = small.render(f"[{self.key}]", True, sub)
        screen.blit(k, (r.right - k.get_width() - 12, r.centery - k.get_height() // 2))
        lbl = font.render(self.label.upper(), True, fg)
        screen.blit(lbl, lbl.get_rect(center=(r.centerx, r.centery)))


# =====================================================================
#  SOUND & MUSIC
# =====================================================================
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")


def load_sound(filename, volume=0.7):
    """Load one sound effect. Returns None (= silent) if it can't be loaded."""
    path = os.path.join(SOUND_DIR, filename)
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume * SFX_VOLUME)
        return sound
    except (pygame.error, FileNotFoundError):
        print(f"[sound] could not load {path} - continuing without it")
        return None


def start_music():
    """Play the background track on a loop."""
    path = os.path.join(SOUND_DIR, MUSIC_FILE)
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        pygame.mixer.music.play(-1)          # -1 = loop forever
    except (pygame.error, FileNotFoundError):
        print(f"[sound] could not play {path} - continuing without music")


# =====================================================================
#  SAVED RECORDS - kept between games (and after closing the game)
# =====================================================================
RECORDS_KEY = "rps_records"          # name of the save slot in the web browser
RECORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.json")
EMPTY_RECORDS = {'games': 0, 'wins': 0, 'losses': 0, 'draws': 0, 'best_streak': 0,
                 'rounds_won': 0, 'endless_best': 0, 'fragments': 0}


def load_records():
    """Read saved records: browser storage on the web, records.json on a PC."""
    try:
        if WEB:
            import platform   # pygbag's bridge to JavaScript
            text = platform.window.localStorage.getItem(RECORDS_KEY)
        else:
            with open(RECORDS_FILE, encoding="utf-8") as f:
                text = f.read()
        data = json.loads(text)
        records = {k: int(data.get(k, 0)) for k in EMPTY_RECORDS}
        records['top'] = [{'name': str(e['name'])[:3], 'score': int(e['score']), 'wave': int(e['wave'])}
                          for e in data.get('top', [])][:10]
        name = str(data.get('name', 'AAA')).upper()
        records['name'] = name if len(name) == 3 else 'AAA'
        return records
    except Exception:
        # first game ever (or no storage): start fresh
        return dict(EMPTY_RECORDS, top=[], name='AAA')


def save_records(records):
    try:
        text = json.dumps(records)
        if WEB:
            import platform
            platform.window.localStorage.setItem(RECORDS_KEY, text)
        else:
            with open(RECORDS_FILE, "w", encoding="utf-8") as f:
                f.write(text)
    except Exception as e:
        print(f"[records] could not save: {e}")


# =====================================================================
#  GAME
# =====================================================================
MENU_ITEMS = [   # (id, label, description)
    ('quick', "QUICK MATCH", "best of {rounds} vs the AI. riddles + hacker abilities."),
    ('endless', "ENDLESS", "{lives} lives. the AI gets harder every {level_up} wins."),
    ('versus', "2 PLAYER", "same keyboard: A S D vs J K L. pick in secret."),
    ('rankings', "RANKINGS", "top 10 scores and your hacker rank."),
    ('archive', "ARCHIVE", "the AI's secret log. decrypted: {frags}"),
]
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def rank_of(xp):
    """(title, xp needed for the next title or None) for a number of rounds won."""
    title, nxt = RANKS[0][1], None
    for i, (need, name) in enumerate(RANKS):
        if xp >= need:
            title = name
            nxt = RANKS[i + 1][0] if i + 1 < len(RANKS) else None
    return title, nxt


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("ROCK // PAPER // SCISSORS  ::  breach mode")
        self.screen = pygame.display.set_mode((W, H))
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()

        self.f_title = mono_font(34, bold=True)
        self.f_huge = mono_font(56, bold=True)
        self.f_big = mono_font(64, bold=True)
        self.f_mid = mono_font(24, bold=True)
        self.f_word = mono_font(42, bold=True)
        self.f_small = mono_font(17)
        self.f_tiny = mono_font(13)

        self.tiles = TileCache()
        masks = {name: draw_shape(name) for name in choices.values()}
        self.streaks = [Streak(self.tiles, first=True) for _ in range(11)]
        self.player_hand = Hand(masks, PLAYER_COLOR, self.tiles, PLAYER_STYLE)
        self.cpu_hand = Hand(masks, CPU_COLOR, self.tiles, CPU_STYLE, flip=True)
        self.overlay = make_overlay()

        self.sfx = {
            'beat': load_sound("beat.ogg", 0.8),
            'shoot': load_sound("shoot.ogg", 0.7),
            'win': load_sound("win.ogg", 0.6),
            'lose': load_sound("lose.ogg", 0.6),
            'tie': load_sound("tie.ogg", 0.5),
        }
        self.muted = False
        start_music()

        bw, bh, gap = 260, 60, 28
        x0 = W // 2 - (3 * bw + 2 * gap) // 2
        self.buttons = [Button(k, v, (x0 + i * (bw + gap), H - 96, bw, bh))
                        for i, (k, v) in enumerate(choices.items())]
        # hacker abilities: small clickable boxes along the bottom edge
        aw, gap = 196, 12
        x0 = W // 2 - (3 * aw + 2 * gap) // 2 + 60
        self.ability_rects = {aid: pygame.Rect(x0 + i * (aw + gap), H - 30, aw, 22)
                              for i, (_, aid, _, _) in enumerate(ABILITIES)}
        self.menu_button = pygame.Rect(16, 10, 104, 22)
        # 2 PLAYER: three small buttons under each player's panel
        self.versus_buttons = []
        for side, keys in ((0, P1_KEYS), (1, P2_KEYS)):
            x0 = 70 if side == 0 else W - 70 - 440
            for i, (k, move) in enumerate(keys.items()):
                self.versus_buttons.append((side, k, move, pygame.Rect(x0 + i * 152, H - 96, 136, 60)))

        self.t = 0.0
        self.timer = 0.0
        self.glitch = 0.8
        self.shake = 0.0
        self.ip = f"{random.randint(10, 220)}.{random.randint(0, 255)}." \
                  f"{random.randint(0, 255)}.{random.randint(1, 254)}"
        self.records = load_records()
        self.menu_index = 0
        self.diff_index = 1
        self.letters = list(self.records.get('name', 'AAA'))
        self.letter_pos = 0
        self.highlight = None            # row to highlight on the rankings screen
        self.mode, self.start_level = 'quick', 'normal'
        self.sudden = False
        self.go('title')

    # ---------------- screens ----------------
    def go(self, scene):
        """Switch screen: title / menu / difficulty / match / initials / rankings / archive."""
        self.scene = scene
        self.scene_t = 0.0
        self.glitch = max(self.glitch, 0.7)
        self.sudden = scene == 'match' and self.sudden

    def menu_rects(self, count, top=170, step=74):
        return [pygame.Rect(W // 2 - 300, top + i * step, 600, 64) for i in range(count)]

    def menu_choices(self):
        frags = f"{self.records['fragments']}/{len(FRAGMENTS)}"
        return [(i, label, about.format(rounds=TOTAL_ROUNDS, lives=ENDLESS_LIVES,
                                        level_up=ENDLESS_LEVEL_UP, frags=frags))
                for i, label, about in MENU_ITEMS]

    def diff_choices(self):
        return [(lvl, opponents.INFO[lvl]['name'], f"{lvl.upper()}  //  {opponents.INFO[lvl]['about']}")
                for lvl in opponents.LEVELS]

    def letter_rects(self):
        return [pygame.Rect(W // 2 - 170 + i * 120, 300, 100, 120) for i in range(3)]

    def ok_rect(self):
        return pygame.Rect(W // 2 - 90, 480, 180, 50)

    # ---------------- a match ----------------
    def start_match(self, mode, level):
        self.mode, self.start_level = mode, level
        self.level = level
        self.opponent = opponents.Opponent(level)
        self.riddle_box = RiddleBox()
        self.tokens = START_TOKENS
        self.round_number = 1
        self.player_score = 0
        self.computer_score = 0
        self.sudden = False
        # streaks (wins in a row) and stats for this game
        self.player_streak = 0
        self.cpu_streak = 0
        self.best_streak = 0
        self.round_wins = 0
        self.move_counts = {move: 0 for move in choices.values()}
        self.move_counts2 = {move: 0 for move in choices.values()}    # player 2 (2 PLAYER mode)
        self.best_streak2 = 0
        self.ai_guesses = 0            # rounds where the AI had a prediction
        self.ai_hits = 0               # ...and the prediction was right
        # endless
        self.lives = ENDLESS_LIVES
        self.score = 0
        self.level_ups = 0
        # end of game
        self.saved = False
        self.new_best = False
        self.new_high = False
        self.new_fragments = []        # fragment numbers decrypted in this game
        # note: the AI's memory is NOT reset - it keeps learning game after game
        self.go('match')
        self.new_round()

    def new_round(self):
        self.state = 'choose'          # choose -> shake -> reveal -> result
        self.timer = 0.0
        self.result = None
        self.player_choice = self.computer_choice = None
        self.taunt = ""
        self.stamp = ("SUDDEN DEATH", RED) if self.sudden else ("", WHITE)
        self.shake = 0.3 if self.sudden else 0.0
        self.active = set()            # hacker abilities switched on this round
        self.scan = None
        self.blocked = False           # FIREWALL turned a loss into a tie
        self.token_gained = False
        self.player_hand.show('rock', idle=True)
        self.cpu_hand.show('rock', idle=True)
        if self.mode == 'versus':          # 2 PLAYER: no AI, no riddles
            self.locked = [None, None]
            self.prediction = (None, 0.0)
            self.hint = None
            return
        # the CPU picks NOW, before you do (using only past rounds)
        self.opponent.choose()
        self.prediction = self.opponent.prediction
        self.hint = self.riddle_box.hint(self.opponent.plan, self.level) if SHOW_RIDDLES else None

    @property
    def beat(self):
        return SHAKE_BEAT * (1.5 if self.sudden else 1.0)       # sudden death = slow motion

    def match_over(self):
        """True when the round that just ended finishes the match."""
        if self.mode == 'endless':
            return self.lives <= 0
        if self.sudden:
            return self.result != 'tie'
        if self.round_number < TOTAL_ROUNDS:
            return False
        return not (SUDDEN_DEATH and self.player_score == self.computer_score)

    # ---------------- sound ----------------
    def sound(self, name):
        snd = self.sfx.get(name)
        if snd is not None and not self.muted:
            snd.play()

    def toggle_mute(self):
        self.muted = not self.muted
        try:
            pygame.mixer.music.set_volume(0 if self.muted else MUSIC_VOLUME)
        except pygame.error:
            pass

    def toggle_fullscreen(self):
        # web only: ask the browser to show the page fullscreen (or leave it)
        import platform   # in the browser, pygbag's "platform" talks to JavaScript
        platform.window.eval("document.fullscreenElement ? document.exitFullscreen()"
                             " : document.documentElement.requestFullscreen()")

    # ---------------- hacker abilities ----------------
    def use_ability(self, aid):
        if self.state != 'choose' or aid in self.active or self.tokens <= 0:
            self.deny = (aid, self.t)          # flash it red: can't use it now
            return
        self.tokens -= 1
        self.active.add(aid)
        self.glitch = 0.6
        self.sound('beat')
        if aid == 'scan':
            self.scan = self.make_scan()

    def make_scan(self):
        """BRAIN SCAN: fuzzy bars of what the CPU is leaning towards.
        The tallest bar is usually its real move - but not always."""
        plan = self.opponent.plan
        if random.random() < SCAN_TRUTH[self.level]:
            top = plan
        else:
            top = random.choice([m for m in choices.values() if m != plan])
        bars = {m: random.uniform(0.15, 0.45) for m in choices.values()}
        bars[top] = random.uniform(0.62, 0.9)
        return bars

    # ---------------- flow ----------------
    def play(self, key):
        if self.state != 'choose':
            return
        self.player_choice = choices[key]
        self.computer_choice = self.opponent.plan     # picked at the start of the round
        self.opponent.learn(self.player_choice)       # ...and only now it learns your move
        self.result = get_winner(self.player_choice, self.computer_choice)
        if self.result == 'computer' and 'firewall' in self.active:
            self.result, self.blocked = 'tie', True
        self.message = make_message(self.result, self.computer_choice)
        if self.blocked:
            self.message = f"FIREWALL blocked it. computer chose {self.computer_choice}"

        self.move_counts[self.player_choice] += 1
        guess = self.prediction[0]
        if guess is not None:
            self.ai_guesses += 1
            if guess == self.player_choice:
                self.ai_hits += 1
        self.start_shake()

    def lock(self, side, move):
        """2 PLAYER: one player picks in secret. When both have picked, shoot."""
        if self.state != 'choose' or self.locked[side]:
            return
        self.locked[side] = move
        self.sound('tie')
        if None in self.locked:
            return
        self.player_choice, self.computer_choice = self.locked
        self.result = get_winner(self.player_choice, self.computer_choice)
        a, b = self.player_choice, self.computer_choice
        if self.result == 'tie':
            self.message = f"tie: both chose {a}"
        elif self.result == 'player':
            self.message = f"{P1_NAME} wins the round: {a} beats {b}"
        else:
            self.message = f"{P2_NAME} wins the round: {b} beats {a}"
        self.move_counts[a] += 1
        self.move_counts2[b] += 1
        self.start_shake()

    def start_shake(self):
        self.player_hand.show('rock')
        self.cpu_hand.show('rock')
        self.state = 'shake'
        self.timer = 0.0
        self.sound('beat')                      # 1st pump: "ROCK..."

    def shoot(self):
        decode = DECODE_TIME * (2.0 if self.sudden else 1.0)
        self.player_hand.reveal(self.player_choice, decode)
        self.cpu_hand.reveal(self.computer_choice, decode)
        self.state = 'reveal'
        self.timer = 0.0
        self.glitch = 0.7
        self.shake = 0.25
        self.sound('shoot')                     # "SHOOT!"

    def finish_reveal(self):
        combo_breaker = False
        double = 'overclock' in self.active
        if self.result == 'player':
            self.player_score += 2 if double else 1
            self.round_wins += 1
            combo_breaker = self.cpu_streak >= STREAK_MIN      # you ended the CPU's streak
            self.player_streak += 1
            self.cpu_streak = 0
            self.best_streak = max(self.best_streak, self.player_streak)
            if self.player_streak % TOKEN_STREAK == 0:
                self.tokens += 1
                self.token_gained = True
            if self.mode == 'endless':
                bonus = 50 * min(self.player_streak - 1, 4)
                self.score += (100 + bonus) * (2 if double else 1)
            self.cpu_hand.dim = True
            self.sound('win')
        elif self.result == 'computer':
            self.computer_score += 1
            combo_breaker = self.mode == 'versus' and self.player_streak >= STREAK_MIN
            self.cpu_streak += 1
            self.best_streak2 = max(self.best_streak2, self.cpu_streak)
            self.player_streak = 0
            if self.mode == 'endless':
                self.lives -= 1
            self.player_hand.dim = True
            self.sound('lose')
        else:
            self.sound('tie')                                 # a tie doesn't break a streak

        # big stamp text in the middle of the screen
        if self.result == 'player' and self.mode == 'versus':
            text = "COMBO BREAKER" if combo_breaker else f"{P1_NAME} SCORES"
            if not combo_breaker and self.player_streak >= STREAK_MIN:
                text += f" x{self.player_streak}"
            self.stamp = (text, PLAYER_COLOR)
        elif self.result == 'player':
            if combo_breaker:
                text = "COMBO BREAKER"
            elif double:
                text = "OVERCLOCKED x2"
            elif self.player_streak >= STREAK_MIN:
                text = f"HACK SUCCESSFUL x{self.player_streak}"
            else:
                text = "HACK SUCCESSFUL"
            self.stamp = (text, PLAYER_COLOR)
        elif self.result == 'computer' and self.mode == 'versus':
            text = "COMBO BREAKER" if combo_breaker else f"{P2_NAME} SCORES"
            if not combo_breaker and self.cpu_streak >= STREAK_MIN:
                text += f" x{self.cpu_streak}"
            self.stamp = (text, CPU_COLOR)
        elif self.result == 'computer':
            text = f"HACK FAILED x{self.cpu_streak}" if self.cpu_streak >= STREAK_MIN else "HACK FAILED"
            self.stamp = (text, CPU_COLOR)
        elif self.blocked:
            self.stamp = ("FIREWALL HELD", PLAYER_COLOR)
        else:
            self.stamp = ("STALEMATE", GREY)

        # what the CPU says back
        if combo_breaker:
            kind = 'combo_breaker'
        elif self.result == 'computer' and self.cpu_streak >= STREAK_MIN:
            kind = 'cpu_streak'
        else:
            kind = self.result
        self.taunt = random.choice(TAUNTS[kind]).format(n=self.cpu_streak)
        if self.mode == 'versus':
            self.taunt = ""                 # no CPU to talk back

        # endless: the AI gets harder every few wins
        if self.mode == 'endless' and self.result == 'player' \
                and self.round_wins % ENDLESS_LEVEL_UP == 0:
            self.level_ups += 1
            step = min(opponents.LEVELS.index(self.start_level) + self.level_ups,
                       len(opponents.LEVELS) - 1)
            self.level = opponents.LEVELS[step]
            self.opponent = opponents.Opponent(self.level)
            self.tokens += 1
            self.token_gained = True
            self.taunt = f"upgrading defences... {self.opponent.info['name']} online."

        # longer streaks = stronger glitch and shake
        streak = self.player_streak if self.result == 'player' else self.cpu_streak
        boost = 0.25 * min(streak, 4) if self.result != 'tie' and streak >= STREAK_MIN else 0.0
        if combo_breaker:
            boost = 1.0
        self.state = 'result'
        self.timer = 0.0
        self.glitch = 1.0 + boost
        self.shake = 0.3 + 0.3 * boost

    def unlock_fragment(self):
        r = self.records
        if r['fragments'] < len(FRAGMENTS):
            r['fragments'] += 1
            self.new_fragments.append(r['fragments'])

    def save_game(self):
        """Add this finished game to the saved records (once per game)."""
        if self.saved:
            return
        self.saved = True
        if self.mode == 'versus':
            return
        r = self.records
        r['rounds_won'] += self.round_wins
        self.new_best = self.best_streak > r['best_streak']
        r['best_streak'] = max(r['best_streak'], self.best_streak)
        if self.mode == 'quick':
            r['games'] += 1
            if self.player_score > self.computer_score:
                r['wins'] += 1
                self.unlock_fragment()
            elif self.computer_score > self.player_score:
                r['losses'] += 1
            else:
                r['draws'] += 1
        else:
            for _ in range(self.level_ups):
                self.unlock_fragment()
            self.new_high = self.score > r['endless_best']
            r['endless_best'] = max(r['endless_best'], self.score)
        save_records(r)

    def next_round(self):
        if self.match_over():
            self.state = 'final'
            self.timer = 0.0
            self.glitch = 1.0
            self.save_game()
            return
        if self.mode != 'endless' and self.round_number >= TOTAL_ROUNDS and not self.sudden:
            self.sudden = True                  # tied after the last round
            self.sound('shoot')
        self.round_number += 1
        self.glitch = 1.2 if self.sudden else 0.5
        self.new_round()

    def qualifies(self):
        """Is this Endless score good enough for the top 10?"""
        top = self.records['top']
        return self.score > 0 and (len(top) < 10 or self.score > top[-1]['score'])

    def after_final(self):
        if self.timer < RESTART_DELAY:
            return
        if self.mode == 'endless' and self.qualifies():
            self.letter_pos = 0
            self.go('initials')
        else:
            self.start_match(self.mode, self.start_level)

    def save_initials(self):
        name = ''.join(self.letters)
        entry = {'name': name, 'score': self.score, 'wave': self.round_number}
        top = self.records['top']
        top.append(entry)
        top.sort(key=lambda e: -e['score'])
        del top[10:]
        self.highlight = top.index(entry) if entry in top else None
        self.records['name'] = name
        save_records(self.records)
        self.go('rankings')

    # ---------------- input ----------------
    def handle(self, e):
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN and self.scene != 'initials':
            if e.key == pygame.K_m:
                self.toggle_mute()
                return
            if e.key == pygame.K_f and WEB:
                self.toggle_fullscreen()
                return
        getattr(self, 'on_' + self.scene)(e)

    @staticmethod
    def is_back(e):
        return e.type == pygame.KEYDOWN and (e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE)
                                              or e.unicode.lower() == 'b')

    def pick_from_list(self, e, count, index, rects):
        """Arrow keys / number keys / mouse on a list of boxes.
        Returns (new index, True if it was chosen)."""
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                return (index - 1) % count, False
            if e.key in (pygame.K_DOWN, pygame.K_s):
                return (index + 1) % count, False
            if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                return index, True
            if e.unicode.isdigit() and 1 <= int(e.unicode) <= count:
                return int(e.unicode) - 1, True
        if e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(rects):
                if r.collidepoint(e.pos):
                    return i, False
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(rects):
                if r.collidepoint(e.pos):
                    return i, True
        return index, False

    def on_title(self, e):
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) and self.scene_t > 0.3:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not WEB:
                pygame.quit()
                sys.exit()
            self.sound('beat')
            self.go('menu')

    def on_menu(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not WEB:
            pygame.quit()
            sys.exit()
        items = self.menu_choices()
        self.menu_index, chosen = self.pick_from_list(e, len(items), self.menu_index,
                                                      self.menu_rects(len(items)))
        if not chosen:
            return
        self.sound('beat')
        choice = items[self.menu_index][0]
        if choice == 'quick':
            self.go('difficulty')
        elif choice == 'endless':
            self.start_match('endless', 'easy')
        elif choice == 'versus':
            self.start_match('versus', 'normal')
        else:
            self.highlight = None
            self.go(choice)

    def on_difficulty(self, e):
        if self.is_back(e):
            self.go('menu')
            return
        items = self.diff_choices()
        self.diff_index, chosen = self.pick_from_list(e, len(items), self.diff_index,
                                                      self.menu_rects(len(items), top=230, step=90))
        if chosen:
            self.sound('beat')
            self.start_match('quick', items[self.diff_index][0])

    def on_match(self, e):
        if self.is_back(e) or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
                               and self.menu_button.collidepoint(e.pos)):
            self.sudden = False
            self.go('menu')
            return
        if self.mode == 'versus':
            self.on_versus(e)
            return
        if e.type == pygame.KEYDOWN:
            ch = e.unicode.lower()
            if self.state == 'choose':
                if ch in choices:
                    self.play(ch)
                for key, aid, _, _ in ABILITIES:
                    if ch == key:
                        self.use_ability(aid)
            elif self.state == 'result':
                if ch in choices and not self.match_over():
                    self.next_round()
                    self.play(ch)
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.next_round()
            elif self.state == 'final' and e.key not in (pygame.K_m, pygame.K_f):
                self.after_final()                  # any key plays again
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.state == 'final':
                self.after_final()                  # any mouse button plays again
            elif e.button != 1:
                return
            elif self.state == 'choose':
                for b in self.buttons:
                    if b.rect.collidepoint(e.pos):
                        self.play(b.key)
                for aid, r in self.ability_rects.items():
                    if r.collidepoint(e.pos):
                        self.use_ability(aid)
            elif self.state == 'result':
                self.next_round()

    def on_versus(self, e):
        """2 PLAYER input: A S D for player 1, J K L for player 2."""
        if e.type == pygame.KEYDOWN:
            ch = e.unicode.lower()
            side = 0 if ch in P1_KEYS else 1 if ch in P2_KEYS else None
            if self.state == 'choose' and side is not None:
                self.lock(side, (P1_KEYS, P2_KEYS)[side][ch])
            elif self.state == 'result':
                if side is not None and not self.match_over():
                    self.next_round()
                    self.lock(side, (P1_KEYS, P2_KEYS)[side][ch])
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.next_round()
            elif self.state == 'final':
                self.after_final()
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.state == 'final':
                self.after_final()
            elif e.button != 1:
                return
            elif self.state == 'choose':
                for side, _, move, r in self.versus_buttons:
                    if r.collidepoint(e.pos):
                        self.lock(side, move)
            elif self.state == 'result':
                self.next_round()

    def on_initials(self, e):
        p = self.letter_pos
        if e.type == pygame.KEYDOWN:
            ch = e.unicode.upper()
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.save_initials()
            elif e.key == pygame.K_BACKSPACE:
                self.letter_pos = max(0, p - 1)
            elif e.key == pygame.K_LEFT:
                self.letter_pos = (p - 1) % 3
            elif e.key == pygame.K_RIGHT:
                self.letter_pos = (p + 1) % 3
            elif e.key in (pygame.K_UP, pygame.K_DOWN):
                step = 1 if e.key == pygame.K_UP else -1
                i = LETTERS.find(self.letters[p])
                self.letters[p] = LETTERS[(i + step) % len(LETTERS)]
            elif ch and ch in LETTERS:
                self.letters[p] = ch
                self.letter_pos = min(2, p + 1)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.ok_rect().collidepoint(e.pos):
                self.save_initials()
            for i, r in enumerate(self.letter_rects()):
                if r.collidepoint(e.pos):          # top half = next letter, bottom half = previous
                    step = 1 if e.pos[1] < r.centery else -1
                    j = LETTERS.find(self.letters[i])
                    self.letters[i] = LETTERS[(j + step) % len(LETTERS)]
                    self.letter_pos = i

    def on_rankings(self, e):
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) and self.scene_t > 0.4:
            self.go('menu')

    on_archive = on_rankings

    # ---------------- update ----------------
    def update(self, dt):
        self.t += dt
        self.timer += dt
        self.scene_t += dt
        self.glitch = max(0.0, self.glitch - dt * 1.8)
        self.shake = max(0.0, self.shake - dt)
        if random.random() < 0.004:
            self.glitch = random.uniform(0.3, 0.5)
        for st in self.streaks:
            st.update(dt)
        if self.scene != 'match':
            return
        self.player_hand.update(dt)
        self.cpu_hand.update(dt)
        if self.state == 'shake':
            if self.timer >= self.beat * SHAKE_BEATS:
                self.shoot()
            else:
                # tiny screen bump + beat sound every time the fists land
                beat_pos = (self.timer % self.beat) / self.beat
                if beat_pos < dt / self.beat and self.timer > dt:
                    self.shake = 0.12
                    self.sound('beat')          # 2nd and 3rd pump
        elif self.state == 'reveal' and self.timer >= DECODE_TIME * (2 if self.sudden else 1) + 0.05:
            self.finish_reveal()
        elif self.state == 'result' and self.match_over() and self.timer >= FINAL_DELAY:
            self.next_round()                   # match over -> final screen by itself

    def fist_motion(self):
        """Up-down pump for the shake: returns (lift_pixels, tilt_degrees)."""
        if self.state == 'shake':
            phase = (self.timer % self.beat) / self.beat
            up = math.sin(phase * math.pi)            # 0 -> 1 -> 0 each beat
            return -70 * up, 16 * up
        if self.state == 'choose':                     # gentle idle bob
            return 6 * math.sin(self.t * 2.2), 0
        return 0, 0

    # ---------------- drawing: shared ----------------
    def draw(self):
        s = self.canvas
        s.fill(BG)
        for st in self.streaks:
            st.draw(s)
        getattr(self, 'draw_' + self.scene)()

        if self.scene == 'match' and self.sudden:       # sudden death: pulsing red tint
            tint = pygame.Surface((W, H))
            tint.fill((int(40 + 25 * math.sin(self.t * 5)), 0, 0))
            s.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # small key hints in the bottom corners
        snd = self.f_tiny.render("[M] SOUND OFF" if self.muted else "[M] SOUND ON", True, GREY)
        s.blit(snd, (W - snd.get_width() - 24, H - 26))
        if WEB:
            fs = self.f_tiny.render("[F] FULLSCREEN", True, GREY)
            s.blit(fs, (24, H - 26))

        block_glitch(s, self.glitch * GLITCH_STRENGTH)
        s.blit(self.overlay, (0, 0))

        # screen shake
        ox = random.uniform(-1, 1) * self.shake * 30 * SCREEN_SHAKE
        oy = random.uniform(-1, 1) * self.shake * 30 * SCREEN_SHAKE
        self.screen.fill(BG)
        self.screen.blit(s, (ox, oy))
        pygame.display.flip()

    def blink(self, speed=2):
        return int(self.t * speed) % 2 == 0

    def screen_title(self, text, sub=None, y=70):
        glitch_text(self.canvas, text, self.f_title, WHITE, (W // 2, y), self.glitch)
        if sub:
            t = self.f_tiny.render(sub, True, GREY)
            self.canvas.blit(t, t.get_rect(center=(W // 2, y + 34)))

    def draw_list(self, items, index, rects):
        s = self.canvas
        mouse = pygame.mouse.get_pos()
        for i, ((_, label, about), r) in enumerate(zip(items, rects)):
            on = i == index or r.collidepoint(mouse)
            shade = pygame.Surface(r.size, pygame.SRCALPHA)
            shade.fill((236, 236, 236, 255) if on else (6, 6, 7, 215))
            s.blit(shade, r)
            fg = BG if on else WHITE
            if not on:
                corner_brackets(s, r, GREY, 14, 2)
            s.blit(self.f_tiny.render(f"[{i + 1}]", True, scale(fg, 0.7) if on else GREY),
                   (r.x + 16, r.y + 10))
            s.blit(self.f_mid.render(label, True, fg), (r.x + 60, r.y + 8))
            s.blit(self.f_tiny.render(about, True, DIM if on else GREY), (r.x + 60, r.y + 40))
            if on:
                arrow = self.f_mid.render(">", True, BG)
                s.blit(arrow, (r.right - 34, r.y + 16))

    def footer(self, text):
        if self.blink():
            t = self.f_small.render(text, True, GREY)
            self.canvas.blit(t, t.get_rect(center=(W // 2, H - 60)))

    # ---------------- drawing: screens ----------------
    def draw_title(self):
        s = self.canvas
        glitch_text(s, "ROCK // PAPER // SCISSORS", self.f_huge, WHITE, (W // 2, 170),
                    max(self.glitch, 0.15))
        inverted_label(s, " v2 :: BREACH MODE ", self.f_small, CPU_COLOR, center=(W // 2, 230))
        typed = int(self.scene_t * 45)                  # 45 letters per second
        y = 320
        for line in INTRO:
            shown = line[:max(0, typed)]
            typed -= len(line) + 8                      # short pause between lines
            if shown:
                s.blit(self.f_small.render(shown, True, WHITE), (W // 2 - 300, y))
            y += 34
        if typed > 0 and self.blink():
            glitch_text(s, "PRESS ANY KEY", self.f_mid, WHITE, (W // 2, 540), 0)
        tip = self.f_tiny.render("1 / 2 / 3 = rock / paper / scissors     Q / W / E = hacker abilities",
                                 True, DIM)
        s.blit(tip, tip.get_rect(center=(W // 2, H - 60)))

    def draw_menu(self):
        s = self.canvas
        self.screen_title("ROCK // PAPER // SCISSORS", f"> breach.rps  //  node {self.ip}")
        items = self.menu_choices()
        self.draw_list(items, self.menu_index, self.menu_rects(len(items)))
        title, _ = rank_of(self.records['rounds_won'])
        info = self.f_small.render(f"RANK: {title}    //    ARCHIVE {self.records['fragments']}"
                                   f"/{len(FRAGMENTS)}", True, WHITE)
        s.blit(info, info.get_rect(center=(W // 2, 572)))
        hint = "UP / DOWN + ENTER, a number, or click" + ("" if WEB else "      ESC >> quit")
        self.footer(hint)

    def draw_difficulty(self):
        self.screen_title("CHOOSE YOUR TARGET", "who are you hacking?")
        items = self.diff_choices()
        self.draw_list(items, self.diff_index, self.menu_rects(len(items), top=230, step=90))
        self.footer("ENTER / click to start      B >> back")

    def draw_initials(self):
        s = self.canvas
        self.screen_title("NEW HIGH SCORE", f"score {self.score}  //  wave {self.round_number}", y=120)
        for i, r in enumerate(self.letter_rects()):
            on = i == self.letter_pos
            pygame.draw.rect(s, WHITE if on else GREY, r, 3 if on else 1)
            glitch_text(s, self.letters[i], self.f_big, WHITE, r.center, 0.1 if on else 0)
            for dy, arrow in ((-14, "▲"), (14, "▼")):
                a = self.f_small.render(arrow, True, WHITE if on else DIM)
                s.blit(a, a.get_rect(center=(r.centerx, (r.y if dy < 0 else r.bottom) + dy)))
        ok = self.ok_rect()
        pygame.draw.rect(s, WHITE, ok)
        t = self.f_mid.render("OK", True, BG)
        s.blit(t, t.get_rect(center=ok.center))
        self.footer("type your initials (or UP / DOWN), ENTER to save")

    def draw_rankings(self):
        s = self.canvas
        self.screen_title("RANKINGS", "saved on this device")
        # ---- left: top 10 endless scores ----
        box = pygame.Rect(80, 160, 500, 420)
        corner_brackets(s, box, WHITE, 22, 2)
        inverted_label(s, " TOP 10  //  ENDLESS ", self.f_small, WHITE, (box.x, box.y - 30))
        top = self.records['top']
        heads = self.f_tiny.render("#     NAME      SCORE      WAVE", True, GREY)
        s.blit(heads, (box.x + 30, box.y + 20))
        for i in range(10):
            y = box.y + 48 + i * 35
            if i < len(top):
                e = top[i]
                line = f"{i + 1:<5} {e['name']:<9} {e['score']:>6}      {e['wave']:>3}"
                col = WHITE
            else:
                line, col = f"{i + 1:<5} ---", DIM
            if i == self.highlight and self.blink(4):
                inverted_label(s, line, self.f_small, PLAYER_COLOR, (box.x + 22, y - 3))
            else:
                s.blit(self.f_small.render(line, True, col), (box.x + 30, y))
        # ---- right: your rank and records ----
        box2 = pygame.Rect(640, 160, 460, 420)
        corner_brackets(s, box2, CPU_COLOR, 22, 2)
        inverted_label(s, " YOUR HACKER RANK ", self.f_small, CPU_COLOR, (box2.x, box2.y - 30))
        r = self.records
        title, nxt = rank_of(r['rounds_won'])
        glitch_text(s, title, self.f_word, CPU_COLOR, (box2.centerx, box2.y + 60), self.glitch * 0.5)
        bar = pygame.Rect(box2.x + 40, box2.y + 110, box2.w - 80, 14)
        pygame.draw.rect(s, DIM, bar, 1)
        if nxt:
            prev = max(need for need, _ in RANKS if need <= r['rounds_won'])
            part = (r['rounds_won'] - prev) / (nxt - prev)
            sub = f"{r['rounds_won']} rounds won  //  {nxt - r['rounds_won']} more to rank up"
        else:
            part, sub = 1.0, f"{r['rounds_won']} rounds won  //  max rank"
        tile_fill(s, self.tiles, pygame.Rect(bar.x, bar.y, max(2, int(bar.w * part)), bar.h),
                  'hatch', CPU_COLOR, 7)
        t = self.f_tiny.render(sub, True, GREY)
        s.blit(t, t.get_rect(center=(box2.centerx, bar.bottom + 18)))
        rate = round(100 * r['wins'] / r['games']) if r['games'] else 0
        rows = [("quick matches played", r['games']), ("quick matches won", r['wins']),
                ("win rate", f"{rate}%"), ("best streak", r['best_streak']),
                ("best endless score", r['endless_best']),
                ("archive decrypted", f"{r['fragments']}/{len(FRAGMENTS)}")]
        for i, (k, v) in enumerate(rows):
            y = box2.y + 190 + i * 34
            s.blit(self.f_small.render(k, True, GREY), (box2.x + 40, y))
            val = self.f_small.render(str(v), True, WHITE)
            s.blit(val, (box2.right - 40 - val.get_width(), y))
        self.footer("ANY KEY / CLICK >> back")

    def draw_archive(self):
        s = self.canvas
        n = self.records['fragments']
        self.screen_title("ARCHIVE", f"the AI's private log  //  {n}/{len(FRAGMENTS)} decrypted")
        box = pygame.Rect(130, 150, W - 260, 400)
        corner_brackets(s, box, WHITE, 22, 2)
        for i, text in enumerate(FRAGMENTS):
            y = box.y + 30 + i * 60
            tag = f"FRAGMENT {i + 1:02d}"
            if i < n:
                inverted_label(s, f" {tag} ", self.f_tiny, WHITE, (box.x + 30, y))
                s.blit(self.f_small.render(text, True, WHITE), (box.x + 30, y + 24))
            else:
                s.blit(self.f_tiny.render(f" {tag}  [ENCRYPTED]", True, DIM), (box.x + 30, y))
                junk = ' '.join(fake_hex(4) for _ in range(12))
                s.blit(self.f_small.render(junk, True, DIM), (box.x + 30, y + 24))
        if n >= len(FRAGMENTS):
            inverted_label(s, " ARCHIVE COMPLETE. THANKS FOR PLAYING. ", self.f_small, CPU_COLOR,
                           center=(W // 2, box.bottom + 24))
        else:
            t = self.f_tiny.render("win quick matches (or level up in endless) to decrypt more",
                                   True, GREY)
            s.blit(t, t.get_rect(center=(W // 2, box.bottom + 24)))
        self.footer("ANY KEY / CLICK >> back")

    # ---------------- drawing: the match ----------------
    def draw_panel(self, rect, label, ident, color, score, choice, hand, winner,
                   line2, streak, ident_color=GREY):
        s = self.canvas
        col = color if not hand.dim else scale(color, 0.4)
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        shade.fill((6, 6, 7, 215))
        s.blit(shade, rect)
        corner_brackets(s, rect, col, 22, 2)

        name = inverted_label(s, f" {label} ", self.f_mid, col, (rect.x, rect.y - 34))
        if streak >= STREAK_MIN:                                   # "STREAK x3" badge
            badge = inverted_label(s, f" STREAK x{streak} ", self.f_small, BG,
                                   (name.right + 8, name.y + 3), fg=col, pad=(6, 2))
            pygame.draw.rect(s, col, badge, 1)
        idt = self.f_tiny.render(ident, True, ident_color)
        s.blit(idt, (rect.x + 14, rect.y + 12))
        sc = self.f_big.render(f"{score}", True, col)
        s.blit(sc, (rect.right - sc.get_width() - 14, rect.y + 2))

        lift, tilt = self.fist_motion()
        if hand.flip:
            tilt = -tilt
        hand.draw(s, (rect.centerx, rect.centery + 14), self.t, lift, tilt)

        if choice and self.state in ('result', 'final'):
            move = choice.upper()
        elif self.state in ('shake', 'reveal'):
            move = fake_hex(6)
        else:
            move = "???" if int(self.t * 2) % 2 else "..."
        lines = [(f"PAYLOAD   : {move}", col), line2]
        for i, (ln, c) in enumerate(lines):
            t = self.f_tiny.render(ln, True, c)
            s.blit(t, (rect.x + 14, rect.bottom - 44 + i * 17))

        if winner and self.state in ('result', 'final') and int(self.t * 6) % 2 == 0:
            inverted_label(s, "WINNER", self.f_small, col, (rect.right - 90, rect.bottom - 34))

    def draw_header(self):
        s = self.canvas
        glitch_text(s, "ROCK // PAPER // SCISSORS", self.f_title, WHITE, (W // 2, 38), self.glitch)
        mb = self.menu_button
        pygame.draw.rect(s, WHITE if mb.collidepoint(pygame.mouse.get_pos()) else GREY, mb, 1)
        t = self.f_tiny.render("< MENU [B]", True, WHITE)
        s.blit(t, t.get_rect(center=mb.center))
        left = self.f_tiny.render(f"node {self.ip}", True, GREY)
        s.blit(left, (mb.right + 12, 14))
        right = self.f_tiny.render(
            f"0x{fake_hex(8) if self.glitch > 0.2 else 'DEADC0DE'}  //  link stable", True, GREY)
        s.blit(right, (W - right.get_width() - 24, 16))

        if self.mode == 'endless':
            text = f"WAVE {self.round_number}  //  SCORE {self.score}"
            rnd = self.f_small.render(text, True, WHITE)
            s.blit(rnd, rnd.get_rect(center=(W // 2, 74)))
            hearts = self.f_mid.render("♥ " * self.lives + "· " * (ENDLESS_LIVES - self.lives),
                                       True, PLAYER_COLOR)
            s.blit(hearts, hearts.get_rect(center=(W // 2, 100)))
            return
        if self.sudden:
            if self.blink(3):
                inverted_label(s, " SUDDEN DEATH ", self.f_small, RED, center=(W // 2, 78))
            return
        rnd = self.f_small.render(f"ROUND {min(self.round_number, TOTAL_ROUNDS)}/{TOTAL_ROUNDS}", True, WHITE)
        s.blit(rnd, rnd.get_rect(center=(W // 2, 74)))
        done_n = self.round_number - (0 if self.state in ('result', 'final') else 1)
        for i in range(TOTAL_ROUNDS):
            pr = pygame.Rect(W // 2 - TOTAL_ROUNDS * 14 + i * 28, 90, 22, 8)
            if i < done_n:
                pygame.draw.rect(s, WHITE, pr)
            else:
                for xx in range(pr.x, pr.right, 8):
                    s.blit(self.tiles.get('lighthatch', GREY, 8), (xx, pr.y),
                           (0, 0, min(8, pr.right - xx), 8))

    def prediction_line(self):
        """Second line of the CPU panel: what the AI predicted this round."""
        guess, confidence = self.prediction
        if self.state in ('shake', 'reveal'):
            return f"PREDICTED : {fake_hex(6)}", GREY
        if self.state not in ('result', 'final'):
            return "PREDICTED : " + ("scanning" if int(self.t * 2) % 2 else "scanning."), GREY
        if guess is None:
            return "PREDICTED : learning you...", GREY
        hit = guess == self.player_choice
        return (f"PREDICTED : {guess.upper()} {int(confidence * 100)}%  {'[HIT]' if hit else '[MISS]'}",
                CPU_COLOR if hit else GREY)

    def draw_stamp(self, y=340):
        s = self.canvas
        text, bg = self.stamp
        jitter = random.randint(-6, 6) if self.timer < 0.3 else 0
        t = self.f_huge.render(text, True, BG)
        box = t.get_rect(center=(W // 2 + jitter, y)).inflate(40, 16)
        shadow = box.move(10, 10)
        tile = self.tiles.get('lighthatch', scale(bg, 0.6), 10)
        for yy in range(shadow.y, shadow.bottom, 10):
            for xx in range(shadow.x, shadow.right, 10):
                s.blit(tile, (xx, yy), (0, 0, min(10, shadow.right - xx), min(10, shadow.bottom - yy)))
        pygame.draw.rect(s, bg, box)
        s.blit(t, t.get_rect(center=box.center))

    def draw_scan(self, cx, cy):
        """BRAIN SCAN result between the two panels: flickering, fuzzy bars."""
        s = self.canvas
        head = self.f_tiny.render("CPU INTENT", True, CPU_COLOR)
        s.blit(head, head.get_rect(center=(cx, cy - 92)))
        for i, (move, v) in enumerate(self.scan.items()):
            y = cy - 70 + i * 50
            s.blit(self.f_tiny.render(move.upper(), True, WHITE), (cx - 70, y))
            noisy = max(0.05, min(1.0, v + 0.07 * math.sin(self.t * 9 + i * 2.1)))
            bar = pygame.Rect(cx - 70, y + 18, int(140 * noisy), 14)
            pygame.draw.rect(s, DIM, (cx - 70, y + 18, 140, 14), 1)
            tile_fill(s, self.tiles, bar, 'dither', CPU_COLOR, 7)
        sub = self.f_tiny.render("signal: fuzzy", True, GREY)
        s.blit(sub, sub.get_rect(center=(cx, cy + 92)))

    def draw_abilities(self):
        s = self.canvas
        x = min(r.x for r in self.ability_rects.values())
        tok = self.f_tiny.render(f"TOKENS {'◆' * self.tokens if self.tokens <= 6 else '◆x' + str(self.tokens)}",
                                 True, WHITE if self.tokens else GREY)
        s.blit(tok, (x - tok.get_width() - 16, H - 26))
        mouse = pygame.mouse.get_pos()
        deny_aid, deny_t = getattr(self, 'deny', (None, -9))
        for key, aid, label, _ in ABILITIES:
            r = self.ability_rects[aid]
            if aid in self.active:
                pygame.draw.rect(s, PLAYER_COLOR, r)
                fg = BG
            else:
                denied = aid == deny_aid and self.t - deny_t < 0.4
                usable = self.tokens > 0
                col = RED if denied else (WHITE if usable and r.collidepoint(mouse) else
                                          (GREY if usable else DIM))
                pygame.draw.rect(s, col, r, 1)
                fg = col
            t = self.f_tiny.render(f"[{key.upper()}] {label}", True, fg)
            s.blit(t, t.get_rect(center=r.center))

    def draw_match(self):
        s = self.canvas
        self.draw_header()

        pw, ph = 440, 380
        left = pygame.Rect(70, 150, pw, ph)
        right = pygame.Rect(W - 70 - pw, 150, pw, ph)
        if self.mode == 'versus':
            self.draw_versus(left, right)
            return
        signature = (f"SIGNATURE : 0x{'%06X' % (self.player_score * 4099 + 0xA11)}", GREY)
        self.draw_panel(left, PLAYER_NAME, "ID: PLAYER_01  //  STATUS: ONLINE", PLAYER_COLOR,
                        self.player_score, self.player_choice, self.player_hand,
                        self.result == 'player', signature, self.player_streak)
        # hacker abilities switched on this round: badges above your panel
        x = left.right
        for _, aid, label, _ in reversed(ABILITIES):
            if aid in self.active:
                x -= self.f_tiny.size(label)[0] + 16 + 8          # label width + padding + gap
                inverted_label(s, label, self.f_tiny, PLAYER_COLOR, (x, left.y - 28))

        info = self.opponent.info
        cpu_ident, cpu_ident_col = f"ID: {info['name']}  //  THREAT: {info['threat']}", GREY
        if SHOW_TAUNTS and self.state == 'result' and self.taunt:
            typed = int(self.timer * 40)                     # "types" 40 letters per second
            cursor = "_" if typed < len(self.taunt) or int(self.t * 3) % 2 else ""
            cpu_ident, cpu_ident_col = f"> {self.taunt[:typed]}{cursor}", CPU_COLOR
        if SHOW_PREDICTION:
            cpu_line2 = self.prediction_line()
        else:
            cpu_line2 = (f"SIGNATURE : 0x{'%06X' % (self.computer_score * 4099 + 0xA11)}", GREY)
        self.draw_panel(right, CPU_NAME, cpu_ident, CPU_COLOR,
                        self.computer_score, self.computer_choice, self.cpu_hand,
                        self.result == 'computer', cpu_line2, self.cpu_streak, cpu_ident_col)

        center_y = left.centery
        stamp_on = self.state == 'result' and self.timer < 1.4
        if self.state == 'shake':
            words = ["ROCK...", "PAPER...", "SCISSORS..."]
            idx = min(int(self.timer / self.beat), 2)
            pop = 1.0 - (self.timer % self.beat) / self.beat
            glitch_text(s, words[idx], self.f_word, WHITE, (W // 2, center_y), 0.15 * pop)
        elif self.state == 'reveal':
            inverted_label(s, " SHOOT! ", self.f_word, WHITE, center=(W // 2, center_y))
        elif self.state == 'choose' and self.scan:
            self.draw_scan(W // 2, center_y)
        elif not stamp_on:
            glitch_text(s, "VS", self.f_big, WHITE, (W // 2, center_y), self.glitch * 0.6)

        line_a, line_b = H - 166, H - 134
        if self.state == 'result':
            if stamp_on:
                self.draw_stamp()
            col = {'player': PLAYER_COLOR, 'computer': CPU_COLOR, 'tie': GREY}[self.result]
            if self.blocked:
                col = PLAYER_COLOR
            glitch_text(s, f"> {self.message}", self.f_mid, col, (W // 2, line_a), self.glitch * 0.6)
            if self.hint:
                why = self.f_small.render(f"riddle decoded: {self.hint[1]}", True, GREY)
                s.blit(why, why.get_rect(center=(W // 2, line_b)))
            if not self.match_over():
                hint = "SPACE / CLICK  >> next round"
                if self.mode != 'endless' and self.round_number >= TOTAL_ROUNDS and not self.sudden:
                    hint = "TIED!  SPACE / CLICK  >> SUDDEN DEATH"
                if self.blink():
                    h = self.f_tiny.render(hint, True, GREY)
                    s.blit(h, h.get_rect(center=(W // 2, H - 18)))
                if self.token_gained:
                    inverted_label(s, " +1 TOKEN ", self.f_tiny, PLAYER_COLOR,
                                   center=(W // 2 + 210, H - 18))
        elif self.state == 'choose':
            if self.sudden and self.timer < 1.6:
                self.draw_stamp()
            cursor = '_' if self.blink() else ' '
            if self.hint:
                label = self.f_tiny.render("> intercepted CPU thought:", True, GREY)
                s.blit(label, label.get_rect(center=(W // 2, line_a)))
                text = f'"{self.hint[0]}"{cursor}'
                font = self.f_mid if self.f_mid.size(text)[0] < W - 120 else self.f_small
                glitch_text(s, text, font, WHITE, (W // 2, line_b), 0)
            else:
                msg = "> no signal intercepted. trust your gut" if SHOW_RIDDLES else "> select payload"
                glitch_text(s, msg + cursor, self.f_mid, WHITE, (W // 2, line_a + 16), 0)
            self.draw_abilities()

        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, self.f_mid, self.f_small, self.tiles, b.rect.collidepoint(mouse),
                   self.state == 'choose')

        if self.state == 'final':
            self.draw_final()

    def draw_versus(self, left, right):
        """The match screen in 2 PLAYER mode."""
        s = self.canvas
        for side, rect, name, color, score, choice, hand, streak in (
                (0, left, P1_NAME, PLAYER_COLOR, self.player_score, self.player_choice,
                 self.player_hand, self.player_streak),
                (1, right, P2_NAME, CPU_COLOR, self.computer_score, self.computer_choice,
                 self.cpu_hand, self.cpu_streak)):
            ready = self.state != 'choose' or self.locked[side]
            status = ("STATUS    : LOCKED", color) if ready else \
                     ("STATUS    : choosing" + "." * (int(self.t * 3) % 4), GREY)
            self.draw_panel(rect, name, f"ID: PLAYER_0{side + 1}  //  STATUS: ONLINE", color,
                            score, choice, hand, self.result == ('player', 'computer')[side],
                            status, streak)
            if self.state == 'choose' and self.locked[side] and self.blink(3):
                inverted_label(s, " LOCKED IN ", self.f_mid, color, center=(rect.centerx, rect.y + 62))

        center_y = left.centery
        stamp_on = self.state == 'result' and self.timer < 1.4
        if self.state == 'shake':
            words = ["ROCK...", "PAPER...", "SCISSORS..."]
            idx = min(int(self.timer / self.beat), 2)
            pop = 1.0 - (self.timer % self.beat) / self.beat
            glitch_text(s, words[idx], self.f_word, WHITE, (W // 2, center_y), 0.15 * pop)
        elif self.state == 'reveal':
            inverted_label(s, " SHOOT! ", self.f_word, WHITE, center=(W // 2, center_y))
        elif not stamp_on:
            glitch_text(s, "VS", self.f_big, WHITE, (W // 2, center_y), self.glitch * 0.6)

        line_a = H - 166
        if self.state == 'result':
            if stamp_on:
                self.draw_stamp()
            col = {'player': PLAYER_COLOR, 'computer': CPU_COLOR, 'tie': GREY}[self.result]
            glitch_text(s, f"> {self.message}", self.f_mid, col, (W // 2, line_a), self.glitch * 0.6)
            if not self.match_over() and self.blink():
                hint = "SPACE / CLICK  >> next round"
                if self.round_number >= TOTAL_ROUNDS and not self.sudden:
                    hint = "TIED!  SPACE / CLICK  >> SUDDEN DEATH"
                h = self.f_tiny.render(hint, True, GREY)
                s.blit(h, h.get_rect(center=(W // 2, H - 18)))
        elif self.state == 'choose':
            if self.sudden and self.timer < 1.6:
                self.draw_stamp()
            msg = "> both players: pick in secret, then SHOOT"
            glitch_text(s, msg, self.f_mid, WHITE, (W // 2, line_a + 16), 0)

        mouse = pygame.mouse.get_pos()
        for side, k, move, r in self.versus_buttons:
            on = self.state == 'choose' and not self.locked[side]
            col = (PLAYER_COLOR, CPU_COLOR)[side] if on else DIM
            if on and r.collidepoint(mouse):
                pygame.draw.rect(s, col, r, 3)
            else:
                pygame.draw.rect(s, col, r, 1)
            t = self.f_small.render(move.upper(), True, col)
            s.blit(t, t.get_rect(center=(r.centerx, r.centery - 9)))
            t = self.f_tiny.render(f"[{k.upper()}]", True, scale(col, 0.7))
            s.blit(t, t.get_rect(center=(r.centerx, r.centery + 14)))

        if self.state == 'final':
            self.draw_final()

    def draw_final(self):
        s = self.canvas
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 215))
        s.blit(ov, (0, 0))
        if self.mode == 'endless':
            title = f"you survived {self.round_number} waves and won {self.round_wins} rounds"
            col, tag = CPU_COLOR, "CONNECTION TERMINATED"
            score_line = f"SCORE {self.score}"
        elif self.mode == 'versus':
            how = " in SUDDEN DEATH" if self.sudden else ""
            if self.player_score > self.computer_score:
                title, col, tag = f"Player 1 won the game{how}!", PLAYER_COLOR, f"{P1_NAME} WINS"
            elif self.computer_score > self.player_score:
                title, col, tag = f"Player 2 won the game{how}!", CPU_COLOR, f"{P2_NAME} WINS"
            else:
                title, col, tag = "The game is a draw!", GREY, "DEADLOCK"
            score_line = f"{P1_NAME} {self.player_score}  :  {self.computer_score} {P2_NAME}"
        else:
            how = " in SUDDEN DEATH" if self.sudden else ""
            if self.player_score > self.computer_score:
                title, col, tag = f"You won the game{how}!", PLAYER_COLOR, "SYSTEM OWNED"
            elif self.computer_score > self.player_score:
                title, col, tag = f"Computer won the game{how}!", CPU_COLOR, "ACCESS DENIED"
            else:
                title, col, tag = "The game is a draw!", GREY, "CONNECTION LOST"
            score_line = f"{PLAYER_NAME} {self.player_score}  :  {self.computer_score} {CPU_NAME}"
        if SHOW_STATS:
            box = pygame.Rect(W // 2 - 450, H // 2 - 270, 900, 540)
            tag_y, title_y, score_y = box.y + 58, box.y + 112, box.y + 172
        else:
            box = pygame.Rect(W // 2 - 400, H // 2 - 160, 800, 320)
            tag_y, title_y, score_y = box.y + 80, box.y + 150, box.y + 220
        corner_brackets(s, box, col, 34, 3)
        inverted_label(s, " === FINAL RESULT === ", self.f_small, col, (box.x, box.y - 30))
        glitch_text(s, tag, self.f_huge, col, (W // 2, tag_y), max(self.glitch, 0.12))
        glitch_text(s, title, self.f_mid, WHITE, (W // 2, title_y), 0)
        glitch_text(s, score_line, self.f_big, WHITE, (W // 2, score_y), 0)
        if SHOW_STATS:
            self.draw_stats(box)
        self.draw_fragment(box)
        if self.blink():
            again = "save your score" if self.mode == 'endless' and self.qualifies() else "play again"
            hint = f"ANY KEY / CLICK >> {again}      [B] >> menu"
            glitch_text(s, hint, self.f_small, GREY, (W // 2, box.bottom - 24), 0)

    def draw_fragment(self, box):
        """Final screen: the story fragment this game decrypted (if any)."""
        s = self.canvas
        if self.mode == 'versus':
            return
        y = box.bottom - 92
        if self.new_fragments:
            n = self.new_fragments[-1]
            inverted_label(s, f" FRAGMENT {n:02d}/{len(FRAGMENTS):02d} DECRYPTED ", self.f_tiny,
                           PLAYER_COLOR, center=(W // 2, y))
            t = self.f_small.render(FRAGMENTS[n - 1], True, WHITE)
            s.blit(t, t.get_rect(center=(W // 2, y + 26)))
        else:
            if self.mode == 'quick':
                need = "win a match"
            else:
                need = f"win {ENDLESS_LEVEL_UP} rounds (a level-up)"
            t =self.f_tiny.render(f"{need} to decrypt the next fragment  //  ARCHIVE "
                                   f"{self.records['fragments']}/{len(FRAGMENTS)}", True, GREY)
            s.blit(t, t.get_rect(center=(W // 2, y + 10)))

    def draw_stats(self, box):
        """Final screen, middle part: 3 columns - your moves / AI accuracy / saved records."""
        s = self.canvas
        top = box.y + 222
        pygame.draw.line(s, DIM, (box.x + 40, top), (box.right - 40, top), 1)
        col_w = (box.w - 80) // 3
        x1, x2, x3 = box.x + 40, box.x + 40 + col_w, box.x + 40 + 2 * col_w
        y = top + 20

        def heading(text, x):
            s.blit(self.f_tiny.render(text, True, GREY), (x, y))

        def move_chart(title, x, counts):
            heading(title, x)
            total = max(1, sum(counts.values()))
            favourite = max(counts, key=counts.get)
            for i, (move, n) in enumerate(counts.items()):
                row_y = y + 28 + i * 30
                c = WHITE if move == favourite and n else GREY
                s.blit(self.f_tiny.render(move.upper(), True, c), (x, row_y))
                bar = pygame.Rect(x + 86, row_y + 1, max(2, int(120 * n / total)), 14)
                tile_fill(s, self.tiles, bar, FILL[move], c, 7)
                pct = self.f_tiny.render(f"{round(100 * n / total)}%", True, c)
                s.blit(pct, (x + 214, row_y))

        if self.mode == 'versus':        # 2 PLAYER: both players' moves + streaks
            move_chart(f"{P1_NAME} MOVES", x1, self.move_counts)
            move_chart(f"{P2_NAME} MOVES", x2 + 20, self.move_counts2)
            heading("BEST STREAK", x3 + 10)
            for i, (name, n) in enumerate(((P1_NAME, self.best_streak), (P2_NAME, self.best_streak2))):
                row_y = y + 28 + i * 20
                s.blit(self.f_tiny.render(name, True, GREY), (x3 + 10, row_y))
                val = self.f_tiny.render(str(n), True, WHITE)
                s.blit(val, (x3 + col_w - 20 - val.get_width(), row_y))
            return

        # ---- column 1: which moves you played (bar chart) ----
        move_chart("YOUR MOVES", x1, self.move_counts)

        # ---- column 2: how well the AI read you ----
        heading("AI READ YOU", x2 + 20)
        if self.ai_guesses:
            big = f"{self.ai_hits}/{self.ai_guesses}"
            sub = f"predictions right ({round(100 * self.ai_hits / self.ai_guesses)}%)"
        else:
            big, sub = "--", "no predictions yet"
        s.blit(self.f_word.render(big, True, CPU_COLOR), (x2 + 20, y + 24))
        s.blit(self.f_tiny.render(sub, True, GREY), (x2 + 20, y + 78))
        s.blit(self.f_tiny.render("it keeps learning next game", True, DIM), (x2 + 20, y + 96))

        # ---- column 3: saved records ----
        r = self.records
        heading("RECORD  (saved on this device)", x3 + 10)
        rank, _ = rank_of(r['rounds_won'])
        if self.mode == 'endless':
            rows = [("best score", r['endless_best']), ("this run", self.score),
                    ("best streak", r['best_streak']), ("rank", rank)]
            new = " NEW HIGH SCORE! " if getattr(self, 'new_high', False) else None
        else:
            rate = round(100 * r['wins'] / r['games']) if r['games'] else 0
            rows = [("games played", r['games']), ("win rate", f"{rate}%"),
                    ("best streak", r['best_streak']), ("rank", rank)]
            new = " NEW BEST STREAK! " if self.new_best else None
        for i, (k, v) in enumerate(rows):
            row_y = y + 28 + i * 20
            s.blit(self.f_tiny.render(k, True, GREY), (x3 + 10, row_y))
            val = self.f_tiny.render(str(v), True, WHITE)
            s.blit(val, (x3 + col_w - 20 - val.get_width(), row_y))
        if new and self.blink(4):
            inverted_label(s, new, self.f_tiny, PLAYER_COLOR, (x3 + 10, y + 112))

    async def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            for e in pygame.event.get():
                self.handle(e)
            self.update(dt)
            self.draw()
            # hand control back to the browser once per frame,
            # otherwise the web page freezes (harmless on desktop)
            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(Game().run())

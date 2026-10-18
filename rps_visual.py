"""
ROCK // PAPER // SCISSORS  -  hacker HUD edition
Visual version of try1.py (same rules, same 5 rounds).

Controls:
    1 / 2 / 3  or click a button  -> rock / paper / scissors
    SPACE / click                  -> next round
    any key / click                -> play again on the final screen
    M                              -> mute / unmute music and sounds
    F                              -> fullscreen (web version)
    ESC                            -> quit

Needs pygame:   pip install pygame
"""
import asyncio
import math
import os
import random
import sys

import pygame

WEB = sys.platform == "emscripten"      # True when running in a web browser

# =====================================================================
#  YOUR GAME LOGIC - imported from try1.py (your own file!)
# =====================================================================
from try1 import choices, get_winner

TOTAL_ROUNDS = 5


def get_computer_choice():
    # same line you wrote inside get_decisions() in try1.py
    return random.choice(list(choices.values()))


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

PLAYER_COLOR = WHITE
CPU_COLOR = RED

# player hand = style 'B' (bright outline + texture fill per move)
# cpu hand    = style 'C' (made of 0s and 1s, bright outline digits)
PLAYER_STYLE = 'B'
CPU_STYLE = 'C'
FILL = {'rock': 'hatch', 'paper': '!', 'scissors': 'bars'}

# timing (seconds)
SHAKE_BEAT = 0.28          # one "rock / paper / scissors" pump
SHAKE_BEATS = 3
DECODE_TIME = 0.35         # glitch-in of the real moves after SHOOT!
FINAL_DELAY = 1.6          # after round 5: show its result this long, then the final screen
RESTART_DELAY = 0.8        # final screen ignores input this long (so it isn't skipped by accident)

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

    def show(self, name, idle=False):
        """Show a shape immediately (used for the shaking fist)."""
        self.target, self.idle, self.progress, self.dim = name, idle, 1.0, False

    def reveal(self, name):
        """Glitch-in a new shape."""
        self.target, self.idle, self.progress, self.dim = name, False, 0.0, False
        self.lock = [random.random() * 0.85 for _ in self.lock]

    def update(self, dt):
        if self.progress < 1:
            self.progress = min(1.0, self.progress + dt / DECODE_TIME)
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
MUSIC_FILE = "music.ogg"      # swap for your own track: .ogg / .mp3 / .wav
MUSIC_VOLUME = 0.35


def load_sound(filename, volume=0.7):
    """Load one sound effect. Returns None (= silent) if it can't be loaded."""
    path = os.path.join(SOUND_DIR, filename)
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
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
#  GAME
# =====================================================================
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
        self.t = 0.0
        self.ip = f"{random.randint(10, 220)}.{random.randint(0, 255)}." \
                  f"{random.randint(0, 255)}.{random.randint(1, 254)}"
        self.reset()

    def reset(self):
        self.round_number = 1
        self.player_score = 0
        self.computer_score = 0
        self.glitch = 0.8
        self.new_round()

    def new_round(self):
        self.state = 'choose'          # choose -> shake -> reveal -> result
        self.timer = 0.0
        self.message = "select payload"
        self.result = None
        self.player_choice = self.computer_choice = None
        self.shake = 0.0
        self.player_hand.show('rock', idle=True)
        self.cpu_hand.show('rock', idle=True)

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

    # ---------------- flow ----------------
    def play(self, key):
        if self.state != 'choose':
            return
        self.player_choice = choices[key]
        self.computer_choice = get_computer_choice()
        self.result = get_winner(self.player_choice, self.computer_choice)
        self.message = make_message(self.result, self.computer_choice)
        self.player_hand.show('rock')
        self.cpu_hand.show('rock')
        self.state = 'shake'
        self.timer = 0.0
        self.sound('beat')                      # 1st pump: "ROCK..."

    def shoot(self):
        self.player_hand.reveal(self.player_choice)
        self.cpu_hand.reveal(self.computer_choice)
        self.state = 'reveal'
        self.timer = 0.0
        self.glitch = 0.7
        self.shake = 0.25
        self.sound('shoot')                     # "SHOOT!"

    def finish_reveal(self):
        if self.result == 'player':
            self.player_score += 1
            self.cpu_hand.dim = True
            self.sound('win')
        elif self.result == 'computer':
            self.computer_score += 1
            self.player_hand.dim = True
            self.sound('lose')
        else:
            self.sound('tie')
        self.state = 'result'
        self.timer = 0.0
        self.glitch = 1.0
        self.shake = 0.3

    def next_round(self):
        if self.round_number >= TOTAL_ROUNDS:
            self.state = 'final'
            self.timer = 0.0
            self.glitch = 1.0
            return
        self.round_number += 1
        self.glitch = 0.5
        self.new_round()

    # ---------------- loop ----------------
    def handle(self, e):
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE and not WEB:     # a browser tab can't be closed
                pygame.quit()
                sys.exit()
            if e.key == pygame.K_m:
                self.toggle_mute()
            if e.key == pygame.K_f and WEB:
                self.toggle_fullscreen()
            ch = e.unicode
            if self.state == 'choose' and ch in choices:
                self.play(ch)
            elif self.state == 'result':
                if ch in choices and self.round_number < TOTAL_ROUNDS:
                    self.next_round()
                    self.play(ch)
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.next_round()
            elif self.state == 'final' and e.key not in (pygame.K_m, pygame.K_f, pygame.K_ESCAPE):
                self.restart()                      # any key plays again
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.state == 'final':
                self.restart()                      # any mouse button plays again
            elif e.button != 1:
                return
            elif self.state == 'choose':
                for b in self.buttons:
                    if b.rect.collidepoint(e.pos):
                        self.play(b.key)
            elif self.state == 'result':
                self.next_round()

    def restart(self):
        if self.timer >= RESTART_DELAY:
            self.reset()

    def update(self, dt):
        self.t += dt
        self.timer += dt
        self.glitch = max(0.0, self.glitch - dt * 1.8)
        self.shake = max(0.0, self.shake - dt)
        if random.random() < 0.004:
            self.glitch = random.uniform(0.3, 0.5)
        for st in self.streaks:
            st.update(dt)
        self.player_hand.update(dt)
        self.cpu_hand.update(dt)
        if self.state == 'shake':
            if self.timer >= SHAKE_BEAT * SHAKE_BEATS:
                self.shoot()
            else:
                # tiny screen bump + beat sound every time the fists land
                beat_pos = (self.timer % SHAKE_BEAT) / SHAKE_BEAT
                if beat_pos < dt / SHAKE_BEAT and self.timer > dt:
                    self.shake = 0.12
                    self.sound('beat')          # 2nd and 3rd pump
        elif self.state == 'reveal' and self.timer >= DECODE_TIME + 0.05:
            self.finish_reveal()
        elif self.state == 'result' and self.round_number >= TOTAL_ROUNDS and self.timer >= FINAL_DELAY:
            self.next_round()                   # last round done -> final screen by itself

    def fist_motion(self):
        """Up-down pump for the shake: returns (lift_pixels, tilt_degrees)."""
        if self.state == 'shake':
            phase = (self.timer % SHAKE_BEAT) / SHAKE_BEAT
            up = math.sin(phase * math.pi)            # 0 -> 1 -> 0 each beat
            return -70 * up, 16 * up
        if self.state == 'choose':                     # gentle idle bob
            return 6 * math.sin(self.t * 2.2), 0
        return 0, 0

    # ---------------- drawing ----------------
    def draw_panel(self, rect, label, ident, color, score, choice, hand, winner):
        s = self.canvas
        col = color if not hand.dim else scale(color, 0.4)
        shade = pygame.Surface(rect.size, pygame.SRCALPHA)
        shade.fill((6, 6, 7, 215))
        s.blit(shade, rect)
        corner_brackets(s, rect, col, 22, 2)

        inverted_label(s, label, self.f_mid, col, (rect.x, rect.y - 34))
        idt = self.f_tiny.render(ident, True, GREY)
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
        lines = [f"PAYLOAD   : {move}",
                 f"SIGNATURE : 0x{'%06X' % (score * 4099 + 0xA11)}"]
        for i, ln in enumerate(lines):
            t = self.f_tiny.render(ln, True, col if i == 0 else GREY)
            s.blit(t, (rect.x + 14, rect.bottom - 44 + i * 17))

        if winner and self.state in ('result', 'final') and int(self.t * 6) % 2 == 0:
            inverted_label(s, "WINNER", self.f_small, col, (rect.right - 90, rect.bottom - 34))

    def draw_header(self):
        s = self.canvas
        glitch_text(s, "ROCK // PAPER // SCISSORS", self.f_title, WHITE, (W // 2, 38), self.glitch)
        left = self.f_tiny.render(f"> breach.rps  //  node {self.ip}", True, GREY)
        s.blit(left, (24, 16))
        right = self.f_tiny.render(
            f"0x{fake_hex(8) if self.glitch > 0.2 else 'DEADC0DE'}  //  link stable", True, GREY)
        s.blit(right, (W - right.get_width() - 24, 16))
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

    def draw_stamp(self):
        s = self.canvas
        if self.result == 'player':
            text, bg = "HACK SUCCESSFUL", WHITE
        elif self.result == 'computer':
            text, bg = "HACK FAILED", RED
        else:
            text, bg = "STALEMATE", GREY
        jitter = random.randint(-6, 6) if self.timer < 0.3 else 0
        t = self.f_huge.render(text, True, BG)
        box = t.get_rect(center=(W // 2 + jitter, 355)).inflate(40, 16)
        shadow = box.move(10, 10)
        tile = self.tiles.get('lighthatch', scale(bg, 0.6), 10)
        for yy in range(shadow.y, shadow.bottom, 10):
            for xx in range(shadow.x, shadow.right, 10):
                s.blit(tile, (xx, yy), (0, 0, min(10, shadow.right - xx), min(10, shadow.bottom - yy)))
        pygame.draw.rect(s, bg, box)
        s.blit(t, t.get_rect(center=box.center))

    def draw(self):
        s = self.canvas
        s.fill(BG)
        for st in self.streaks:
            st.draw(s)
        self.draw_header()

        pw, ph = 440, 410
        left = pygame.Rect(70, 150, pw, ph)
        right = pygame.Rect(W - 70 - pw, 150, pw, ph)
        self.draw_panel(left, " YOU ", "ID: PLAYER_01  //  STATUS: ONLINE", PLAYER_COLOR,
                        self.player_score, self.player_choice, self.player_hand,
                        self.result == 'player')
        self.draw_panel(right, " CPU ", "ID: CPU_UNIT  //  THREAT: HIGH", CPU_COLOR,
                        self.computer_score, self.computer_choice, self.cpu_hand,
                        self.result == 'computer')

        center_y = left.centery
        stamp_on = self.state == 'result' and self.timer < 1.4
        if self.state == 'shake':
            words = ["ROCK...", "PAPER...", "SCISSORS..."]
            idx = min(int(self.timer / SHAKE_BEAT), 2)
            pop = 1.0 - (self.timer % SHAKE_BEAT) / SHAKE_BEAT
            glitch_text(s, words[idx], self.f_word, WHITE, (W // 2, center_y), 0.15 * pop)
        elif self.state == 'reveal':
            inverted_label(s, " SHOOT! ", self.f_word, WHITE, center=(W // 2, center_y))
        elif not stamp_on:
            vs_glitch = self.glitch * 0.6
            glitch_text(s, "VS", self.f_big, WHITE, (W // 2, center_y), vs_glitch)

        msg_y = H - 128
        if self.state == 'result':
            if stamp_on:
                self.draw_stamp()
            col = {'player': WHITE, 'computer': RED, 'tie': GREY}[self.result]
            glitch_text(s, f"> {self.message}", self.f_mid, col, (W // 2, msg_y), self.glitch * 0.6)
            hint = "SPACE / CLICK  >> next round" if self.round_number < TOTAL_ROUNDS \
                else "compiling final result..."
            if int(self.t * 2) % 2 == 0:
                h = self.f_tiny.render(hint, True, GREY)
                s.blit(h, h.get_rect(center=(W // 2, H - 18)))
        elif self.state == 'choose':
            cursor = '_' if int(self.t * 2) % 2 == 0 else ' '
            glitch_text(s, f"> {self.message}{cursor}", self.f_mid, WHITE, (W // 2, msg_y), 0)

        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(s, self.f_mid, self.f_small, self.tiles, b.rect.collidepoint(mouse),
                   self.state == 'choose')

        # small key hints in the bottom corners
        snd = self.f_tiny.render("[M] SOUND OFF" if self.muted else "[M] SOUND ON", True, GREY)
        s.blit(snd, (W - snd.get_width() - 24, H - 26))
        if WEB:
            fs = self.f_tiny.render("[F] FULLSCREEN", True, GREY)
            s.blit(fs, (24, H - 26))

        if self.state == 'final':
            self.draw_final()

        block_glitch(s, self.glitch)
        s.blit(self.overlay, (0, 0))

        # screen shake
        ox = random.uniform(-1, 1) * self.shake * 30
        oy = random.uniform(-1, 1) * self.shake * 30
        self.screen.fill(BG)
        self.screen.blit(s, (ox, oy))
        pygame.display.flip()

    def draw_final(self):
        s = self.canvas
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 215))
        s.blit(ov, (0, 0))
        if self.player_score > self.computer_score:
            title, col, tag = "You won the game!", WHITE, "SYSTEM OWNED"
        elif self.computer_score > self.player_score:
            title, col, tag = "Computer won the game!", RED, "ACCESS DENIED"
        else:
            title, col, tag = "The game is a draw!", GREY, "CONNECTION LOST"
        box = pygame.Rect(W // 2 - 400, H // 2 - 160, 800, 320)
        corner_brackets(s, box, col, 34, 3)
        inverted_label(s, " === FINAL RESULT === ", self.f_small, col, (box.x, box.y - 30))
        glitch_text(s, tag, self.f_huge, col, (W // 2, box.y + 80), max(self.glitch, 0.12))
        glitch_text(s, title, self.f_mid, WHITE, (W // 2, box.y + 150), 0)
        glitch_text(s, f"YOU {self.player_score}  :  {self.computer_score} CPU",
                    self.f_big, WHITE, (W // 2, box.y + 220), 0)
        if int(self.t * 2) % 2 == 0:
            hint = "ANY KEY / CLICK >> play again" if WEB \
                else "ANY KEY / CLICK >> play again     ESC >> disconnect"
            glitch_text(s, hint, self.f_small, GREY, (W // 2, box.bottom - 24), 0)

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

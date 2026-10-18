# ROCK // PAPER // SCISSORS — hacker HUD edition

A 5-round Rock Paper Scissors game against the computer, with a glitchy "hacker terminal" look, animated hands, music and sound effects. Written in Python with pygame. It runs on the desktop and in a web browser.

### ▶ [Play it in your browser](https://raftan10.github.io/rock-paper-scissors-visualized-cyber-version-/)

![Gameplay screenshot](docs/screenshot.png)

## How to play

| Key | Action |
|---|---|
| `1` / `2` / `3`, or click a button | rock / paper / scissors |
| `Space` or click | next round |
| any key or click | play again on the final screen |
| `M` | mute / unmute |
| `F` | fullscreen (browser) |

The first load in a browser can take a while, because it downloads a small Python runtime. After that it's cached. Click the page once to start, which lets the browser play sound.

## How it works

The project is split into a **brain** and a **face**:

| File | Role |
|---|---|
| [`try1.py`](try1.py) | **The brain:** the game rules. A dictionary maps keys to moves (`{'1': 'rock', ...}`), and `get_winner()` decides each round. Run on its own, it's a text version of the game in the terminal. |
| [`rps_visual.py`](rps_visual.py) | **The face:** the pygame window, the hand animations, the effects and the sound. It **imports the rules from `try1.py`** instead of copying them, so changing a rule there changes the visual game too. |
| [`main.py`](main.py) | Starts the web version. |
| [`build_web.py`](build_web.py) | Builds the browser version with [pygbag](https://github.com/pygame-web/pygbag). |

`try1.py` puts its console game under `if __name__ == "__main__":`, so importing it doesn't start the console game.

The visual game runs a loop about 60 times a second, with three steps:

1. **Input:** read key presses and clicks.
2. **Update:** advance the animation, decide the winner, update the score and play sounds.
3. **Draw:** redraw the whole screen.

Each round moves through four states: `choose → shake → reveal → result`. After 5 rounds there's a `final` screen.

The hands aren't images. Each one is drawn as a shape, sampled into a 60 × 40 grid, and every cell is filled with a texture or a `0`/`1` digit. That's what gives them the retro look.

### Making it work in a browser

- **pygbag** packages the game, and the browser runs it with Python compiled to WebAssembly.
- The game loop calls `await asyncio.sleep(0)` every frame, so the browser stays responsive.
- The sounds are `.ogg` files and the font file ships with the game, because browsers can't play every sound format and have no system fonts.
- In the browser, Python starts with the same random seed on every load, so `main.py` re-seeds it from the clock. Otherwise the computer would make the same moves every game.
- **GitHub Actions** ([workflow](.github/workflows/deploy-web.yml)) rebuilds the web version and publishes it to GitHub Pages on every push.

## Run it on your computer

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install pygame-ce
python rps_visual.py            # visual version
python try1.py                  # text version in the terminal
```

To test the web version locally:

```bash
pip install pygbag
python build_web.py --serve     # then open http://localhost:8000
```

## Credits

- Font: [DejaVu Sans Mono](https://dejavu-fonts.github.io/). Its license is in [`fonts/DejaVu-LICENSE.txt`](fonts/DejaVu-LICENSE.txt).
- The sound effects and music were generated for this project.

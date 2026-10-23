# Version 2 plan

**Status (2026-10-23):** the jam build is done and released as `v2.0` on itch.io: https://raftan10.itch.io/rockpaperscissor-cyber
Steps 1 to 8 and the two-player stretch goal are built. The open tasks are at the bottom, under "Still to do".

### Changes made after this plan was written

The jam build below is what was planned. These changes were made afterwards and win over the plan:

- **Hacker abilities are Endless-only.** Quick Match keeps the riddles but has no abilities or tokens.
- **Endless has no lives.** One loss ends the run. Ties don't.
- **Mission briefing screen** before Quick Match and Endless. It explains the riddles, and in Endless the abilities.
- **Ability bar** is bigger, brighter, and pulses in round 1. Tokens show as a number.
- **Auto-continue:** after each round, the next one starts by itself after 4 seconds (`AUTO_NEXT`).

The jam is about one day away. This plan has two parts:

- **Jam build:** what we add in the next day, in order.
- **After the jam:** everything else, kept for later.

## Ground rules for the jam build

- Tag the current game as `v1.0` before starting. If anything breaks, v1 can still be submitted.
- **No big refactor.** `rps_visual.py` stays one file. New content goes in two new small files, `opponents.py` and `riddles.py`.
- Commit after every step. Every commit must be playable on desktop and in the browser.
- **Feature freeze 3 hours before the deadline.** After that, only fixes, the web build, screenshots and the jam page.

---

## Jam build, in order

| # | Step | Budget |
|---|---|---|
| 1 | AI difficulty levels | 1.5 h |
| 2 | Title screen and mode menu | 1.5 h |
| 3 | Sudden death | 1 h |
| 4 | Riddle hints | 2 h |
| 5 | Hacker abilities, 3 of them | 2 h |
| 6 | Endless survival and rankings | 2 h |
| 7 | Story framing, light version | 1 h |
| 8 | Web build, README, screenshots, submission | 1.5 h |
| | **Total** | **12.5 h** |
| ★ | Stretch: local two-player | 1.5 h |

**If we fall behind:** cut step 7 first, then make step 6 save only one high score instead of a top 10.

### 1 · AI difficulty levels

- The AI picks its move at the **start** of each round instead of when you press a key. Riddles and BRAIN SCAN need a move that already exists. It still uses only past rounds, so it stays fair.
- Three levels:

| Level | Name | How it plays |
|---|---|---|
| Easy | SCRIPT KIDDIE | Mostly random, uses its memory about 30% of the time |
| Normal | FIREWALL | The current learning AI from `try1.py`, unchanged |
| Hard | BLACK ICE | Remembers your last two moves and your overall favourite move |

### 2 · Title screen and mode menu

- A short boot sequence types out, then "PRESS ANY KEY".
- Menu: QUICK MATCH, ENDLESS, RANKINGS. Quick Match then asks for a difficulty.
- Works with the keyboard alone, and with clicks.

### 3 · Sudden death

- If a Quick Match ends tied, play SUDDEN DEATH rounds until someone wins.
- Red screen tint and a slow-motion reveal. The existing sounds are reused.

### 4 · Riddle hints

- Each round shows a meme riddle about the CPU's move, which is already chosen.
- Evergreen memes only, because trending ones age within months. No politically charged memes. Text only, because the font has no emoji.
- Two kinds:
  - **Meme riddles** point at the move.
  - **NOT riddles** rule one move out.
- Easy gives meme riddles. Normal mixes both. Hard gives only NOT riddles.
- After the round, one line explains the joke, for example "ROCK. The Rock's eyebrow raise."

### 5 · Hacker abilities (vs AI only)

- You get 3 tokens per match, plus 1 for every 3-win streak.
- Each ability costs 1 token and is used before you pick your move.

| Key | Ability | What it does |
|---|---|---|
| `Q` | BRAIN SCAN | Shows the AI's thinking as fuzzy bars with noise, so it's a clue, not an answer |
| `W` | OVERCLOCK | A win this round counts double |
| `E` | FIREWALL | A loss this round counts as a tie |

### 6 · Endless survival and rankings

- One loss ends the run. Ties are free.
- The AI gets harder every 5 wins: Easy, then Normal, then Hard.
- Score: points per win, plus a streak bonus.
- A local top 10 with arcade-style 3-letter initials.
- A rank title from your lifetime record: SCRIPT KIDDIE → HACKER → ELITE → ROOT.
- Saved in the browser on the web, and in `records.json` on a PC.

### 7 · Story framing, light version

- The title screen sets the premise: a rogue AI has taken over the network, and you are hacking it.
- Every match you win decrypts one fragment of a hidden message. The final fragment reveals the ending.
- Progress is saved with the records.

### 8 · Submission

- Test the web build in a browser and on a phone.
- New screenshots and a short GIF.
- Update the README and the controls table.
- Write the jam page text.

### ★ Stretch · Local two-player

Only if steps 1 to 7 are done before the feature freeze.

- Player 1 uses `A` `S` `D`, player 2 uses `J` `K` `L`.
- Both pick in secret. The screen shows "LOCKED" until both have chosen.
- Best of 5 with sudden death. No riddles or abilities.

---

## Starter riddle bank

**Rock**
- "*raises one eyebrow very slowly*" (The Rock's eyebrow)
- "Can you smell what the CPU is cooking?" (The Rock's catchphrase)
- "Patrick Star lives under one of these."
- "Sticks and ____ may break your bones."
- "*sits in burning room* This is fine. Fire can't hurt me." (This Is Fine)

**Paper**
- "Money printer go BRRRR." (paper money)
- "2020 called. It wants its toilet rolls back." (toilet paper panic)
- "Limitless ____ in a ____less world." (The Office, Michael Scott)
- "My homework ate the dog."
- "I'm the boyfriend. Rock is my girlfriend. Something thin just walked by." (Distracted Boyfriend)

**Scissors**
- "Snip snip. It's a crab rave tonight." (Crab Rave)
- "Edward ____hands sends his regards."
- "Mom said don't run with these."
- "Peace sign. But make it dangerous."
- "Barber at 3am: 'just a little trim'."

**NOT riddles**
- "Never gonna give you up. Never gonna fold." (Rickroll) → not paper
- "Drake says no to sharp things." (Drakeposting) → not scissors
- "Hard pass. Literally." → not rock

---

## Still to do

### Right now (jam and release)

1. **Submit to the jam.** The itch.io page is live but not yet entered in the jam.
2. **Play-test in a browser and on a phone.** Use the itch.io page. Check sound, saving, touch buttons and fullscreen.
3. **itch.io page polish.** Dark page theme (background #060607, links #FF2834). Make the AI disclosure list Code and Text too. Consider matching the page title to "Breach Mode".
4. **Merge `v2` into `main`.** This updates the GitHub front page and the GitHub Pages web version, which still show v1.
5. **A short GIF** for the itch.io page and README.

### Balance to watch

- **FIREWALL in Endless** now saves the run from a loss for 1 token, which may be too strong. Possible fix: cost 2 tokens.
- **Safari** can block saving inside itch.io's frame, so records may not stick for some players.

### After the jam

1. **Full story mode.** Four chapters, each with its own opponent, colour, taunts and lore. The early chapters double as the tutorial. The final boss is ROOT, a secret fourth difficulty that notices when you try to counter it.
2. **More abilities and loadouts.** Add SPOOF, which feeds the AI a fake move, and DECRYPT, which makes a riddle clearer. Players pick 2 abilities before each match.
3. **Refactor** `rps_visual.py` into smaller files, with a proper screen system.
4. **Input layer** that turns keys, touch and joysticks into actions. Arcade sticks then only need a new mapping.
5. **In-game settings:** glitch strength, screen shake, volume and reduced flashing.
6. **Polish:** particles, screen flashes, a heartbeat sound for sudden death. A full how-to-play page beyond the briefing.
7. **Arcade battles:** USB arcade sticks, an attract mode that plays itself when idle, and a tournament bracket for events.
8. **Online leaderboard.** It needs a server.

# Math Quest

A daily PEMDAS adventure for Sydney (8), Lucas (12) and Jordan (13). Instead of
a flat page of a hundred drills, each kid gets their own themed world, a
difficulty that adapts while they play, and hints that teach the rule rather
than just marking them wrong.

- **`index.html`** — the app. One self-contained file, no install, works offline.
- **`math_quest.py`** — the same engine in the terminal.

---

## Getting it onto an iPhone or iPad

Three ways, best first.

### 1. A real web address (works anywhere — school, a friend's house, grandma's)

Push this folder to GitHub and turn on GitHub Pages:

1. In the repo on github.com: **Settings → Pages**
2. **Source:** Deploy from a branch → **Branch:** `main`, **Folder:** `/ (root)`
3. Save, wait about a minute.

The app is then at:

```
https://<your-github-username>.github.io/10days-usa-cli-planner/mathquest/
```

Text that link to the kids. On the iPhone: open it in Safari → tap the **Share**
button → **Add to Home Screen**. It gets an icon and launches fullscreen with no
browser chrome, exactly like a native app.

> This is the option that survives you turning your laptop off, and it is the
> only one that works when they are not on the house wifi.

### 2. On the home wifi only (no internet needed)

From the folder containing `index.html`, on your Mac:

```bash
cd ~/Sites/mathquest
python3 -m http.server 8080
```

Then on the iPhone (same wifi): `http://<your-mac-ip>:8080`

Find the Mac's IP with `ipconfig getifaddr en0`.

**Want to drop the `:8080`?** Ports below 1024 need root, so serve on port 80
with:

```bash
sudo python3 -m http.server 80
```

…and the address becomes just `http://<your-mac-ip>` — much easier for a kid to
type. The trade-off is that it needs `sudo` every time and only one thing can
own port 80 at a time.

Two caveats with the LAN approach: the Mac has to be awake and running the
server, and your router can hand the Mac a new IP address after a reboot, which
silently breaks the bookmark. A DHCP reservation in the router pins it.

### 3. AirDrop the file

AirDrop `index.html` to the iPad. It lands in Files, and tapping it opens a
preview. This works for a quick look but is the **worst** option for daily use:
the Files preview does not reliably keep `localStorage`, so levels, treasures
and streaks can vanish between sessions. Use 1 or 2 if they are going to play
more than once.

---

## What each kid gets

| | Sydney (8) | Lucas (12) | Jordan (13) |
|---|---|---|---|
| World | Boba & ice cream shop with Stripes the tiger | Fishing trip | Brawl trophy road |
| Reward | Toppings, spa stickers | Rarer fish in deeper water | Bronze → Mythic → Hall of Fame |
| Starts at | Level 1 | Level 2 | Level 3 |
| Day length | ~40% of the chosen length | full length | full length |
| Levels up after | 4 correct in a row | 3 in a row | 3 in a row |

Quest length is a button on the home screen: 20, 40, 80 or 100 questions.
Sydney always gets a shorter day than the boys — an 8-year-old does not need a
hundred of these to learn the rule.

### Sydney's ladder is deliberately gentle

This was rebuilt after the first version came out far too hard for an
8-year-old. Her ten levels now go:

| Level | What she sees | Example |
|---|---|---|
| 1 | one step, single digits | `8 - 1` |
| 2 | three small numbers | `5 + 5 + 2` |
| 3 | small times tables | `4 × 4` |
| 4 | **× before +**, the big idea | `7 + 3 × 3` |
| 5 | same idea, slightly bigger | `9 + 4 × 5` |
| 6 | parentheses appear | `(4 + 4) × 3` |
| 7 | two multiplications | `4 × 3 + 4 × 3` |
| 8 | division appears | `10 ÷ 2 + 6` |
| 9 | three operations | `(7 + 2) × 4 - 3` |
| 10 | squares | `3² + 5` |

Her guardrails, enforced by the generator and checked in the test suite: no
times-table fact harder than 5 × 10, no answer above 45, never a negative
number, and never a fraction at any intermediate step.

Lucas and Jordan climb into nested parentheses, exponents and (for Jordan)
negative results.

---

## How the daily quest works

Questions are generated from a seed built out of **today's date in DD/MM/YY
form** plus the kid's name and level, so:

- the same day gives the same quest on every device,
- each kid gets a completely different set,
- tomorrow is a brand-new quest with no repeats to memorise.

**It adapts as they play.** Answer several in a row correctly *and* reasonably
quickly and the level goes up mid-quest, immediately regenerating everything
they have not seen yet. Miss two in a wave and it quietly steps back down. The
level they finish at is where they start tomorrow.

**Wrong answers teach.** The first miss names the rule to apply. The second
shows the first step worked out and what the expression looks like afterwards.
The third gives the full walkthrough, line by line. Nobody ever just gets
"wrong" with no way forward.

At the end of the day, **Coach notes** looks at which rules they have been
missing across every session and calls out the weakest one.

---

## Terminal version

```bash
python3 math_quest.py                 # menu
python3 math_quest.py --kid lucas     # jump straight in
python3 math_quest.py --length 80     # questions per day
python3 math_quest.py --date 05/08/26 # replay a specific day
python3 math_quest.py --selftest      # validate the generator
```

Type `h` at any prompt for a hint (again for more), `q` to save and quit.
Progress goes to `math_quest_save.json` next to the script.

---

## Where progress is stored

The web app saves to the browser's `localStorage`, which means **progress is
per-device**. If Lucas plays on the iPad on Monday and the desktop on Tuesday,
those are two separate save files. Playing on the same device every day is what
makes levels and treasures accumulate.

# Math Quest

A daily PEMDAS adventure for Sydney (8), Lucas (12) and Jordan (13). Instead of
a flat page of a hundred drills, each kid gets their own themed world, a
difficulty that adapts while they play, and hints that teach the rule rather
than just marking them wrong.

- **`index.html`** — the app. One self-contained file, no install, works offline.
- **`math_quest.py`** — the same engine in the terminal.
- **`worksheet.py`** — printable PDF worksheets, 50 questions per page.
- **`serve.sh`** — serve it to the house wifi on port 80.

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

On your Mac, from this folder:

```bash
./serve.sh
```

That serves on **port 80**, so the address is a bare IP with no port on the end —
`http://192.168.0.30` — which is far easier for a kid to type on an iPad. It
prints the exact URL to hand out. Ports below 1024 are privileged, so it will
ask for your password.

Don't want the sudo prompt? Pass a high port instead:

```bash
./serve.sh 8080      # -> http://192.168.0.30:8080
```

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

## Printable worksheets

50 questions laid out **5 across and 10 down** on one page, with a matching
answer key on page 2 so checking them is a straight left-to-right read.

```bash
pip install fpdf2      # once
python3 worksheet.py   # writes one PDF per kid, ready to print
```

Open the PDF and hit Cmd-P. Options:

```bash
python3 worksheet.py --kid sydney      # just one kid
python3 worksheet.py --level 6         # pin the difficulty
python3 worksheet.py --count 30        # fewer questions
python3 worksheet.py --cols 4          # wider columns for longer expressions
python3 worksheet.py --no-ramp         # every question at one level
python3 worksheet.py --out ~/Desktop   # where to write them
```

By default each sheet is built around **the level that kid is currently
playing at**, ramping gently across three levels so it starts easy and
finishes at their edge. Questions are checked for duplicates, so nobody gets
`7 - 3` four times on the same page.

One deliberate exception: Sydney's printed sheets never go below level 4. Her
first three levels are single-operation warm-ups (`8 - 1`), which are right for
her first minutes in the game but would make an order-of-operations worksheet
with no order of operations in it. Pass `--level 2` if you want those anyway.

PDF generation uses [fpdf2](https://github.com/py-pdf/fpdf2). The expressions
are measured and the type shrunk per cell, so long ones like
`(10 + 13) × (4 - 1)` still fit their column.

---

## Terminal version

```bash
python3 math_quest.py                 # menu
python3 math_quest.py --kid lucas     # jump straight in
python3 math_quest.py --length 50     # questions per day (any number 5-500)
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

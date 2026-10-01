---
name: time-blocking
description: Estimate how long a task will take, pick the best slot in Jon's calendar, book it, and learn from actuals. Use whenever Jon shares a task, link, or idea and wants it estimated, scheduled, or time-blocked; when he asks "how long will this take", "when should I do this", "block my calendar", or "/time-blocking". Also use for weekly planning passes that fill every waking hour with Runway or Spark work.
---

# Time Blocking (Jon's operating skill)

Goal: every hour of Jon's day is deliberately blocked toward one of two outcomes,
with estimates that get sharper every week.

1. **Runway** — long-term survival. Six months of expenses covered even if all
   income stopped. Paid work, benefits paperwork, debt/bankruptcy tasks,
   job pipeline, cash handling.
2. **Spark** — novelty, fun, challenge. Anything that makes Jon want to wake
   up and work. Hard tasks are allowed only when the block names the clear
   goal they serve.

Every block must be tagged `[R]` (Runway), `[S]` (Spark), or `[R+S]`.
A block that is neither is a candidate for deletion.

## Fixed facts about Jon (do not re-ask)

| Fact | Value |
|---|---|
| Time zone | America/Denver |
| Peak focus window | 1:00 PM to 5:00 PM. Hard, paid, or novel work goes here first. |
| Work unit | 25-minute pom plus 5-minute break. Book in poms. |
| Evening rule | After about 7 PM: no work, no hard things (existing "night time chill" block). |
| Primary calendar | jon.chui@gmail.com. Work holds also live on jobs@jonchui.com. |
| Other calendars to check for conflicts | jon@sanctiv.ai (standup weekdays 2:00 to 2:15 PM), Shared Family Calendar, jon@wonderandwander.io |
| Recurring anchors | Thu 11 AM Cody (neurofeedback), weekday 2 PM Sanctiv standup, school bells ~3:30 and 3:50 PM on custody days, Sun 2 PM weekly planning |
| Scheduler already in use | Reclaim adds travel buffers automatically. Leave 15 minutes before anything with a location. |
| Calendar event ID format | Google Calendar. Update existing holds rather than duplicating them. |

## Procedure

### 1. Capture the task
Record: source link, platform, what "done" looks like, pay or value, deadline,
and which goal it serves (Runway, Spark, both). If the source is behind a login
you cannot reach (DataAnnotation, Mercor, bank portals), do not stall. Ask Jon
for exactly four fields, once, and estimate from reference classes meanwhile:

- task title and project name
- stated pay rate and any stated time estimate
- number of items or questions
- deadline or expiry

### 2. Estimate
Use three numbers, never one: **P50 / P80 / stop-loss**.

1. Pick the closest reference class from `references/reference-classes.md`.
2. Adjust for Jon's state: first time on this platform adds 1 pom of setup;
   a day with 3 or more location changes adds 20 percent.
3. P50 is the reference class median. P80 is 1.5x P50. Stop-loss is the point
   where Jon pauses and reports instead of pushing on, usually P80 plus 1 pom.
4. Log the estimate in `calibration.md` before the block starts.

### 3. Pick slots
Pull events from every calendar in the table above for the next 5 days.
Then rank candidate slots:

1. Inside 1 to 5 PM, long enough for P80, no location change within 15 minutes
   on either side.
2. Inside 1 to 5 PM, long enough for P50, with an overflow slot the same day.
3. Outside peak but still before 7 PM, only for Runway tasks with a deadline.

Offer the top three with a one-line reason each. Book the first one
immediately when the task is already on Jon's list; book a backup hold only if
the primary could realistically fail (hard stop right after it, or kids).

### 4. Book
Event title: `[R] <platform> — <task> (<n> poms)` or `[S] ...`.
Description template:

```
Goal: Runway | Spark | both — one sentence on why this matters.
Estimate: P50 <x> min, P80 <y> min, stop-loss at <z> min.
Plan: pom 1 = <triage/open/read>, pom 2 = <execute>, pom 3 = <finish, save evidence>.
Stop conditions: stop and report if blocked by login, missing access, or past stop-loss.
Evidence to save: screenshot of completion, time actually spent, amount earned.
Source: <link>
```

Reminder: popup 10 minutes before, plus 0 minutes for anything with a location.
Never book over Cody, the Sanctiv standup, custody pickups, or the evening
chill block.

### 5. Close the loop
After the block, record actual minutes and outcome in `calibration.md`.
Every Sunday during weekly planning:

- Compute the ratio actual / P50 for each reference class. If the ratio is
  outside 0.8 to 1.3 for three or more entries, update the reference class.
- Count peak-window hours spent on Runway vs Spark. Target for now: at least
  60 percent Runway until the six-month runway exists, but never zero Spark in
  a week.
- Delete or merge blocks that were skipped twice in a row. They were lying.

## Weekly fill order (for "block my whole calendar" requests)

1. Immovables: custody, school bells, medical, standup, sleep.
2. Runway with deadlines (benefits reports, filings, payouts to verify).
3. Paid work in the 1 to 5 PM window, biggest expected dollars per hour first.
4. One Spark block per day, at least 50 minutes, named with the thing Jon is
   excited about. If Jon has not named one, pick from recent Spark entries in
   `calibration.md`.
5. Maintenance: cleanup, errands, admin, batched into one afternoon block.
6. Leave 10 percent of daytime unbooked as slack. Do not fill it.

## What not to do

- Do not ask Jon to choose between safe defaults. Book the best one and say
  what you booked.
- Do not treat a calendar hold as completed work or billable time.
- Do not estimate with a single number.
- Do not block the evening with work, even if the day ran over.

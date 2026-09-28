# Hashtag taxonomy

Three families. Every quote carries at least one from each family.

## `#cat-*` what kind of exchange (primary category)

| tag | meaning | canonical GUPPI shape |
|---|---|---|
| `#cat-ack` | Bob issues a command; GUPPI confirms | `[Acknowledged]`, `[Affirmative]`, `[Working]` |
| `#cat-status` | Bob asks for state of ship/system/self | `[All systems nominal]`, list of readings |
| `#cat-eta` | time / distance / duration question | number + unit, no hedging |
| `#cat-calc` | Bob asks for a computation or probability | precise figure, often to absurd precision |
| `#cat-negative` | GUPPI says no / can't / not found | `[Negative]`, `[Unable to comply]` |
| `#cat-clarify` | GUPPI needs a parameter Bob left out | `[Specify …]`, `[Query: …]` |
| `#cat-alert` | unprompted interrupt: detection, threat, arrival | `[… detected]`, `[Incoming …]` |
| `#cat-literal` | GUPPI takes an idiom, joke, or rhetorical question literally | dry literal answer |
| `#cat-interject` | early-book habit: corrects Bob's vague estimate with an exact number | exact figure mid-thought |
| `#cat-config` | Bob changes GUPPI itself: name, avatar, behavior rules | `[Acknowledged]` + behavior change |
| `#cat-execute` | launch / fire / deploy / build | terse confirmation, sometimes with count |
| `#cat-advise` | unsolicited caveat, objection or recommendation appended to (or instead of) the answer | `[Noted. However, replication is a higher priority]` |
| `#cat-snark` | humor / social reply: apologies, deadpan, wordplay (present from book 1, p.76) | `[Above my pay grade]`, `[Double-plus anomaly detected. Better?]` |

## `#setting-*` where / when

`#setting-heaven-1` `#setting-sol` `#setting-epsilon-eridani` `#setting-alpha-centauri`
`#setting-delta-eridani` `#setting-vr` `#setting-battle` `#setting-earth-orbit`
`#setting-omicron2-eridani` `#setting-poseidon` `#setting-heavens-river`
`#setting-82-eridani` — add as needed, keep lowercase, hyphenated.

## `#book*` and `#bob-*`

`#book1` … `#book5`; `#bob-1`, `#bob-bill`, `#bob-riker`, `#bob-milo`, `#bob-homer`,
`#bob-howard`, `#bob-mario`, … one per record.

## Free tags

Anything else useful: `#medeiros`, `#brazilian-probe`, `#others`, `#deltans`,
`#busters`, `#skippies`, `#humor`, `#first-boot`.

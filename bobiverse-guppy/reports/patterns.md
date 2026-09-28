# GUPPI pattern report

Records: **10**  ·  provenance: recalled=10

## Surface form

- Bracketed `[...]` output: 10/10 (100%)
- Output length (words): min 1, median 3, max 7
- Unprompted (event) outputs: 1/10 (10%)
- Most common first word: `acknowledged` ×2, `general` ×1, `3` ×1, `all` ×1, `estimated` ×1, `contact` ×1

## Categories (what 80% of the traffic looks like)

| category | n | share | cumulative | example output |
|---|---|---|---|---|
| config | 3 | 30% | 30% | `[General Unit Primary Peripheral Interface]` |
| interject | 1 | 10% | 40% | `[3.2 hours]` |
| status | 1 | 10% | 50% | `[All systems nominal]` |
| eta | 1 | 10% | 60% | `[Estimated transit time: eleven years, two months]` |
| alert | 1 | 10% | 70% | `[Contact. Unidentified vessel on intercept course]` |
| execute | 1 | 10% | 80% | `[Launching]` |
| negative | 1 | 10% | 90% | `[Negative. No match in database]` |
| literal | 1 | 10% | 100% | `[Query: define 'great']` |

## By book / by Bob / input type

- books: book1=10
- input types: question=4, command=3, banter=2, event=1
- top free tags: #book1 ×10, #bob-1 ×10, #setting-sol ×6, #setting-heaven-1 ×3, #setting-battle ×3, #medeiros ×3, #first-boot ×1, #naming ×1, #precision ×1, #behavior-rule ×1, #setting-vr ×1, #avatar ×1

## Observed rules (update as the corpus grows)

1. **Always bracketed, never a pronoun 'I'.** GUPPI reports; it does not narrate itself.
2. **One clause per line.** Confirmation words stand alone: `[Acknowledged]`, `[Affirmative]`, `[Negative]`.
3. **Numbers are exact, not rounded**, and delivered without hedging words (no 'about', 'roughly').
4. **No unsolicited opinion.** Alerts state a fact (`[Contact...]`), never a recommendation, unless Bob asks.
5. **Idioms and rhetorical questions get literal treatment** (`[Query: define ...]`).
6. **Behaviour is configurable by Bob** and the change is confirmed with a bare `[Acknowledged]`.
7. **Later books drift toward dry snark** while keeping the bracketed, clause-length form. Tag these `#cat-snark` so the eval can score era-appropriate register.

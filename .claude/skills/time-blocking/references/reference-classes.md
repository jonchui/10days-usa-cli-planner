# Reference classes

Medians are starting points. Replace them with Jon's own medians from
`../calibration.md` once three or more actuals exist for a class.

## DataAnnotation (hourly-paid, self-timed tasks)

DataAnnotation pays by the hour worked, not per item, so the real question is
"how many quality hours can I bank before the queue empties or I hit stop-loss".
Task pages normally show pay rate, an instructions block, and sometimes an
expected length. First task in any new project costs one extra pom for reading
the project instructions and the examples.

| class | what it looks like | P50 per task | notes |
|---|---|---|---|
| da-unknown | task not yet opened | 60 min | default: 1 pom triage + 1 pom work + buffer |
| da-chat-rating | rate or compare chatbot responses, write short rationales | 20 min per item | fast once instructions are learned |
| da-coding-eval | review code responses, run or reason about snippets, rank | 35 min per item | Jon's strongest class; expect high accept rate |
| da-coding-write | write a prompt and a reference solution with tests | 60 to 90 min per item | highest pay per hour, deepest focus |
| da-qualification | unpaid or low-paid gate test for a new project | 45 min | Runway investment; do once, during peak |
| da-long-form | write or edit multi-paragraph responses with sources | 45 min per item | watch stop-loss, these creep |

## Other recurring classes

| class | P50 | notes |
|---|---|---|
| admin-triage | 25 min | open a portal, find the thing, write next step |
| benefits-form | 50 min | TANF/SNAP reports; gather docs first pom, fill second |
| payout-verify | 25 min | match a payout notice to earnings and bank posting |
| sanctiv-deliverable-start | 50 min | scope read + first commit |
| job-application | 40 min | tailored application with one new paragraph |
| spark-build | 50 to 100 min | personal project session; always name the goal |

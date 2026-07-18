# Council report format

Template for `docs/plans/council-<topic>.md`. Keep every section; write "None" rather than deleting one — an explicitly empty bucket tells the reader the analysis looked and found nothing, a missing section says nothing.

```markdown
# Council report — <topic>

Date: <YYYY-MM-DD>
Council: <inline analysis | full council (lenses run)>

## Roster

| Plan | Model | File | Gist |
| ---- | ----- | ---- | ---- |
| A    | fable | docs/plans/fable-<topic>.md | one sentence |
| B    | kimi  | docs/plans/kimi-<topic>.md  | one sentence |

## Settled decisions

Decisions every plan agreed on. Adopt with confidence.

- **<decision>** — <the shared position, one sentence>

## Divergences

The real decisions. One subsection per divergence:

### <decision>

- **Plan A**: <position — reasoning>
- **Plan B**: <position — reasoning>
- **At stake**: <the actual trade-off, not a restatement of the positions>
- **Council verdicts** (if lenses ran): <per-lens verdict, one line each>
- **Recommendation**: <position + why>
- **Resolution**: <filled in while drafting the final plan; leave as "open" until then>

## Majority calls

Decisions where one plan dissented without a load-bearing argument. One line each: the adopted position and the dismissed dissent.

## Unique contributions

Catches only one plan made. Credit the plan; these survive into the final plan regardless of how that plan fared overall.

- **(Plan B)** <the catch>

## Blind spots

What no plan addressed but a plan for this work should have.

## Recommendation

Which plan (if any) is the best backbone for the final plan, and the shape of the merge in a paragraph.
```

---
name: linklog
description: Sync Vid's linklog (saved articles feed) into the Obsidian vault and review new items — clustering them by theme and promoting the interesting ones into blog post ideas. Use when the user says "sync my linklog", "any new articles", "/linklog", or wants to review saved articles for blog inspiration.
---

# Linklog sync & review

Vid saves interesting articles at linklog.app. This skill pulls the feed into his Obsidian vault and turns the interesting ones into blog post ideas.

**Paths (absolute — this skill runs from any cwd):**

- Vault: `/Users/vluther/Documents/Obsidian Vault`
- Hub table: `<vault>/Areas/Writing/Linklog.md`
- Ideas hub: `<vault>/Areas/Writing/Blog Ideas.md`
- Idea notes: `<vault>/Areas/Writing/Ideas/`
- Idea template: `<vault>/Templates/Blog Idea.md`
- Feed: `https://api.linklog.app/vidluther/feed` (RSS 2.0)

## Step 1 — Sync

Fetch and parse the feed (WebFetch gets a 403; curl with a browser User-Agent works):

```
curl -sL -H "User-Agent: Mozilla/5.0" "https://api.linklog.app/vidluther/feed" | python3 <skill-dir>/scripts/fetch_feed.py
```

Output is TSV: `pubDate(ISO)  title  link  description`.

Dedup by URL: any `link` already present in `Linklog.md`'s table is old — skip it. Insert the rest as new rows at the **top** of the table (newest first), formatted:

```
| YYYY-MM-DD | [Title](url) | new | |
```

Escape pipe characters in titles. Report the count: "N new articles since last sync."

## Step 2 — Review (conversational)

Don't just dump the list. Read the new items' titles/descriptions and:

1. **Cluster** them by theme ("three of these are about agent memory…").
2. **Connect**: check `Blog Ideas.md` — does a new article feed an existing idea? Say so.
3. **Ask** which to promote into ideas, which to mark `reviewed`, which to `skip`. One short pass, not an interrogation.

## Promotion

When Vid promotes an article (or a cluster) into an idea:

1. Create `<vault>/Areas/Writing/Ideas/<Idea Title>.md` from the Blog Idea template (`status: spark`, today's date, article links under Sources).
2. Add a row to `Blog Ideas.md`: `| [[<Idea Title>]] | spark | <source links> | luther.io |`.
3. In `Linklog.md`, set the article's status to `promoted` and wikilink the Idea column.

Filenames must be unique across the vault (vault convention — links are bare-filename wikilinks).

## Wrap-up

Per the vault's session ritual (see `<vault>/AGENTS.md`): log a 1–2 line summary to today's daily note under `## Log`. Update `TASKS.md` only if commitments changed. From here, `/blog-post` takes an idea forward.

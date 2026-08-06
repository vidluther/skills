---
name: blog-post
description: Take a blog post idea from Vid's vault through interview → outline → scaffold → review → publish for luther.io (Astro). Use when the user says "/blog-post", "work on the <X> post", "let's write that blog post", "new blog post about X", or "review my draft".
---

# Blog post pipeline for luther.io

Takes an idea from `Blog Ideas.md` to a published Astro post. Vid writes the prose; you interview, outline, scaffold, and review. **Never write the post for him unless he explicitly asks.**

**Paths (absolute — runs from any cwd):**

- Vault: `/Users/vluther/Documents/Obsidian Vault`
- Ideas hub: `<vault>/Areas/Writing/Blog Ideas.md` · idea notes: `<vault>/Areas/Writing/Ideas/`
- Astro repo: `/Users/vluther/work/personal/astro.luther.io` · posts: `src/content/articles/`

## Which stage?

Read the idea note's `status` and run the matching stage below. Pipeline: `spark → interviewing → outlined → drafting → in-review → published`. If no idea is named, list the hub table and ask which one. If the idea doesn't exist yet, create it first (template: `<vault>/Templates/Blog Idea.md`) and add a hub row.

## spark → outlined: interview, then outline

Interview Vid **one question at a time** (see the `rubber-duck` skill for the technique — recommendation offered with each question, wait for the answer, follow the branch). Target his raw material, not facts you can look up:

- What's his actual take? Where does he *disagree* with the source articles?
- What personal story/experience makes this his post rather than a summary?
- Who is it for, and what should they do differently after reading?

Capture answers verbatim-ish under `## Interview Notes` in the idea note as you go (each answer is written down before the next question — session may die anytime). When the angle is sharp, propose an outline under `## Outline`: section headings, one line each on what it argues, where sources slot in. Iterate until he approves. Set status `outlined` in note + hub.

## outlined → drafting: scaffold in the Astro repo

Create `src/content/articles/_YYYY-MM-DD-<kebab-slug>.mdx`. The leading `_` keeps it **out of the build** (glob pattern `[^_]*` skips it) — the site has no draft field, this is the only mechanism. Frontmatter (schema: `src/content.config.ts`):

```yaml
---
title: "Title In Title Case"
description: "One-sentence summary for meta tags and listings."
publishDate: YYYY-MM-DD
slug: kebab-slug
tags:
  - lowercase-kebab
---
```

Always set `slug` — it drives the URL (`/articles/<slug>`), decoupled from the filename. Body: the outline as `##` headings, each with an HTML comment holding the argument prompt + source links for Vid to write against. Record the file path under `## Draft` in the idea note. Set status `drafting`. Vid writes in his own time.

## drafting → in-review: review the draft

When Vid says it's ready: read the `_`-file, review for (in order) argument coherence vs. the outline, his voice (conversational, first-person — read a recent published post first to calibrate), factual claims vs. sources, then polish `description` and `tags` (compare against tags used by existing posts). Suggest `relatedArticles` refs if any existing post genuinely relates (schema supports it). Give feedback as a short list; edit only what he asks you to edit. Verify: `pnpm run build && pnpm run fmt:check && pnpm run lint` in the repo (build runs `astro check`). Set status `in-review`.

## in-review → published (only on explicit "publish")

1. Rename to drop the `_` prefix.
2. `pnpm run build` again; confirm the post appears.
3. Version control: repo uses GitButler (`gitbutler/workspace` branch) → use `but`, never plain git. **Do not commit or push unless Vid explicitly says to** (his global rule).
4. Set status `published` in note + hub; move the idea's linklog sources to final state if any were still open.

## Wrap-up (every stage)

Update the idea note + `Blog Ideas.md` hub row, and log 1–2 lines to today's daily note under `## Log` per `<vault>/AGENTS.md`. Update `TASKS.md` if a commitment changed (e.g. "draft due" promises).

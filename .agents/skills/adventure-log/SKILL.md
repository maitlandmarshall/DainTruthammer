---
name: adventure-log
description: Maintain this campaign's adventure/session logs during live play or post-session cleanup. Use when Codex needs to append session beats, update chronological adventure files, capture character state changes, reconcile open threads, record discoveries, preserve player prompts, or add session images.
---

# Adventure Log

## Overview

Keep `Adventures/YYYY-MM-DD.md` useful during play and reliable afterward. Append chronology first, then reconcile state, Codex facts, open threads, and images without inventing certainty.

Use `start-adventure` when creating the initial file and recap for a new session. Use this skill after play begins or when cleaning up an existing session log.

## Live Logging Workflow

1. Identify the active adventure file, usually today's `Adventures/YYYY-MM-DD.md`.
2. Append new events under `## Live Notes (chronological)` in order.
3. Preserve direct user narration as a prompt only when it materially defines in-world events:

````md
- **[Prompt]**

  ```text
  user text here
  ```
````

4. Add concise bullets under `## Character State Changes` for HP, resources, items, conditions, location, relationships, disguises, promises, and other meaningful changes.
5. Add important facts under `## New Canon / Important Discoveries` when they should propagate into Codex.
6. Add or update `## Open Threads` for newly opened, advanced, or resolved hooks.
7. If a new meaningful visual beat occurs, generate or queue the image immediately using the repo-local `openai-image-gen` workflow and embed it before ending the turn.
8. Use knowledge tags such as `[Party]`, `[Character-only]`, `[NPC-only]`, `[DM-private]`, `[Inferred]`, `[Rumor]`, `[To verify]`, and `[Retcon]`.

Do not reorder past beats during live capture unless the user asks. Append first; clean later.

## Git Snapshots During Play

The user has given standing permission for frequent campaign-memory commits during live play, session startup, and post-session cleanup so the player does not have to manually commit the archive.

- Commit early after the active session file is created or after the first meaningful live-play beat is captured.
- Commit often after coherent chunks: a logged scene, state reconciliation, Codex update, open-thread update, or completed image/embed pass.
- Before committing, run lightweight checks when practical, such as `git diff --check` and markdown image/link verification for touched files.
- Stage only files that belong to the current campaign-memory chunk: adventure logs, Character files, Codex pages, relevant skill/instruction updates, and generated images actually embedded or referenced.
- Do not stage or commit `.env`, secrets, dependency churn, editor files, unrelated user work, or speculative scratch material.
- If the git index already contains staged changes, do not unstage them. Inspect enough to avoid trampling the user's review queue, then either leave unrelated staged changes alone or include them only when they clearly belong to the same campaign update.
- Use short commit messages that describe the archive change, such as `session: log Dain outcast note` or `codex: add Garl Glittergold faith page`.
- If a commit cannot be made cleanly, leave the worktree intact and tell the user exactly what remains uncommitted.

## Session File Shape

Prefer this structure, preserving existing local variants:

```md
# Session - YYYY-MM-DD

## Summary
- Filled after play.

## Links
- Previous session: ...
- Next session: TBD
- Open Threads: [Open Threads](../Codex/Lore/Open%20Threads.md)

## Starting State
- Location:
- Immediate goal:
- Important active conditions/resources:
- Key unresolved tension entering session:

## Live Notes (chronological)
- ...

## Character State Changes
- ...

## New Canon / Important Discoveries
- ...

## Open Threads
- ...

## Images
- ...
```

If the file uses `What Happened Last Time`, `Open Points`, or `Get Into Character` from `start-adventure`, preserve those sections and append live material below them.

## Post-Session Cleanup

After play or when asked to clean up:

1. Fill `## Summary` with 3-8 concise bullets.
2. Keep `## Live Notes` as source chronology unless the user explicitly wants a rewrite.
3. Reconcile `Character/Current State.md`, `Character/Inventory.md`, `Character/Relationships.md`, and `Character/Timeline.md` for confirmed changes.
4. Update affected Codex pages for recurring people, places, items, factions, powers, events, and lore.
5. Reconcile `Codex/Lore/Open Threads.md`; do not delete old hooks, mark resolved instead.
6. Link session facts to stable Codex entries and stable Codex entries back to the session.
7. Verify embedded images with:

```bash
python3 .agents/skills/openai-image-gen/scripts/verify_markdown_images.py Adventures/YYYY-MM-DD.md
```

## Images

Session images belong in `Adventures/YYYY-MM-DD/` with stable descriptive names such as:

- `YYYY-MM-DD_forest-long-rest-camp.png`
- `YYYY-MM-DD_harpy-nest-reveal.png`
- `YYYY-MM-DD_ritual-stone-door.png`

Generate or queue an image for new meaningful locations, camp scenes, travel context shifts, combats, rituals, reveals, strange magical experiments, recurring entities, and important items.

Use `Codex/Images/Campaign Visual Style Guide.md` as the style source. For character-heavy images, pass existing Codex portraits as references whenever possible.

## Link Discipline

Use Markdown links for Codex entries and canonical files whenever a named person, place, item, faction, event, power, lore topic, or open thread is referenced in a stable section.

Examples:

- `[Kagrenac](../Codex/Characters/The%20Astral%20Elf.md)`
- `[Brother Taleesh](../Codex/Characters/Brother%20Taleesh.md)`
- `[Agland's Sealed Letter](../Codex/Items/Aglands%20Sealed%20Letter.md)`
- `[Open Threads](../Codex/Lore/Open%20Threads.md)`

During rapid live notes, plain names are acceptable briefly, but cleanup should add links where practical.

## Canon Discipline

- Treat the repository as source of truth unless the user corrects it.
- Separate confirmed fact from inference, rumor, and uncertainty.
- Never silently upgrade inference into canon.
- If sources conflict, prefer explicit user correction, then latest confirmed in-play event, then curated Codex, then session notes, then prep/module notes, then earlier inference.
- Record contradictions with `[To verify]` or `[Retcon]` rather than hiding them.
- Mark player-controlled characters explicitly using the roster convention in `Codex/Lore/Table Roster.md`.

---
name: start-adventure
description: Start a new D&D campaign adventure/session log in this repository. Use when the user asks to begin, start up, open, prep, or create a new adventure/session file, especially when they want a "what happened last time" recap, unresolved hooks, current character state, and in-character prompts before play.
---

# Start Adventure

## Overview

Create a new adventure file that is useful at the table immediately: a clean starting-state snapshot, a concise recap, open points, character-facing prompts, and a ready place for live notes.

Use repository evidence first. Do not invent missing continuity; mark it with `[To verify]`.

## Workflow

1. Determine the session date from the user or environment. Use `Adventures/YYYY-MM-DD.md`; if that file already exists for a distinct session, use a clear suffix such as `Adventures/YYYY-MM-DD-2.md`.
2. Inspect the most recent prior adventure log, `Character/Current State.md`, `Character/Inventory.md`, `Character/Relationships.md`, `Character/Timeline.md`, and `Codex/Lore/Open Threads.md`.
3. Extract only player-usable context:
   - last session's 5-8 most important beats
   - current location, objective, resources, items, and conditions
   - urgent open threads and useful next actions
   - relationship tensions, secrets, character-only knowledge, and roleplay hooks
   - any unresolved contradictions or details to verify early in play
4. Create the new adventure file with the structure below. Keep it compact enough to scan during a live session.
5. Update the prior adventure's `Next session` link when there is an unambiguous previous session.
6. Create `Adventures/YYYY-MM-DD/` only when images, maps, handouts, or session media are needed.
7. If the new session starts in a new meaningful location or introduces a visual beat, generate or queue the image according to the repository image workflow. If startup only recaps known context, do not invent an image requirement.
8. Before finishing, verify that every linked file and embedded image path exists.
9. Commit the session-start scaffold early once the file, links, and any required startup image references are valid. Use a scoped message such as `session: start YYYY-MM-DD adventure log`, and stage only the startup files and assets.

## File Template

Use this structure unless the repository already has a better local pattern:

```md
# Session - YYYY-MM-DD

## What Happened Last Time
- ...

## Open Points
- [Open] ...
- [To verify] ...

## Get Into Character
- ...

## Starting State
- Location:
- Immediate goal:
- Important active conditions/resources:
- Key items:
- Key relationship tensions:

## Links
- Previous session: [Session - YYYY-MM-DD](./YYYY-MM-DD.md)
- Next session: TBD
- Open Threads: ../Codex/Lore/Open%20Threads.md

## Summary
- Filled after play.

## Live Notes (chronological)
- Session opens here.

## Character State Changes
- None recorded yet.

## New Canon / Important Discoveries
- None recorded yet.

## Open Threads
- Carry forward:

## Images
- None yet.
```

## Recap Guidance

Write the recap as a player briefing, not a lore dump. Favor short bullets that answer:

- Where are we?
- What are we trying to do?
- What changed last session?
- What danger, obligation, or uncertainty is immediately in front of us?
- What does the tracked character know that the whole party may not?

Keep knowledge tags such as `[Party]`, `[Character-only]`, `[Inferred]`, `[Rumor]`, and `[To verify]`.

## Character Prompt Guidance

The `Get Into Character` section should help the player play the character in the first ten minutes of the session. Include 3-6 prompts such as:

- a private question the character might want answered
- a social angle to test with an NPC or party member
- a strange magic, item, or environmental detail to watch for
- a personal motive that could color the next decision
- a concise line or attitude the player can use at the table

Keep these grounded in confirmed notes and current open threads.

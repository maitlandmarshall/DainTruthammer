---
name: campaign-markdown
description: Edit this campaign repository's Markdown files with strong internal linking, Codex cross-references, knowledge tags, clean relative paths, table roster markings, and Markdown image verification. Use when creating or updating Codex, Character, Adventure, Lore, Event, Item, Place, Faction, Power, or Rules markdown.
---

# Campaign Markdown

## Overview

Make every campaign Markdown file navigable, evidence-aware, and easy to use at the table. Prefer explicit links over plain names in stable prose.

When referencing a Codex item, character, place, faction, event, power, rule, lore page, table roster, or open thread, hyperlink to it whenever the target page exists.

## Link Rules

1. Use normal Markdown links with relative paths.
2. URL-encode spaces as `%20` inside link targets.
3. Link the first meaningful mention in a section; repeated mentions can remain plain if the section is short.
4. In stable Codex and Character pages, always link related entries under `## Related Entries`.
5. In adventure logs, link stable references in `Links`, `Starting State`, `Open Threads`, `Images`, summaries, and cleanup sections. During rapid `Live Notes`, links are useful but speed can win temporarily.
6. If a page should exist but does not, either create a concise placeholder page or mark the reference `[To verify]` rather than inventing details.

Examples:

- `[Dain Truthammer](../Characters/Dain%20Truthammer.md)`
- `[Kagrenac](../Characters/The%20Astral%20Elf.md)`
- `[Brother Taleesh](../Characters/Brother%20Taleesh.md)`
- `[Hammerton Harry Drizddon](../Characters/Hammerton%20Harry%20Drizddon.md)`
- `[Agland's Sealed Letter](../Items/Aglands%20Sealed%20Letter.md)`
- `[Truthammer's Leaky Tent](../Powers/Truthammer%20Leaky%20Tent.md)`
- `[Table Roster](../Lore/Table%20Roster.md)`
- `[Open Threads](../Lore/Open%20Threads.md)`

## Common Relative Paths

From `Codex/Characters/Foo.md`:

- `../Items/Item%20Name.md`
- `../Places/Place%20Name.md`
- `../Lore/Open%20Threads.md`
- `../../Character/Relationships.md`
- `../../Adventures/YYYY-MM-DD.md`

From `Adventures/YYYY-MM-DD.md`:

- `../Codex/Characters/Name.md`
- `../Codex/Items/Item%20Name.md`
- `../Codex/Lore/Open%20Threads.md`
- `../Character/Current%20State.md`

From `Character/Relationships.md`:

- `../Codex/Characters/Name.md`
- `../Codex/Lore/Table%20Roster.md`

From `Codex/Brainstorm/Lore/Foo.md`:

- `../../Lore/Canon%20Lore%20Page.md`
- `../../Characters/Name.md`
- `../../Powers/Canon%20Power.md`
- `../Powers/Brainstorm%20Power.md`
- `./Sibling%20Brainstorm%20Page.md`
- `../../Lore/Open%20Threads.md`

From `Codex/Brainstorm/Powers/Foo.md`:

- `../../Powers/Canon%20Power.md`
- `../../Lore/Canon%20Lore%20Page.md`
- `../../Characters/Name.md`
- `../Lore/Brainstorm%20Lore.md`
- `../../Lore/Open%20Threads.md`

## Codex Page Standards

Use concise, scannable sections:

```md
# Name

![Reference image](./Name_ref.png)

## One-Line Summary
...

## Table Role
- Role: Player Character / DM-controlled / NPC / Unknown.
- Player: ...
- DM: ...

## Status
- [Confirmed] ...
- [To verify] ...

## What Dain Knows
- ...

## What The Party Knows
- ...

## What Is Uncertain
- ...

## Description
- ...

## Notable Events
- YYYY-MM-DD: ... [Session YYYY-MM-DD](../../Adventures/YYYY-MM-DD.md)

## Related Entries
- ...
```

Use `## Table Role` for character pages. Player characters must explicitly name the player and known aliases. DM-controlled people should say `DM-controlled / NPC`.

## Brainstorm Staging Pages

Use `Codex/Brainstorm/` for speculative ideas, mechanical drafts, backstory variants, cosmology proposals, and non-canon design packets.

Do not place idea-stage pages directly in canonical shelves like `Codex/Lore/`, `Codex/Powers/`, `Codex/Items/`, `Codex/Characters/`, `Codex/Places/`, `Codex/Factions/`, `Codex/Events/`, or `Codex/Rules/`.

Every brainstorm page should include:

```md
## Status
- [DM-private] [To verify] Idea-stage only...
- [To verify] Not canon unless approved...

## Brainstorm Routing
- Current shelf: [Brainstorm](../README.md)
- Proposed canon shelf if approved: `Codex/Lore/Name.md`
- Promotion requirement: explicit user/DM approval...
```

Promotion workflow:

1. Get explicit user and/or DM approval for what becomes true.
2. Decide knowledge boundaries with the normal tags.
3. Move or split approved material into the proper canonical shelf.
4. Rewrite status sections so approved facts become confirmed and unresolved ideas stay marked.
5. Update affected canonical pages and state files.
6. Generate or embed canonical images only after approval, unless the user explicitly asks for concept art.
7. Reconcile `Codex/Lore/Open Threads.md`.
8. Commit the promoted packet once links, state changes, and images are clean.

## Knowledge Tags

Use inline tags where they protect canon boundaries:

- `[Party]`: known by the party in-world.
- `[Character-only]`: known only by Dain or the tracked character.
- `[NPC-only]`: known by an NPC or outside party.
- `[DM-private]`: prep/table information not known in-world.
- `[Inferred]`: reasoned but not explicit.
- `[Rumor]`: uncertain in-world claim.
- `[To verify]`: unresolved detail.
- `[Retcon]`: later correction to an earlier assumption.

Do not remove uncertainty markers without evidence.

## Images

- Use relative Markdown image links.
- Codex references usually live beside the page: `![Name portrait](./Name_portrait.png)`.
- Adventure/session images live under `Adventures/YYYY-MM-DD/`.
- If an image is referenced, verify the path exists before finishing.

Verification:

```bash
python3 .agents/skills/openai-image-gen/scripts/verify_markdown_images.py path/to/file.md
```

## Editing Discipline

- Keep edits localized.
- Preserve chronology in adventure logs.
- Prefer bullets over dense prose for in-play reference.
- Do not invent connective facts to make links feel tidy.
- When a Codex page gets a new fact from a session, link back to the session.
- When a session references a stable Codex entry during cleanup, link to the Codex page.
- Maintain `Codex/Lore/Table Roster.md` for player mappings and keep character `## Table Role` sections consistent with it.

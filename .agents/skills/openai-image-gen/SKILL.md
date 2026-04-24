---
name: openai-image-gen
description: Generate and save images/panels for Obsidian-style campaign logs and lore entries using the OpenAI Images API (gpt-image-2) with OPENAI_API_KEY from .env.
---

# OpenAI Image Generation (Panels + Portraits)

Use this skill whenever the game rules require **frequent image generation** (scene panels, action shots, character portraits) and you need to **save the image to the repo**, **use canon reference images**, and **embed the result into Markdown**.

This repository uses this local skill from `.agents/skills/openai-image-gen/`. Do not use legacy skill paths in examples or commands for this repo.

## Quickstart

Generate a new image from text:
- `python3 .agents/skills/openai-image-gen/scripts/generate_image.py --prompt "..." --out "Adventures/2026-04-18/001_establishing.png"`

Generate a **scene panel** that keeps characters consistent. In this repo, `generate_panel.py` can auto-resolve embedded images from `Codex/Characters/*.md`:
- `python3 .agents/skills/openai-image-gen/scripts/generate_panel.py --character "Dain Truthammer" --character "The Astral Elf" --prompt "..." --out "Adventures/2026-04-18/010_squad_encounter.png" --size 1536x1024`

Check which references will be used before spending an API call:
- `python3 .agents/skills/openai-image-gen/scripts/generate_panel.py --character "Dain Truthammer" --character "The Astral Elf" --prompt "..." --out "tmp/check.png" --dry-run`

Generate using reference images (for visual continuity) via the edits endpoint:
- `python3 .agents/skills/openai-image-gen/scripts/generate_image.py --prompt "..." --input-image "Codex/Characters/Dain_Truthammer_portrait_v3.png" --input-image "Codex/Items/Ghostly_Form_Tattoo_ref_v2.png" --out "Adventures/2026-04-18/002_action.png" --size 1536x1024`

When using reference images, prefer existing codex portraits, item references, place references, and prior scene panels before relying on text-only memory.

## Timeouts and retries

Image edits with multiple reference images can run longer than the default HTTP timeouts used by many scripts. This skill's `generate_image.py` supports:

- `--timeout 600`: read timeout per OpenAI request, default `600`.
- `--connect-timeout 30`: connection timeout, default `30`.
- `--retries 2`: retries for timeouts, connection errors, and retryable HTTP statuses.
- `--retry-delay 5`: base delay between retries.

For large comic pages or reference-heavy edits, use a longer timeout:

```bash
python3 .agents/skills/openai-image-gen/scripts/generate_image.py \
  --prompt "..." \
  --input-image "Codex/Characters/Dain_Truthammer_portrait_v3.png" \
  --out "Adventures/2026-04-18/comic-page-01.png" \
  --size 1536x1024 \
  --timeout 900 \
  --retries 3
```

The same timeout and retry flags pass through `generate_panel.py`.

## Async and batching

For independent images, run several `generate_image.py` or `generate_panel.py` commands in parallel shell sessions. Keep each command writing to a distinct output path.

Use `--n` for variants of the same prompt:

```bash
python3 .agents/skills/openai-image-gen/scripts/generate_image.py \
  --prompt "..." \
  --out "Codex/Characters/Commander_Agland_portrait.png" \
  --n 3
```

When `--n` is greater than `1`, the script writes numbered siblings such as `Commander_Agland_portrait_01.png`, `Commander_Agland_portrait_02.png`, and so on. Select one, embed it in the markdown page, and keep the rest only if useful.

## Embedding into logs (Obsidian-friendly)

Embed panels and references with relative markdown links:
- `![Caption](./2026-04-18/001_establishing.png)`
- `![Reference image](./Commander_Agland_portrait.png)`

After editing markdown, verify image links:

```bash
python3 .agents/skills/openai-image-gen/scripts/verify_markdown_images.py \
  Adventures/2026-04-18.md \
  Codex/Characters/Commander\ Agland.md
```

## Prompting rules (to keep the world consistent)

- Use `Codex/Images/Campaign Visual Style Guide.md` as the style source for this campaign.
- Prefer concrete, visual descriptions (lighting, materials, camera, mood).
- For known entities: describe their consistent features + pass their existing images as `--input-image`.
- For comic pages: specify panel count/layout, key beats, recurring references, and `no generated text` unless the user explicitly wants lettering.
- If the prompt needs readable words, expect to inspect and possibly regenerate; image models often distort small text.

## Environment

- Reads `OPENAI_API_KEY` from the environment.
- If not present, tries to load it from a repo `.env` file (simple `KEY=VALUE` parsing).
- Never print, commit, or summarize `.env` values.

## Scripts

- `scripts/generate_image.py`: Create an image using `gpt-image-2` by default, retry slow requests, and write the output directly to disk.
- `scripts/generate_panel.py`: Wrapper that resolves character reference images from this repo's `Codex/Characters` layout or older `codex/worlds` layouts, supports `--dry-run`, then calls `generate_image.py` with `--input-image` for visual consistency.
- `scripts/verify_markdown_images.py`: Verify that all image links in a Markdown file exist on disk.

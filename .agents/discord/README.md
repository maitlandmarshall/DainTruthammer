# Discord adventure posts

Maitland authorised adventure-log captions and generated campaign images to be posted as play progresses on 2026-10-03. The destination is [THe](https://discord.com/channels/958554312185884723/1497086827365142530), a thread in **#when-dnd** in **Goblin Time 69!**.

## Current route: the verified webhook

Maitland supplied a webhook on 2026-10-03 and requested that it be remembered outside the repository. It is saved in Windows Credential Manager for the current Windows user. The live verification authenticated successfully and matched the authorised server and **#when-dnd** parent channel. Do not copy the credential into repository files, memory notes or logs, or print it.

1. Finish each event and its scene images, then write a concise party-facing caption in a new `.agents/discord/outbox/<date>-<sequence>-<scene>.json` entry.
2. Commit the caption, event and images together. The configured local post-commit hook sends pending committed entries to **THe** automatically.
3. Confirm the publisher reports a successful send and readback. It checks the exact caption, thread, webhook, attachment filenames and sizes.
4. Run `python -B .agents/discord/publish.py archive-receipts`, then commit `.agents/discord/delivered.json` with the session's delivery note. Delivery history prevents earlier desktop posts or webhook posts from being replayed.

Posting runs when this checkout creates a commit. It does not watch arbitrary file edits or require the Discord desktop app to remain open. The hook configuration is local to this checkout; the saved credential remains available across sessions and checkouts for the same Windows user on this computer.

## Credential storage

The nonsecret Windows Credential Manager target is `Truthammer/Discord/958554312185884723/1497086827365142530`. [credential_store.py](credential_store.py) reads this generic credential, using persistence across logons on the same computer as described by [Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw). This does not make the credential available on a different computer.

The publisher first accepts an explicit process environment setting, `DISCORD_ADVENTURE_WEBHOOK_URL`, then reads Credential Manager. It never reads the webhook from the repository's `.env`. Keep the URL outside the repository, including ignored files. Future agents can use `verify` without requesting the URL again on this computer.

Migration verified on 2026-10-03: the saved credential matched its readback, the repository `.env` setting was removed, and a fresh publisher process authenticated successfully through Credential Manager. All twelve offline tests passed after the change.

## Desktop fallback

Before the supplied webhook, the signed-in desktop account's inspected settings did not expose webhook creation. Its thread composer successfully posted captions and images. No user account token is used.

If the webhook is unavailable, inspect pending receipts before using the native app through the installed computer-use skill. Preserve an existing user draft and do not repeat an uncertain send.

1. Archive the event and finish its scene image. Write a short, party-facing caption in a new `.agents/discord/outbox/<date>-<sequence>-<scene>.json` file. Use a unique ID and committed image paths under `Adventures/`.
2. Commit the caption, event and images together. Run `python -B .agents/discord/publish.py preview` to see undelivered committed posts.
3. Read the computer-use skill and observe the native Discord window. Verify the server, parent channel and thread URL before sending. Use the observed thread composer for the caption and its upload button/file chooser for images. Preserve an existing user draft rather than overwriting it. Re-observe focus, attachment previews and the destination before sending.
4. Verify the posted caption and images in the thread. Obtain the message ID from the accessibility tree or Copy Message Link, then run:

   ```powershell
   python -B .agents/discord/publish.py record-ui <post-id> https://discord.com/channels/958554312185884723/1497086827365142530/<message-id>
   ```

5. Commit `.agents/discord/delivered.json`. Delivery history prevents another checkout from replaying earlier posts. The command records the agent's visual verification; it does not independently inspect Discord.

The Dain and Harry images already posted by Maitland are not queued again. The initial queue entry adds a caption beneath those images.

Live desktop verification: [the opening recap](https://discord.com/channels/958554312185884723/1497086827365142530/1555768895921717391) was posted and read back through the native app on 2026-10-03. The next [displacer-beast encounter post](https://discord.com/channels/958554312185884723/1497086827365142530/1555770997817217128) verified a caption and a new scene-image upload together.

Live webhook verification: the local post-commit hook sent [the current-session recap](https://discord.com/channels/958554312185884723/1497086827365142530/1555796612998234236) on 2026-10-03. The API response and subsequent message readback matched THe, the webhook, exact caption and empty attachment list. The eight offline publisher tests also passed. This recap established live text delivery; the first webhook image upload was still to verify at that point.

Live webhook image verification: the hook subsequently posted [the continuing tent-meditation scene](https://discord.com/channels/958554312185884723/1497086827365142530/1555800651194310718) with `tent-and-gas-meditation.png` (**2,538,092 bytes**) on 2026-10-03. The response and separate message readback verified the exact caption, THe destination, webhook, attachment filename and byte size. Both live text and image delivery are now established; the private character reflection was excluded from the caption.

Native upload detail: the Windows Open picker appeared as an owned dialogue in the Discord window's `get_window_state`, without a separate `list_windows` entry. Set the observed **File name** edit to the committed image's absolute path, refresh to verify its value and focus, then press Return to accept the file. Wait for its attachment preview before adding the caption. Refresh after sending until a numeric message ID and the rendered image appear; an upload progress bar is not confirmed delivery. Do not reuse Open-button indexes or coordinates that belong to a different window.

## Post format

```json
{
  "id": "2026-10-03-002-next-scene",
  "content": "**Truthammer — 3 October 2026**\n\nA concise account of the confirmed scene.",
  "images": ["Adventures/2026-10-03/next-scene.png"]
}
```

Keep captions below 2,000 characters and avoid mentions. Do not publish credentials, raw prompts, technical setup notes, DM-private material or unsupported character knowledge. Corrections use a new ID; do not alter a delivered entry. Do not backfill old sessions unless requested.

## Webhook commands

The configured webhook belongs to **#when-dnd**, parent channel `1017211804184743997`. Its URL stays in Windows Credential Manager outside the repository. Never print or commit that value.

```powershell
python -B .agents/discord/publish.py verify
python -B .agents/discord/publish.py publish
python -B .agents/discord/publish.py archive-receipts
```

The publisher verifies the webhook's server and parent channel, sends with `thread_id=1497086827365142530`, and reads the message back from that thread. It uploads committed images using multipart form data and disables mentions. The tracked post-commit hook runs it when configured; otherwise it reports how many posts await desktop delivery. After successful webhook delivery, commit the archived receipts as part of the agent's cleanup.

The local hook is enabled with `git config --local core.hooksPath .agents/hooks`; do not replace an existing custom hooks configuration without preserving it.

## Delivery failures

Campaign commits still succeed if Discord delivery fails. Report pending delivery plainly. Receipts and the publisher lock live in the ignored `.agents/discord/state/` directory. A send with no readable response remains uncertain and will not be retried automatically: inspect the target thread before recording the observed message or clearing a rejected send. A message ID saved before a failed readback lets the next run verify that message without sending another copy.

If a process exits unexpectedly and leaves a lock, confirm that no publisher is running before removing that exact lock file. Never clear receipts merely to make a test pass. Native-app posting is a fallback after the webhook's receipt state has been checked.

## Validation

```powershell
python -B -m unittest discover -s .agents/discord -p 'test_*.py'
```

Tests use temporary local repositories, mocked credential reads and a fake Discord API. They verify external credential lookup, exclusion of repository `.env` credentials, committed uploads, thread routing, destination rejection, duplicate prevention, uncertain sends, readback recovery and archived desktop receipts. No test posts to Discord or accesses the real saved credential.

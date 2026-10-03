# Discord adventure posts

Maitland authorised adventure-log captions and generated campaign images to be posted as play progresses on 2026-10-03. The destination is [THe](https://discord.com/channels/958554312185884723/1497086827365142530), a thread in **#when-dnd** in **Goblin Time 69!**.

## Current route: the Discord desktop app

The signed-in desktop account can use the thread composer. Its server settings do not expose Integrations or Webhooks, and the parent channel's context menu does not expose Edit Channel. Webhook creation was therefore unavailable in the inspected UI. No user account token is used.

During active campaign turns, the agent sends each finished beat through the native app using the installed computer-use skill. This saves Maitland from copying captions and uploading images. It depends on the signed-in app being available during the turn; it is not an unattended background service.

1. Archive the event and finish its scene image. Write a short, party-facing caption in a new `.agents/discord/outbox/<date>-<sequence>-<scene>.json` file. Use a unique ID and committed image paths under `Adventures/`.
2. Commit the caption, event and images together. Run `python -B .agents/discord/publish.py preview` to see undelivered committed posts.
3. Read the computer-use skill and observe the native Discord window. Verify the server, parent channel and thread URL before sending. Use the observed thread composer for the caption and its upload button/file chooser for images. Preserve an existing user draft rather than overwriting it. Re-observe focus, attachment previews and the destination before sending.
4. Verify the posted caption and images in the thread. Obtain the message ID from the accessibility tree or Copy Message Link, then run:

   ```powershell
   python -B .agents/discord/publish.py record-ui <post-id> https://discord.com/channels/958554312185884723/1497086827365142530/<message-id>
   ```

5. Commit `.agents/discord/delivered.json`. Delivery history prevents another checkout from replaying earlier posts. The command records the agent's visual verification; it does not independently inspect Discord.

The Dain and Harry images already posted by Maitland are not queued again. The initial queue entry adds a caption beneath those images.

Live verification: [the opening recap](https://discord.com/channels/958554312185884723/1497086827365142530/1555768895921717391) was posted and read back through the native app on 2026-10-03. The next [displacer-beast encounter post](https://discord.com/channels/958554312185884723/1497086827365142530/1555770997817217128) verified a caption and a new scene-image upload together. The webhook route remains covered by offline tests only.

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

## Optional webhook route

A server administrator can create a webhook in **#when-dnd**, parent channel `1017211804184743997`. Store its URL only in the ignored `.env` file as `DISCORD_ADVENTURE_WEBHOOK_URL`. Never print or commit that value.

```powershell
python -B .agents/discord/publish.py verify
python -B .agents/discord/publish.py publish
python -B .agents/discord/publish.py archive-receipts
```

The publisher verifies the webhook's server and parent channel, sends with `thread_id=1497086827365142530`, and reads the message back from that thread. It uploads committed images using multipart form data and disables mentions. The tracked post-commit hook runs it when configured; otherwise it reports how many posts await desktop delivery. After successful webhook delivery, commit the archived receipts as part of the agent's cleanup.

The local hook is enabled with `git config --local core.hooksPath .agents/hooks`; do not replace an existing custom hooks configuration without preserving it.

## Delivery failures

Campaign commits still succeed if Discord delivery fails. Report pending delivery plainly. Receipts and the publisher lock live in the ignored `.agents/discord/state/` directory. A send with no readable response remains uncertain and will not be retried automatically: inspect the target thread before recording the observed message or clearing a rejected send. A message ID saved before a failed readback lets the next run verify that message without sending another copy.

If a process exits unexpectedly and leaves a lock, confirm that no publisher is running before removing that exact lock file. Never clear receipts merely to make a test pass. Native-app posting remains the current route until a webhook is actually configured and verified.

## Validation

```powershell
python -B -m unittest discover -s .agents/discord -p 'test_*.py'
```

Tests use temporary local repositories and a fake Discord API. They verify committed uploads, thread routing, destination rejection, duplicate prevention, uncertain sends, readback recovery and archived desktop receipts. No test posts to Discord.

"""Queue and record campaign posts for Maitland's requested Discord thread."""

import argparse
import hashlib
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


GUILD_ID = "958554312185884723"
PARENT_CHANNEL_ID = "1017211804184743997"
THREAD_ID = "1497086827365142530"
WEBHOOK_SETTING = "DISCORD_ADVENTURE_WEBHOOK_URL"
ROOT = Path(__file__).resolve().parents[2]
OUTBOX = ".agents/discord/outbox"
DELIVERED = ".agents/discord/delivered.json"
USER_AGENT = "DiscordBot (https://github.com/maitlandmarshall/DainTruthammer, 1.0)"


class DeliveryError(Exception):
    """A safe error message that never includes the webhook credential."""


class RequestError(DeliveryError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def git_bytes(root, *args):
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        raise DeliveryError("A queued post or image is missing from the committed archive.") from None


def webhook_url(root):
    value = os.environ.get(WEBHOOK_SETTING, "").strip()
    env_file = root / ".env"
    if not value and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, candidate = line.partition("=")
            if separator and key.strip() == WEBHOOK_SETTING:
                value = candidate.strip().strip("\"'")
                break
    if not value:
        return None

    parsed = urllib.parse.urlsplit(value)
    valid_path = re.fullmatch(r"/api/(?:v10/)?webhooks/\d+/[A-Za-z0-9._-]+", parsed.path)
    if (parsed.scheme != "https" or parsed.netloc != "discord.com"
            or not valid_path or parsed.query or parsed.fragment):
        raise DeliveryError("The local setting must contain a Discord webhook URL, not a channel link.")
    return value


def committed_posts(root):
    paths = git_bytes(root, "ls-tree", "-r", "--name-only", "HEAD", "--", OUTBOX)
    posts = []
    seen_ids = set()
    for path in paths.decode("utf-8").splitlines():
        if not path.endswith(".json"):
            continue
        try:
            entry = json.loads(git_bytes(root, "show", f"HEAD:{path}"))
        except ValueError:
            raise DeliveryError(f"Invalid queued JSON: {path}") from None
        if not isinstance(entry, dict):
            raise DeliveryError(f"Queued JSON must be an object: {path}")
        entry_id = entry.get("id", "")
        content = entry.get("content", "")
        image_paths = entry.get("images", [])
        if not isinstance(entry_id, str) or not re.fullmatch(r"[a-z0-9-]+", entry_id):
            raise DeliveryError(f"Invalid post ID: {path}")
        if entry_id in seen_ids:
            raise DeliveryError(f"Duplicate post ID: {entry_id}")
        if not isinstance(content, str) or not content.strip() or len(content.encode("utf-16-le")) > 4000:
            raise DeliveryError(f"Post {entry_id} needs between 1 and 2,000 characters.")
        if not isinstance(image_paths, list) or len(image_paths) > 10:
            raise DeliveryError(f"Post {entry_id} must have at most ten images.")

        # Read images from the same commit as the caption, never from pending edits.
        images = []
        digest = hashlib.sha256(content.encode("utf-8"))
        for image_path in image_paths:
            if not isinstance(image_path, str):
                raise DeliveryError(f"Invalid image path in {entry_id}.")
            relative = PurePosixPath(image_path)
            if (relative.is_absolute() or ".." in relative.parts or "\\" in image_path
                    or relative.parts[:1] != ("Adventures",)
                    or relative.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}):
                raise DeliveryError(f"Post {entry_id} can only attach images from Adventures/.")
            image = git_bytes(root, "show", f"HEAD:{image_path}")
            if len(image) > 10 * 1024 * 1024:
                raise DeliveryError(f"An image in {entry_id} exceeds the publisher's 10 MiB limit.")
            images.append((relative.name, image))
            digest.update(image_path.encode("utf-8") + b"\0" + image)
        if len({name for name, _ in images}) != len(images):
            raise DeliveryError(f"Post {entry_id} has duplicate attachment names.")
        if sum(len(image) for _, image in images) > 20 * 1024 * 1024:
            raise DeliveryError(f"Post {entry_id} exceeds the publisher's 20 MiB upload limit.")
        seen_ids.add(entry_id)
        posts.append({"id": entry_id, "content": content, "images": images,
                      "fingerprint": digest.hexdigest()})
    return posts


def multipart(post):
    boundary = "truthammer-" + uuid.uuid4().hex
    payload = {"content": post["content"], "username": "Truthammer Adventure Log",
               "allowed_mentions": {"parse": []},
               "attachments": [{"id": index, "filename": name}
                               for index, (name, _) in enumerate(post["images"])]}
    header = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"payload_json\"\r\n"
              "Content-Type: application/json\r\n\r\n")
    chunks = [header.encode("utf-8")
              + json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\r\n"]
    for index, (name, image) in enumerate(post["images"]):
        safe_name = name.replace('"', "_").replace("\r", "_").replace("\n", "_")
        mime_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        header = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files[{index}]\"; "
                  f"filename=\"{safe_name}\"\r\nContent-Type: {mime_type}\r\n\r\n")
        chunks.extend([header.encode("utf-8"), image, b"\r\n"])
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), "multipart/form-data; boundary=" + boundary


def request_json(url, method="GET", body=None, content_type="application/json"):
    request = urllib.request.Request(url, data=body, method=method,
                                     headers={"User-Agent": USER_AGENT, "Content-Type": content_type})
    try:
        with urllib.request.build_opener(NoRedirects()).open(request, timeout=20) as response:
            result = json.loads(response.read())
            if not isinstance(result, dict):
                raise ValueError
            return result
    except urllib.error.HTTPError as error:
        raise RequestError(f"Discord returned HTTP {error.code}.", error.code) from None
    except (OSError, ValueError, urllib.error.URLError):
        # Network errors can contain the full token-bearing URL; keep them private.
        raise RequestError("Discord did not return a readable confirmation.") from None


def verify_destination(url):
    webhook = request_json(url)
    if (str(webhook.get("guild_id")) != GUILD_ID
            or str(webhook.get("channel_id")) != PARENT_CHANNEL_ID
            or webhook.get("type") != 1):
        raise DeliveryError("The webhook must target #when-dnd in the authorised server.")
    return str(webhook["id"])


def verify_message(message, post, webhook_id):
    expected_files = sorted((name, len(image)) for name, image in post["images"])
    actual_files = sorted((file.get("filename"), file.get("size"))
                          for file in message.get("attachments", []))
    if (not re.fullmatch(r"\d+", str(message.get("id", "")))
            or str(message.get("channel_id")) != THREAD_ID
            or str(message.get("webhook_id")) != webhook_id
            or message.get("content") != post["content"]
            or actual_files != expected_files):
        raise DeliveryError(f"Discord's message does not match queued post {post['id']}.")


def save_receipts(path, receipts):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def receipts_for(root):
    """Combine saved delivery history with receipts from the current checkout."""
    tracked = git_bytes(root, "ls-tree", "--name-only", "HEAD", "--", DELIVERED)
    receipts = json.loads(git_bytes(root, "show", f"HEAD:{DELIVERED}")) if tracked.strip() else {}
    local = root / ".agents/discord/state/receipts.json"
    if local.exists():
        receipts.update(json.loads(local.read_text(encoding="utf-8")))
    return receipts


def pending_posts(root):
    receipts = receipts_for(root)
    pending = []
    for post in committed_posts(root):
        prior = receipts.get(post["id"], {})
        if prior and prior.get("fingerprint") != post["fingerprint"]:
            raise DeliveryError(f"Post {post['id']} changed after delivery started; use a new ID for a correction.")
        if prior.get("status") != "confirmed":
            pending.append(post)
    return pending


def archive_receipts(root):
    confirmed = {key: receipt for key, receipt in receipts_for(root).items()
                 if receipt.get("status") == "confirmed"}
    save_receipts(root / DELIVERED, confirmed)


def record_ui(root, post_id, message_url):
    """Record a desktop send only after the agent verifies the visible message."""
    match = re.fullmatch(
        rf"https://discord\.com/channels/{GUILD_ID}/{THREAD_ID}/(\d+)", message_url
    )
    if not match:
        raise DeliveryError("The message link must point to the authorised THe thread.")
    post = next((entry for entry in committed_posts(root) if entry["id"] == post_id), None)
    if post is None:
        raise DeliveryError("The desktop post must already be committed in the outbox.")
    receipts = receipts_for(root)
    if post_id in receipts:
        raise DeliveryError("A delivery receipt already exists; inspect it before recording another send.")
    receipts[post_id] = {"fingerprint": post["fingerprint"], "status": "confirmed",
                         "message_id": match[1], "route": "desktop"}
    save_receipts(root / ".agents/discord/state/receipts.json", receipts)
    archive_receipts(root)
    print(f"Discord desktop delivery recorded: {message_url}")


def publish(root, url):
    """Send pending committed posts and verify previously acknowledged sends."""
    state_dir = root / ".agents/discord/state"
    state_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = state_dir / "receipts.json"
    lock_path = state_dir / "publish.lock"
    try:
        with lock_path.open("x", encoding="utf-8") as lock:
            lock.write(str(os.getpid()))
    except FileExistsError:
        raise DeliveryError("Another publisher holds the delivery lock; no messages were sent.") from None

    try:
        receipts = receipts_for(root)
        pending = pending_posts(root)
        if not pending:
            print("Discord: no new campaign posts.")
            return
        webhook_id = verify_destination(url)

        for post in pending:
            prior = receipts.get(post["id"], {})
            if prior.get("status") == "sending":
                raise DeliveryError(f"Post {post['id']} has an uncertain send; reconcile it before retrying.")
            message_id = prior.get("message_id")
            if not message_id:
                body, content_type = multipart(post)
                # Discord webhooks have no idempotency key. A lost response must not
                # cause the next commit to blindly publish the same message again.
                receipts[post["id"]] = {"fingerprint": post["fingerprint"], "status": "sending"}
                save_receipts(receipt_path, receipts)
                try:
                    query = urllib.parse.urlencode({"wait": "true", "thread_id": THREAD_ID})
                    message = request_json(url + "?" + query, "POST", body, content_type)
                except RequestError as error:
                    if error.status in {400, 401, 403, 404, 405, 413, 429}:
                        receipts.pop(post["id"])
                        save_receipts(receipt_path, receipts)
                    raise
                message_id = str(message.get("id", ""))
                if not re.fullmatch(r"\d+", message_id):
                    raise DeliveryError(f"Post {post['id']} has no confirmed message ID; reconcile before retrying.")
                receipts[post["id"]].update(status="sent", message_id=message_id)
                save_receipts(receipt_path, receipts)
                verify_message(message, post, webhook_id)

            message = request_json(url + "/messages/" + message_id + "?thread_id=" + THREAD_ID)
            verify_message(message, post, webhook_id)
            receipts[post["id"]]["status"] = "confirmed"
            save_receipts(receipt_path, receipts)
            print(f"Discord posted {post['id']}: https://discord.com/channels/{GUILD_ID}/{THREAD_ID}/{message_id}")
    finally:
        lock_path.unlink()


def main():
    # Windows shell output must preserve the same punctuation as the queued caption.
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preview", "verify", "publish", "record-ui", "archive-receipts"])
    parser.add_argument("post_id", nargs="?")
    parser.add_argument("message_url", nargs="?")
    parser.add_argument("--if-configured", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "record-ui":
            record_ui(ROOT, args.post_id, args.message_url or "")
            return 0
        if args.action == "archive-receipts":
            archive_receipts(ROOT)
            return 0
        if args.action == "preview":
            for post in pending_posts(ROOT):
                print(json.dumps({"id": post["id"], "content": post["content"],
                                  "images": [name for name, _ in post["images"]]}, ensure_ascii=False, indent=2))
            return 0
        url = webhook_url(ROOT)
        if not url:
            if args.if_configured:
                count = len(pending_posts(ROOT))
                print(f"Discord desktop: {count} committed post(s) awaiting delivery.")
                return 0
            raise DeliveryError("Save the channel webhook URL in the ignored local .env file first.")
        if args.action == "verify":
            verify_destination(url)
            print(f"Discord webhook verified for #when-dnd; posts will target thread {THREAD_ID}.")
        else:
            publish(ROOT, url)
        return 0
    except (DeliveryError, OSError, ValueError) as error:
        # Only our own errors are safe to print; unexpected library errors may carry secrets.
        print(str(error) if isinstance(error, DeliveryError) else "Local publisher state needs attention.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

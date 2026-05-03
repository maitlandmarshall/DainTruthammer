from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


def _env_float(name: str, default: float) -> float:
	raw = os.environ.get(name)
	if not raw:
		return default
	try:
		return float(raw)
	except ValueError:
		return default


def _env_int(name: str, default: int) -> int:
	raw = os.environ.get(name)
	if not raw:
		return default
	try:
		return int(raw)
	except ValueError:
		return default


def _guess_mimetype(path: Path) -> str:
	s = path.suffix.lower()
	if s == ".png":
		return "image/png"
	if s in {".jpg", ".jpeg"}:
		return "image/jpeg"
	if s == ".webp":
		return "image/webp"
	return "application/octet-stream"


def _find_repo_root(start: Path) -> Path:
	cur = start.resolve()
	for _ in range(10):
		if (cur / ".git").exists() or (cur / ".env").exists():
			return cur
		if cur.parent == cur:
			break
		cur = cur.parent
	return start.resolve()


def _load_dotenv_if_needed(repo_root: Path) -> None:
	if os.environ.get("OPENAI_API_KEY"):
		return
	env_path = repo_root / ".env"
	if not env_path.exists():
		return
	for line in env_path.read_text(encoding="utf-8").splitlines():
		line = line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, val = line.split("=", 1)
		key = key.strip()
		val = val.strip().strip("\"'")  # minimal parsing
		if key and not os.environ.get(key):
			os.environ[key] = val


def _post_with_retries(
	url: str,
	api_key: str,
	*,
	timeout: tuple[float, float],
	retries: int,
	retry_delay: float,
	json_payload: dict[str, Any] | None = None,
	form_data: dict[str, Any] | None = None,
	files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
) -> dict[str, Any]:
	last_error: Exception | None = None
	attempts = retries + 1
	for attempt in range(1, attempts + 1):
		try:
			resp = requests.post(
				url,
				headers={"Authorization": f"Bearer {api_key}"},
				json=json_payload,
				data=form_data,
				files=files,
				timeout=timeout,
			)
			if resp.status_code < 400:
				return resp.json()
			err = RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")
			if resp.status_code not in RETRYABLE_STATUS_CODES or attempt >= attempts:
				raise err
			last_error = err
		except (
			requests.exceptions.Timeout,
			requests.exceptions.ConnectionError,
			requests.exceptions.ChunkedEncodingError,
		) as e:
			last_error = e
			if attempt >= attempts:
				raise RuntimeError(f"OpenAI request failed after {attempt} attempt(s): {e}") from e

		if retry_delay > 0:
			time.sleep(retry_delay * attempt)

	if last_error:
		raise last_error
	raise RuntimeError("OpenAI request failed for an unknown reason")


def _openai_post_json(
	url: str,
	payload: dict[str, Any],
	api_key: str,
	*,
	timeout: tuple[float, float],
	retries: int,
	retry_delay: float,
) -> dict[str, Any]:
	return _post_with_retries(
		url,
		api_key,
		json_payload=payload,
		timeout=timeout,
		retries=retries,
		retry_delay=retry_delay,
	)


def _openai_post_multipart(
	url: str,
	data: dict[str, Any],
	files: list[tuple[str, tuple[str, bytes, str]]],
	api_key: str,
	*,
	timeout: tuple[float, float],
	retries: int,
	retry_delay: float,
) -> dict[str, Any]:
	return _post_with_retries(
		url,
		api_key,
		form_data=data,
		files=files,
		timeout=timeout,
		retries=retries,
		retry_delay=retry_delay,
	)


def _write_b64_image(out_path: Path, b64_json: str) -> None:
	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_bytes(base64.b64decode(b64_json))


def _is_model_not_found(err: Exception) -> bool:
	msg = str(err).lower()
	return ("model" in msg and "not found" in msg) or ("model_not_found" in msg)


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--prompt", required=True)
	parser.add_argument("--out", required=True, help="Output image path (.png/.jpg based on --output-format)")
	parser.add_argument("--model", default="gpt-image-2")
	parser.add_argument("--fallback-model", default="gpt-image-1.5")
	parser.add_argument("--size", default="1024x1024")
	parser.add_argument("--quality", default="high", choices=["low", "medium", "high"])
	parser.add_argument("--output-format", default="png", choices=["png", "jpeg", "webp"])
	parser.add_argument("--background", default=None, choices=[None, "transparent", "opaque"])
	parser.add_argument("--n", type=int, default=1, help="Number of images to request (writes *_01, *_02... if >1)")
	parser.add_argument("--input-image", action="append", default=[], help="Reference images for edits endpoint")
	parser.add_argument("--mask", default=None, help="Optional mask image path for edits endpoint")
	parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com"))
	parser.add_argument("--connect-timeout", type=float, default=_env_float("OPENAI_IMAGE_CONNECT_TIMEOUT", 30.0))
	parser.add_argument("--timeout", type=float, default=_env_float("OPENAI_IMAGE_READ_TIMEOUT", 600.0), help="Read timeout in seconds for each OpenAI request")
	parser.add_argument("--retries", type=int, default=_env_int("OPENAI_IMAGE_RETRIES", 2), help="Retry count for timeouts, connection errors, and retryable HTTP statuses")
	parser.add_argument("--retry-delay", type=float, default=_env_float("OPENAI_IMAGE_RETRY_DELAY", 5.0), help="Base delay in seconds between retries")
	args = parser.parse_args()

	repo_root = _find_repo_root(Path(__file__))
	_load_dotenv_if_needed(repo_root)

	api_key = os.environ.get("OPENAI_API_KEY")
	if not api_key:
		raise SystemExit("Missing OPENAI_API_KEY (set env var or add it to repo .env)")

	out_path = Path(args.out)
	if args.n < 1 or args.n > 10:
		raise SystemExit("--n must be between 1 and 10")
	if args.timeout <= 0 or args.connect_timeout <= 0:
		raise SystemExit("--timeout and --connect-timeout must be positive")
	if args.retries < 0:
		raise SystemExit("--retries must be 0 or greater")

	use_edits = len(args.input_image) > 0 or args.mask is not None
	endpoint = "/v1/images/edits" if use_edits else "/v1/images/generations"
	url = args.base_url.rstrip("/") + endpoint
	request_timeout = (args.connect_timeout, args.timeout)

	def run_with_model(model_name: str) -> dict[str, Any]:
		if use_edits:
			files: list[tuple[str, tuple[str, bytes, str]]] = []
			for p in args.input_image:
				pp = Path(p)
				files.append(("image[]", (pp.name, pp.read_bytes(), _guess_mimetype(pp))))
			if args.mask:
				mp = Path(args.mask)
				files.append(("mask", (mp.name, mp.read_bytes(), _guess_mimetype(mp))))
			data: dict[str, Any] = {
				"model": model_name,
				"prompt": args.prompt,
				"size": args.size,
				"quality": args.quality,
				"output_format": args.output_format,
				"n": str(args.n),
			}
			if args.background:
				data["background"] = args.background
			return _openai_post_multipart(
				url,
				data=data,
				files=files,
				api_key=api_key,
				timeout=request_timeout,
				retries=args.retries,
				retry_delay=args.retry_delay,
			)

		payload: dict[str, Any] = {
			"model": model_name,
			"prompt": args.prompt,
			"size": args.size,
			"quality": args.quality,
			"output_format": args.output_format,
			"n": args.n,
		}
		if args.background:
			payload["background"] = args.background
		return _openai_post_json(
			url,
			payload=payload,
			api_key=api_key,
			timeout=request_timeout,
			retries=args.retries,
			retry_delay=args.retry_delay,
		)

	try:
		result = run_with_model(args.model)
		model_used = args.model
	except Exception as e:
		if args.fallback_model and _is_model_not_found(e):
			result = run_with_model(args.fallback_model)
			model_used = args.fallback_model
		else:
			raise

	data = result.get("data") or []
	if not isinstance(data, list) or len(data) == 0:
		raise SystemExit(f"Unexpected response shape (no data): {result}")

	stem = out_path.stem
	suffix = out_path.suffix or f".{args.output_format}"
	parent = out_path.parent

	written: list[str] = []
	for idx, item in enumerate(data, start=1):
		b64_json = item.get("b64_json")
		if not b64_json:
			raise SystemExit(f"Unexpected response item (missing b64_json): {item}")
		target = out_path
		if args.n > 1:
			target = parent / f"{stem}_{idx:02d}{suffix}"
		_write_b64_image(target, b64_json)
		written.append(str(target))

	# Machine-readable summary for agents.
	print(json.dumps({
		"model_used": model_used,
		"endpoint": endpoint,
		"files": written,
		"timeout": args.timeout,
		"connect_timeout": args.connect_timeout,
		"retries": args.retries,
	}))


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		raise
	except Exception as e:
		print(str(e), file=sys.stderr)
		sys.exit(1)

"""Collect public AI-tool candidates for the daily learning workflow.

The collector deliberately keeps discovery deterministic. Codex performs the
semantic explanation and learning-task selection after this file is committed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


GITHUB_API = "https://api.github.com"
HF_API = "https://huggingface.co/api"
LOOKBACK_DAYS = 30
DEDUP_DAYS = 30
MAX_CANDIDATES = 60
TOPICS = ("ai-tools", "ocr", "speech-to-text", "mcp", "rag", "ai-agents")
OFFICIAL_ORGS = ("mistralai", "groq", "openai", "huggingface")
OFFICIAL_REFERENCES = (
    {
        "name": "Mistral Document AI OCR",
        "url": "https://docs.mistral.ai/studio-api/document-processing/basic_ocr",
        "provider": "Mistral AI",
        "capability_tags": ["ocr", "document-ai", "structured-extraction"],
        "description": "Official OCR documentation for structured PDF and image extraction.",
        "input_output": "PDF or image -> Markdown, tables, images, links, blocks, confidence scores",
    },
    {
        "name": "Groq Speech-to-Text",
        "url": "https://console.groq.com/docs/speech-to-text",
        "provider": "Groq",
        "capability_tags": ["speech-to-text", "asr", "transcription", "audio-chunking"],
        "description": "Official speech transcription and translation API documentation.",
        "input_output": "Audio -> text, verbose JSON, segment or word timestamps",
    },
    {
        "name": "OpenAI Cookbook",
        "url": "https://github.com/openai/openai-cookbook",
        "provider": "OpenAI",
        "capability_tags": ["api", "sdk", "structured-output", "agents"],
        "description": "Official API examples and implementation patterns.",
        "input_output": "Task input -> API example and inspectable output",
    },
    {
        "name": "Hugging Face Hub Search",
        "url": "https://huggingface.co/docs/huggingface_hub/guides/search",
        "provider": "Hugging Face",
        "capability_tags": ["models", "spaces", "inference", "search"],
        "description": "Official Hub search and filtering documentation.",
        "input_output": "Task filters -> model, dataset, or Space candidates",
    },
)
HF_TASK_TERMS = (
    "ocr",
    "document",
    "speech",
    "audio",
    "transcrib",
    "text-to-speech",
    "text-to-image",
    "image-to-text",
    "image-text-to-text",
    "agent",
    "embedding",
    "rerank",
    "mcp",
    "multimodal",
    "vision",
)
FetchFn = Callable[[str], dict[str, Any]]


class FetchError(RuntimeError):
    pass


def shanghai_today(now: dt.datetime | None = None) -> str:
    timezone = dt.timezone(dt.timedelta(hours=8))
    current = now or dt.datetime.now(timezone)
    return current.astimezone(timezone).strftime("%Y-%m-%d")


def parse_day(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def fetch_json(url: str, timeout: int = 20) -> dict[str, Any] | list[Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "liangfeng-ai-tool-radar/1.0",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        detail = getattr(exc, "reason", str(exc))
        raise FetchError(f"{url}: {detail}") from exc


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def signal_fingerprint(candidate: dict[str, Any]) -> str:
    signals = candidate.get("signals", {})
    raw = json.dumps(
        {
            "url": candidate["url"],
            "updated_at": signals.get("updated_at"),
            "pushed_at": signals.get("pushed_at"),
            "stars": signals.get("stars"),
            "downloads": signals.get("downloads"),
            "likes": signals.get("likes"),
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def candidate(
    *,
    kind: str,
    name: str,
    url: str,
    provider: str,
    description: str,
    capability_tags: list[str],
    signals: dict[str, Any],
    input_output: str | None = None,
) -> dict[str, Any]:
    normalized = canonical_url(url)
    return {
        "id": f"{kind}:{normalized}",
        "kind": kind,
        "name": name.strip(),
        "url": normalized,
        "provider": provider,
        "description": " ".join(description.split()),
        "capability_tags": sorted({tag.lower() for tag in capability_tags if tag}),
        "input_output": input_output,
        "signals": signals,
        "source": "public_api",
    }


def github_topic_candidates(topic: str, cutoff: str, fetch: FetchFn) -> list[dict[str, Any]]:
    query = f"topic:{topic} stars:>=200 pushed:>={cutoff} archived:false"
    params = urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": 10})
    payload = fetch(f"{GITHUB_API}/search/repositories?{params}")
    results: list[dict[str, Any]] = []
    for item in payload.get("items", []) if isinstance(payload, dict) else []:
        if item.get("archived") or item.get("stargazers_count", 0) < 200:
            continue
        owner = (item.get("owner") or {}).get("login", "")
        provider = owner if owner in OFFICIAL_ORGS else "GitHub"
        results.append(
            candidate(
                kind="github_repository",
                name=item.get("full_name", item.get("name", "unknown")),
                url=item.get("html_url", ""),
                provider=provider,
                description=item.get("description") or "",
                capability_tags=[topic],
                signals={
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "pushed_at": item.get("pushed_at"),
                    "updated_at": item.get("updated_at"),
                    "archived": bool(item.get("archived")),
                },
                input_output="Repository README and examples",
            )
        )
    return results


def github_official_candidates(org: str, cutoff: str, fetch: FetchFn) -> list[dict[str, Any]]:
    payload = fetch(f"{GITHUB_API}/orgs/{org}/repos?sort=updated&direction=desc&per_page=15")
    results: list[dict[str, Any]] = []
    for item in payload if isinstance(payload, list) else []:
        pushed_at = item.get("pushed_at") or ""
        if item.get("archived") or pushed_at[:10] < cutoff:
            continue
        results.append(
            candidate(
                kind="official_repository",
                name=item.get("full_name", item.get("name", "unknown")),
                url=item.get("html_url", ""),
                provider=org,
                description=item.get("description") or "",
                capability_tags=["official", org],
                signals={
                    "stars": item.get("stargazers_count", 0),
                    "pushed_at": pushed_at,
                    "updated_at": item.get("updated_at"),
                    "archived": bool(item.get("archived")),
                },
                input_output="Official repository README and release notes",
            )
        )
    return results[:3]


def official_reference_candidates() -> list[dict[str, Any]]:
    return [
        candidate(
            kind="official_reference",
            name=reference["name"],
            url=reference["url"],
            provider=reference["provider"],
            description=reference["description"],
            capability_tags=reference["capability_tags"],
            signals={"authority": "official", "updated_at": None},
            input_output=reference["input_output"],
        )
        for reference in OFFICIAL_REFERENCES
    ]


def hf_relevant(item: dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            str(item.get("id", "")),
            str(item.get("pipeline_tag", "")),
            " ".join(str(tag) for tag in item.get("tags", []) or []),
        ]
    ).lower()
    return any(term in haystack for term in HF_TASK_TERMS)


def huggingface_candidates(kind: str, fetch: FetchFn) -> list[dict[str, Any]]:
    endpoint = "models" if kind == "hf_model" else "spaces"
    params = urlencode({"sort": "trendingScore", "direction": "-1", "limit": 20})
    payload = fetch(f"{HF_API}/{endpoint}?{params}")
    results: list[dict[str, Any]] = []
    for item in payload if isinstance(payload, list) else []:
        if not hf_relevant(item):
            continue
        repo_id = item.get("id", "unknown")
        url = f"https://huggingface.co/{endpoint}/{repo_id}"
        tags = list(item.get("tags") or [])
        pipeline = item.get("pipeline_tag")
        if pipeline:
            tags.append(pipeline)
        results.append(
            candidate(
                kind=kind,
                name=repo_id,
                url=url,
                provider="Hugging Face",
                description=item.get("description") or f"Trending Hugging Face {endpoint}",
                capability_tags=tags,
                signals={
                    "downloads": item.get("downloads"),
                    "likes": item.get("likes"),
                    "updated_at": item.get("lastModified") or item.get("last_modified"),
                    "pipeline_tag": pipeline,
                },
                input_output=(pipeline or "Hugging Face repository") + " -> inference result",
            )
        )
    return results[:10]


def merge_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in items:
        key = canonical_url(item["url"])
        item["url"] = key
        existing = merged.get(key)
        if not existing:
            merged[key] = item
            continue
        existing["capability_tags"] = sorted(
            set(existing.get("capability_tags", [])) | set(item.get("capability_tags", []))
        )
        existing["signals"]["source_count"] = existing["signals"].get("source_count", 1) + 1
        if len(item.get("description", "")) > len(existing.get("description", "")):
            existing["description"] = item["description"]
    return list(merged.values())


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "items": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "items": {}}
    if not isinstance(value, dict) or not isinstance(value.get("items"), dict):
        return {"schema_version": 1, "items": {}}
    return value


def select_new(
    candidates: list[dict[str, Any]],
    state: dict[str, Any],
    date: str,
    force: bool = False,
) -> list[dict[str, Any]]:
    current = parse_day(date)
    selected: list[dict[str, Any]] = []
    items = state.setdefault("items", {})
    for item in candidates:
        fingerprint = signal_fingerprint(item)
        previous = items.get(item["id"])
        age = 0
        keep = force or not previous
        if previous and not force:
            try:
                age = (current - parse_day(previous.get("last_seen", date))).days
            except (TypeError, ValueError):
                age = DEDUP_DAYS
            keep = age >= DEDUP_DAYS or previous.get("fingerprint") != fingerprint
        if keep:
            item["selection"] = {
                "fingerprint": fingerprint,
                "novel": not bool(previous),
                "dedup_age_days": None if not previous else max(0, age),
            }
            selected.append(item)
            items[item["id"]] = {"last_seen": date, "fingerprint": fingerprint}
    state["schema_version"] = 1
    return selected[:MAX_CANDIDATES]


def collect(date: str, fetch: FetchFn = fetch_json, force: bool = False) -> tuple[list[dict[str, Any]], list[str]]:
    cutoff = (parse_day(date) - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    all_candidates: list[dict[str, Any]] = official_reference_candidates()
    errors: list[str] = []
    sources: list[Callable[[], list[dict[str, Any]]]] = []
    sources.extend(lambda topic=topic: github_topic_candidates(topic, cutoff, fetch) for topic in TOPICS)
    sources.extend(lambda org=org: github_official_candidates(org, cutoff, fetch) for org in OFFICIAL_ORGS)
    sources.extend((lambda: huggingface_candidates("hf_model", fetch), lambda: huggingface_candidates("hf_space", fetch)))
    for source in sources:
        try:
            all_candidates.extend(source())
        except FetchError as exc:
            errors.append(str(exc))
    return merge_candidates(all_candidates), errors


def write_run(
    output_dir: Path,
    date: str,
    candidates: list[dict[str, Any]],
    errors: list[str],
    force: bool = False,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "seen.json"
    state = load_state(state_path)
    selected = select_new(candidates, state, date, force=force)
    selected.sort(
        key=lambda item: (
            not (item.get("kind", "").startswith("official") or item.get("provider") in OFFICIAL_ORGS),
            -(item.get("signals", {}).get("stars") or item.get("signals", {}).get("likes") or 0),
            item.get("name", "").lower(),
        )
    )
    payload = {
        "schema_version": 1,
        "date": date,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "lookback_days": LOOKBACK_DAYS,
        "dedup_days": DEDUP_DAYS,
        "candidate_count": len(selected),
        "candidates": selected,
        "errors": errors,
        "status": "partial" if errors and selected else "error" if errors and not selected else "ok",
    }
    daily_path = output_dir / f"{date}.json"
    daily_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return daily_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=shanghai_today(), help="Run date in YYYY-MM-DD format")
    parser.add_argument("--output-dir", default="data/ai-tool-radar")
    parser.add_argument("--force", action="store_true", help="Ignore the 30-day deduplication window")
    args = parser.parse_args(argv)
    try:
        parse_day(args.date)
    except ValueError:
        parser.error("--date must use YYYY-MM-DD")
    candidates, errors = collect(args.date, force=args.force)
    path = write_run(Path(args.output_dir), args.date, candidates, errors, force=args.force)
    print(f"wrote {path} with {json.loads(path.read_text(encoding='utf-8'))['candidate_count']} candidates")
    if errors:
        print(f"completed with {len(errors)} source errors", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

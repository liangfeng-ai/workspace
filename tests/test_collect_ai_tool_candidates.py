import json
import tempfile
import unittest
from pathlib import Path

from scripts.collect_ai_tool_candidates import (
    collect,
    merge_candidates,
    select_new,
    write_run,
)


class CollectorTests(unittest.TestCase):
    def test_merge_combines_topics_for_same_url(self):
        items = [
            {
                "id": "one",
                "url": "https://github.com/example/tool/?tab=readme",
                "capability_tags": ["ocr"],
                "description": "short",
                "signals": {"stars": 10},
            },
            {
                "id": "two",
                "url": "https://github.com/example/tool",
                "capability_tags": ["rag"],
                "description": "a longer description",
                "signals": {"stars": 20},
            },
        ]
        merged = merge_candidates(items)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["capability_tags"], ["ocr", "rag"])
        self.assertEqual(merged[0]["description"], "a longer description")

    def test_select_new_suppresses_same_fingerprint_for_30_days(self):
        item = {
            "id": "github_repository:https://github.com/example/tool",
            "url": "https://github.com/example/tool",
            "signals": {"stars": 200, "pushed_at": "2026-07-01T00:00:00Z"},
        }
        state = {"schema_version": 1, "items": {}}
        self.assertEqual(len(select_new([item.copy()], state, "2026-07-15")), 1)
        self.assertEqual(len(select_new([item.copy()], state, "2026-07-20")), 0)
        self.assertEqual(len(select_new([item.copy()], state, "2026-08-15")), 1)

    def test_popularity_changes_do_not_bypass_deduplication(self):
        first = {
            "id": "github_repository:https://github.com/example/tool",
            "kind": "github_repository",
            "url": "https://github.com/example/tool",
            "signals": {"stars": 200, "pushed_at": "2026-07-15T00:00:00Z"},
        }
        later = {
            "id": first["id"],
            "kind": first["kind"],
            "url": first["url"],
            "signals": {"stars": 500, "pushed_at": "2026-07-16T00:00:00Z"},
        }
        state = {"schema_version": 1, "items": {}}
        self.assertEqual(len(select_new([first], state, "2026-07-15")), 1)
        self.assertEqual(len(select_new([later], state, "2026-07-16")), 0)

    def test_collector_keeps_other_sources_when_one_fails(self):
        def fake_fetch(url):
            if "search/repositories" in url:
                raise RuntimeError("unexpected test request")
            if "huggingface.co/api/models" in url:
                return [
                    {
                        "id": "demo/ocr-model",
                        "pipeline_tag": "image-to-text",
                        "likes": 12,
                        "tags": ["ocr"],
                    }
                ]
            if "huggingface.co/api/spaces" in url:
                return []
            return []

        # The public collector catches FetchError, so this test uses a wrapper
        # that raises the same typed error for the failed source.
        from scripts.collect_ai_tool_candidates import FetchError

        def typed_fake_fetch(url):
            if "search/repositories" in url:
                raise FetchError("search unavailable")
            return fake_fetch(url)

        candidates, errors = collect("2026-07-15", fetch=typed_fake_fetch)
        self.assertTrue(errors)
        self.assertTrue(any(item["name"] == "demo/ocr-model" for item in candidates))

    def test_write_run_is_utf8_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            item = {
                "id": "hf_model:https://huggingface.co/models/demo/ocr",
                "kind": "hf_model",
                "name": "demo/ocr",
                "url": "https://huggingface.co/models/demo/ocr",
                "provider": "Hugging Face",
                "description": "OCR model",
                "capability_tags": ["ocr"],
                "input_output": "image -> text",
                "signals": {"likes": 10, "updated_at": "2026-07-15"},
            }
            first = write_run(output_dir, "2026-07-15", [item], [])
            payload = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(payload["candidate_count"], 1)
            second = write_run(output_dir, "2026-07-16", [item], [])
            payload2 = json.loads(second.read_text(encoding="utf-8"))
            self.assertEqual(payload2["candidate_count"], 0)
            self.assertTrue((output_dir / "seen.json").exists())

    def test_force_refresh_handles_existing_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            item = {
                "id": "github_repository:https://github.com/example/tool",
                "kind": "github_repository",
                "name": "example/tool",
                "url": "https://github.com/example/tool",
                "provider": "GitHub",
                "description": "tool",
                "capability_tags": ["ai-tools"],
                "input_output": "README -> examples",
                "signals": {"stars": 200, "pushed_at": "2026-07-15T00:00:00Z"},
            }
            write_run(output_dir, "2026-07-15", [item], [])
            refreshed = write_run(output_dir, "2026-07-15", [item], [], force=True)
            payload = json.loads(refreshed.read_text(encoding="utf-8"))
            self.assertEqual(payload["candidate_count"], 1)


if __name__ == "__main__":
    unittest.main()

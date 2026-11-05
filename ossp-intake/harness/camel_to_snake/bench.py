"""Median time to snake_case every key in one recorded modmail listing.

The payload is the ``api/mod/conversations`` response from
``tests/integration/cassettes/TestSubredditModmail.test_conversations.json``.
``snake_case_keys`` runs ``camel_to_snake`` on each of those keys.
"""

from __future__ import annotations

import gc
import json
import statistics
import time
from pathlib import Path

from praw.util import camel_to_snake

ROOT = Path(__file__).resolve().parents[3]
CASSETTE = ROOT / "tests/integration/cassettes/TestSubredditModmail.test_conversations.json"
REPEATS = 31
# Long enough for a cold process to leave idle CPU frequency before sampling.
WARMUP = 40


def _load_keys() -> list[str]:
    recorded = json.loads(CASSETTE.read_text())
    payload = max(recorded["interactions"], key=lambda item: len(item["response"]["body"]["string"]))
    decoded = json.loads(payload["response"]["body"]["string"])
    keys: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            keys.extend(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(decoded)
    if len(keys) < 1000:
        msg = f"expected a full modmail listing, found {len(keys)} keys"
        raise RuntimeError(msg)
    return keys


def _convert(keys: list[str]) -> None:
    for key in keys:
        camel_to_snake(key)


def main() -> None:
    keys = _load_keys()
    for _ in range(WARMUP):
        _convert(keys)
    samples: list[float] = []
    gc.disable()
    try:
        for _ in range(REPEATS):
            started = time.perf_counter()
            _convert(keys)
            samples.append((time.perf_counter() - started) * 1000)
    finally:
        gc.enable()
    print(f"{statistics.median(samples):.4f}")


if __name__ == "__main__":
    main()

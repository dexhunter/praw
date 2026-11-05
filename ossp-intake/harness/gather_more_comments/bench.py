"""Median time for ``CommentForest._gather_more_comments`` on a large thread.

The shape and payloads come from the recorded comment tree in
``tests/integration/cassettes/TestCommentForest.test_replace__skip_all.json``
(submission ``3hahrw``: 476 comments and 18 ``MoreComments``). That tree is
attached four times under one forest (~2000 nodes). ``replace_more`` walks
forests of this size on a busy thread; the integration suite asserts a fully
expanded thread is larger than 1000 comments.
"""

from __future__ import annotations

import gc
import json
import os
import statistics
import time
from pathlib import Path

os.environ["praw_check_for_updates"] = "False"

from praw import Reddit
from praw.models import Comment, MoreComments, Submission
from praw.models.comment_forest import CommentForest

ROOT = Path(__file__).resolve().parents[3]
CASSETTE = ROOT / "tests/integration/cassettes/TestCommentForest.test_replace__skip_all.json"
# Four copies of this recorded thread are about 2000 nodes.
COPIES = 4
REPEATS = 31
WARMUP = 20


def _build_tree(reddit: Reddit, nodes: list[dict]) -> list[Comment | MoreComments]:
    built: list[Comment | MoreComments] = []
    for node in nodes:
        if node.get("kind") == "more":
            built.append(MoreComments(reddit, _data=dict(node["data"])))
            continue
        data = node["data"]
        replies = data.get("replies")
        comment = Comment(reddit, _data={key: value for key, value in data.items() if key != "replies"})
        children = _build_tree(reddit, replies["data"]["children"]) if isinstance(replies, dict) else []
        comment._replies = children
        built.append(comment)
    return built


def _load_forest(reddit: Reddit) -> list[Comment | MoreComments]:
    recorded = json.loads(CASSETTE.read_text())
    payload = max(recorded["interactions"], key=lambda item: len(item["response"]["body"]["string"]))
    listing = json.loads(payload["response"]["body"]["string"])
    children = listing[1]["data"]["children"]
    submission = Submission(reddit, id="3hahrw")
    submission._fetched = True
    forest: list[Comment | MoreComments] = []
    for _ in range(COPIES):
        forest.extend(_build_tree(reddit, children))
    # Production assigns the submission after fetch, which wraps each replies
    # list in a CommentForest. _gather_more_comments then walks those forests.
    for node in forest:
        if isinstance(node, Comment):
            node.submission = submission
    return forest


def main() -> None:
    reddit = Reddit(
        client_id="dummy",
        client_secret="dummy",
        user_agent="ossp-intake-bench",
        check_for_updates=False,
    )
    forest = _load_forest(reddit)

    def run() -> None:
        CommentForest._gather_more_comments(forest)

    for _ in range(WARMUP):
        run()
    samples: list[float] = []
    gc.disable()
    try:
        for _ in range(REPEATS):
            started = time.perf_counter()
            run()
            samples.append((time.perf_counter() - started) * 1000)
    finally:
        gc.enable()
    print(f"{statistics.median(samples):.4f}")


if __name__ == "__main__":
    main()

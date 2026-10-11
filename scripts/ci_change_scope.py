"""Classify the files that a pull request changes as `docs-only` or `full`.

Read changed paths from standard input, one path on each line, and print the
scope. The scope is `docs-only` only when the list is not empty and each path is
a top-level project document, a file under assets/, or a Markdown file under
docs/ outside docs/preregistrations/. Any other path gives `full`. CI runs the
whole suite for `full` and skips the tests marked `slow` for `docs-only`.
"""

from __future__ import annotations

import re
import sys


DOCS_ONLY_PATH = re.compile(r"^(README\.md|CHANGELOG\.md|CITATION\.cff|LICENSE|assets/.*|docs/.*\.md)$")


def change_scope(paths: list[str]) -> str:
    changed = [path for path in paths if path]
    if changed and all(
        DOCS_ONLY_PATH.fullmatch(path) and not path.startswith("docs/preregistrations/") for path in changed
    ):
        return "docs-only"
    return "full"


if __name__ == "__main__":
    print(change_scope(sys.stdin.read().splitlines()))

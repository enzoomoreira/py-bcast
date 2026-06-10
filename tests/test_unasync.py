"""Generated sync I/O layer freshness.

The sync tree (``_legacy/_sync/``) is generated from the async source tree
(``_legacy/_async/``) by ``scripts/gen_sync.py``. This test regenerates into a
temp dir and diffs against the committed tree, so an edit to the source (or a
hand edit to the generated tree) that lands without regeneration fails loudly.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_generated_sync_tree_is_fresh():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gen_sync.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"generated _legacy/_sync/ tree is stale:\n{result.stdout}{result.stderr}"
    )

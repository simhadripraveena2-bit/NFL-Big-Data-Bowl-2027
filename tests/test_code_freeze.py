import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_confirmatory_code_is_unchanged():
    """Fails if any file of the frozen confirmatory pipeline changes without updating the freeze manifest
    (which itself requires a logged deviation in preregistration.md §15)."""
    m = json.loads((ROOT / "research_notes/code_freeze.json").read_text())
    changed = [f for f, h in m["files"].items() if hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != h]
    assert not changed, f"frozen files changed: {changed}"

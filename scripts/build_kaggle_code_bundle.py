"""Assemble the small code dataset that the public Kaggle notebook attaches (Phase 9B). NOTHING IS UPLOADED.

Contents (no competition data, no credentials, no experiment outputs):
  src/nfl_bdb/**           the pipeline package (frozen modules unchanged)
  scripts/run_real_capacity.py, scripts/run_phase3_screening.py   (frozen feature stages imported by the notebook)
  research_notes/code_freeze.json                                  (sha256 manifest checked by the notebook)
  paper/registered_results.json                                    (aggregate registered results)
  dataset-metadata.json, kernel-metadata.json                      (templates; replace <KAGGLE_USERNAME> before use)

Output: build/kaggle_code_bundle/ (git-ignored). Upload is a manual, owner-approved step:
  kaggle datasets create -p build/kaggle_code_bundle --dir-mode zip
  kaggle kernels push -p <dir containing 11_final_submission.ipynb + kernel-metadata.json>
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "kaggle_code_bundle"
FILES = ["scripts/run_real_capacity.py", "scripts/run_phase3_screening.py", "research_notes/code_freeze.json",
         "paper/registered_results.json"]
FORBIDDEN = (".csv", ".parquet", ".npz", ".npy", ".zip", ".json.bak", "kaggle.json", ".env")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "src" / "nfl_bdb", OUT / "src" / "nfl_bdb", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for f in FILES:
        (OUT / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, OUT / f)
    (OUT / "dataset-metadata.json").write_text(json.dumps({
        "title": "NFL BDB 2027 pipeline code (Combine speed to NFL movement)",
        "id": "<KAGGLE_USERNAME>/nfl-bdb-2027-pipeline-code",
        "licenses": [{"name": "apache-2.0"}],
        "description": "Pipeline code and aggregate registered results for the public notebook. No competition data."}, indent=1))
    (OUT / "kernel-metadata.json").write_text(json.dumps({
        "id": "<KAGGLE_USERNAME>/combine-speed-to-nfl-movement",
        "title": "Combine Speed to NFL Movement: Reproducibility",
        "code_file": "11_final_submission.ipynb", "language": "python", "kernel_type": "notebook",
        "is_private": True, "enable_gpu": False, "enable_internet": False,
        "dataset_sources": ["<KAGGLE_USERNAME>/nfl-bdb-2027-pipeline-code"],
        "competition_sources": ["nfl-big-data-bowl-2027"]}, indent=1))
    bad = [p for p in OUT.rglob("*") if p.is_file() and p.name.endswith(FORBIDDEN) and p.name != "dataset-metadata.json"]
    assert not bad, f"forbidden files in bundle: {bad}"
    n = sum(1 for p in OUT.rglob("*") if p.is_file()); size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"bundle: {OUT} ({n} files, {size / 1024:.0f} KiB)")


if __name__ == "__main__":
    main()

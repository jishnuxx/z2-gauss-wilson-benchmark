#!/usr/bin/env python3
"""Create a clean reproducibility bundle for the Z2 Gauss/Wilson benchmark.

The bundle includes the public source, tests, archived evidence, and figures
needed for reproduction. Planning notes, obsolete workflows, local environments,
caches, and temporary working folders are excluded.
"""

from __future__ import annotations

import fnmatch
import hashlib
import shutil
import zipfile
from datetime import date
from pathlib import Path

import _bootstrap


ROOT = _bootstrap.ROOT
DIST = ROOT / "dist"
BUNDLE_NAME = f"z2_gauss_wilson_benchmark_bundle_{date.today():%Y%m%d}"
BUNDLE_DIR = DIST / BUNDLE_NAME
ARCHIVE = DIST / f"{BUNDLE_NAME}.zip"

TOP_LEVEL_FILES = [
    ".gitattributes",
    ".gitignore",
    "ARTIFACT_MANIFEST.md",
    "LICENSE",
    "Makefile",
    "README.md",
    "REPRODUCIBILITY.md",
    "pyproject.toml",
    "requirements.txt",
]

FULL_DIRS = [
    "circuits",
    "figures",
    "scripts",
    "src",
    "tests",
    "results/ideal",
    "results/noisy",
    "results/processed",
    "results/iqm/static_blindspot_5000",
    "results/iqm/emerald_blindspot_candidate_5000",
    "results/iqm/periodic_hardware",
    "results/iqm/emerald_periodic_candidate_5000_seed1",
    "results/iqm/periodic_matter_hardware",
    "results/iqm/emerald_periodic_matter_candidate_5000",
    "results/iqm/emerald_periodic_matter_hardware",
    "results/iqm/emerald_periodic_matter_scan_candidate_5000",
    "results/iqm/emerald_periodic_matter_scan_repeat2_5000",
    "results/iqm/sirius_periodic_matter_hardware",
    "results/iqm/sirius_periodic_matter_scan_candidate_5000",
    "results/iqm/sirius_periodic_matter_scan_repeat2_5000",
]

SELECTED_FILES = [
    "docs/blindspot_model.md",
    "docs/circuit_and_encoding_reference.md",
    "docs/hardware_device_comparison.md",
    "docs/iqm_emerald_hardware_result.md",
    "docs/iqm_readout_and_response_mitigation.md",
    "docs/model_convention.md",
    "docs/technical_appendix_blindspot_iqm.md",
    "docs/technical_appendix_periodic_iqm.md",
]

EXCLUDE_PATTERNS = [
    ".DS_Store",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".venv",
    "work",
    "tmp",
    "dist",
    "*.egg-info",
    "freeze_hardware_candidate.py",
]


def excluded(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    parts = relative.parts
    for pattern in EXCLUDE_PATTERNS:
        if any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
        if fnmatch.fnmatch(str(relative), pattern):
            return True
    return False


def copy_file(relative: str) -> None:
    src = ROOT / relative
    if not src.exists():
        raise FileNotFoundError(src)
    dst = BUNDLE_DIR / relative
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(relative: str) -> None:
    src_root = ROOT / relative
    if not src_root.exists():
        raise FileNotFoundError(src_root)
    for src in src_root.rglob("*"):
        if excluded(src) or src.is_dir():
            continue
        dst = BUNDLE_DIR / src.relative_to(ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest() -> None:
    files = sorted(path for path in BUNDLE_DIR.rglob("*") if path.is_file())
    contents = "\n".join(str(path.relative_to(BUNDLE_DIR)) for path in files) + "\n"
    (BUNDLE_DIR / "BUNDLE_CONTENTS.txt").write_text(contents, encoding="utf-8")

    hash_lines = []
    for path in sorted(BUNDLE_DIR.rglob("*")):
        if path.is_file():
            hash_lines.append(f"{sha256(path)}  {path.relative_to(BUNDLE_DIR)}")
    (BUNDLE_DIR / "BUNDLE_MANIFEST_SHA256.txt").write_text(
        "\n".join(hash_lines) + "\n", encoding="utf-8"
    )


def make_archive() -> None:
    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(BUNDLE_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=Path(BUNDLE_NAME) / path.relative_to(BUNDLE_DIR))


def main() -> None:
    DIST.mkdir(exist_ok=True)
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir()

    for relative in TOP_LEVEL_FILES:
        copy_file(relative)
    for relative in FULL_DIRS:
        copy_tree(relative)
    for relative in SELECTED_FILES:
        copy_file(relative)

    write_manifest()
    make_archive()

    file_count = sum(1 for path in BUNDLE_DIR.rglob("*") if path.is_file())
    print(f"Bundle directory: {BUNDLE_DIR}")
    print(f"Bundle archive:   {ARCHIVE}")
    print(f"Files included:   {file_count}")


if __name__ == "__main__":
    main()

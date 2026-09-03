#!/usr/bin/env python3
"""Audit coursework verification boundaries without printing matched private data."""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIED_FILES = {
    ".github/workflows/coursework-verification.yml",
    "README.md",
    "COURSEWORK_VERIFICATION_SCOPE.md",
    "TROUBLESHOOTING.md",
    "WORKLOG.md",
    "Programming_Languages/README.md",
    "Programming_Languages/interpreter.py",
    "Programming_Languages/interpreter.cpp",
    "Computer_Architecture/README.md",
    "Computer_Architecture/src/main.c",
    "Algorithm/README.md",
    "Algorithm/src/MyInteger.h",
    "Algorithm/src/hw1_common.h",
    "Algorithm/src/hw1_myheader.h",
    "coursework_tests/algorithm_harness.cpp",
    "coursework_tests/test_coursework_verification.py",
    "scripts/audit_public_surface.py",
}
TEXT_SUFFIXES = {
    ".c",
    ".cpp",
    ".h",
    ".java",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
}
PUBLIC_DELIVERABLE_SUFFIXES = {
    ".7z",
    ".bmp",
    ".ckpt",
    ".docx",
    ".gif",
    ".gz",
    ".h5",
    ".hdf5",
    ".jpeg",
    ".jpg",
    ".joblib",
    ".npy",
    ".npz",
    ".onnx",
    ".pdf",
    ".pickle",
    ".pkl",
    ".png",
    ".pt",
    ".pth",
    ".rar",
    ".safetensors",
    ".tar",
    ".tgz",
    ".tif",
    ".tiff",
    ".webp",
    ".zip",
}
ARCHIVE_SUFFIXES = PUBLIC_DELIVERABLE_SUFFIXES | {".ipynb"}
PRIVATE_NOTEBOOK_METADATA_KEYS = {
    "ExecuteTime",
    "authorship_tag",
    "base_uri",
    "colab",
    "displayName",
    "executionInfo",
    "outputId",
    "trusted",
    "user",
    "userId",
    "widgets",
}
MAX_HISTORY_BLOB_BYTES = 20 * 1024 * 1024
STUDENT_ID = re.compile(r"\b20\d{6}\b")
STUDENT_ID_IN_PATH = re.compile(r"20\d{6}")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def repository_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("unable to enumerate tracked repository files")
    return sorted(
        ROOT / relative.decode("utf-8", errors="surrogateescape")
        for relative in result.stdout.split(b"\0")
        if relative
    )


def contains_identity(text: str) -> bool:
    return bool(STUDENT_ID.search(text) or EMAIL.search(text))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return ""


def read_checked_text(path: Path) -> tuple[str, bool]:
    try:
        data = path.read_bytes()
        if b"\0" in data:
            return "", False
        return data.decode("utf-8-sig"), True
    except (OSError, UnicodeDecodeError):
        return "", False


def contains_private_notebook_metadata(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key in PRIVATE_NOTEBOOK_METADATA_KEYS
            or contains_private_notebook_metadata(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(contains_private_notebook_metadata(child) for child in value)
    return False


def inspect_notebook(path: Path) -> dict[str, int]:
    try:
        notebook = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "parse_errors": 1,
            "cells_with_outputs": 0,
            "cells_with_execution_counts": 0,
            "files_with_private_metadata": 0,
        }

    if not isinstance(notebook, dict):
        return {
            "parse_errors": 1,
            "cells_with_outputs": 0,
            "cells_with_execution_counts": 0,
            "files_with_private_metadata": 0,
        }
    cells = notebook.get("cells")
    valid_cells = isinstance(cells, list) and all(
        isinstance(cell, dict)
        and cell.get("cell_type") in {"code", "markdown", "raw"}
        and isinstance(cell.get("metadata", {}), dict)
        and isinstance(cell.get("source", []), (str, list))
        for cell in cells
    )
    if not valid_cells:
        return {
            "parse_errors": 1,
            "cells_with_outputs": 0,
            "cells_with_execution_counts": 0,
            "files_with_private_metadata": 0,
        }
    metadata = {
        "notebook": notebook.get("metadata", {}),
        "cells": [cell.get("metadata", {}) for cell in cells if isinstance(cell, dict)],
    }
    return {
        "parse_errors": 0,
        "cells_with_outputs": sum(
            bool(cell.get("outputs"))
            for cell in cells
            if isinstance(cell, dict) and cell.get("cell_type") == "code"
        ),
        "cells_with_execution_counts": sum(
            cell.get("execution_count") is not None
            for cell in cells
            if isinstance(cell, dict) and cell.get("cell_type") == "code"
        ),
        "files_with_private_metadata": int(contains_private_notebook_metadata(metadata)),
    }


def extract_archive_text(data: bytes, suffix: str) -> tuple[str, bool]:
    """Return best-effort text and whether a content-aware scanner ran."""
    suffix = suffix.casefold()
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                parts = [
                    archive.read(name).decode("utf-8", errors="ignore")
                    for name in archive.namelist()
                    if name.startswith(("word/", "docProps/")) and name.endswith(".xml")
                ]
            return "\n".join(parts), True
        except (OSError, KeyError, zipfile.BadZipFile):
            return "", False
    if suffix == ".ipynb":
        return data.decode("utf-8", errors="ignore"), True
    if suffix == ".pdf" and shutil.which("pdftotext"):
        try:
            result = subprocess.run(
                ["pdftotext", "-", "-"],
                input=data,
                capture_output=True,
                check=False,
                timeout=15,
            )
            if result.returncode == 0:
                return result.stdout.decode("utf-8", errors="ignore"), True
        except (OSError, subprocess.TimeoutExpired):
            pass
        return "", False
    # Raw printable metadata still catches ASCII e-mail/student-number markers
    # in images and model files, but is not a semantic binary-document review.
    return data.decode("utf-8", errors="ignore"), False


def audit_current_tree(files: list[Path]) -> tuple[int, dict[str, int]]:
    verified_violations = 0
    archive_identity_text_files = 0
    archive_identity_filenames = 0
    archive_artifacts = 0
    archive_content_scanned = 0
    archive_identity_content_files = 0
    archive_content_unscanned = 0
    notebooks_checked = 0
    notebook_parse_errors = 0
    notebook_output_cells = 0
    notebook_execution_count_cells = 0
    notebooks_with_private_metadata = 0

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        suffix = path.suffix.casefold()
        if suffix in PUBLIC_DELIVERABLE_SUFFIXES:
            archive_artifacts += 1
        if STUDENT_ID_IN_PATH.search(relative):
            archive_identity_filenames += 1

        if suffix not in ARCHIVE_SUFFIXES:
            text, content_aware = read_checked_text(path)
            if not content_aware:
                archive_content_unscanned += 1
                continue
            identity = contains_identity(text)
            if relative in VERIFIED_FILES:
                verified_violations += int(identity)
            elif identity:
                archive_identity_text_files += 1
            continue

        if suffix == ".ipynb":
            notebooks_checked += 1
            notebook_review = inspect_notebook(path)
            notebook_parse_errors += notebook_review["parse_errors"]
            notebook_output_cells += notebook_review["cells_with_outputs"]
            notebook_execution_count_cells += notebook_review["cells_with_execution_counts"]
            notebooks_with_private_metadata += notebook_review["files_with_private_metadata"]
            archive_content_scanned += int(not notebook_review["parse_errors"])
            archive_content_unscanned += notebook_review["parse_errors"]
            archive_identity_content_files += int(contains_identity(read_text(path)))
            continue

        if suffix in PUBLIC_DELIVERABLE_SUFFIXES:
            try:
                data = path.read_bytes()
            except OSError:
                archive_content_unscanned += 1
                continue
            text, content_aware = extract_archive_text(data, suffix)
            archive_content_scanned += int(content_aware)
            archive_content_unscanned += int(not content_aware)
            archive_identity_content_files += int(contains_identity(text))

    return verified_violations, {
        "binary_or_submission_artifacts": archive_artifacts,
        "identity_bearing_filenames": archive_identity_filenames,
        "identity_bearing_text_files": archive_identity_text_files,
        "content_aware_binary_files_scanned": archive_content_scanned,
        "identity_bearing_binary_content_files": archive_identity_content_files,
        "binary_files_without_content_aware_scanner": archive_content_unscanned,
        "notebooks_checked": notebooks_checked,
        "notebook_parse_errors": notebook_parse_errors,
        "notebook_cells_with_outputs": notebook_output_cells,
        "notebook_cells_with_execution_counts": notebook_execution_count_cells,
        "notebooks_with_private_metadata": notebooks_with_private_metadata,
    }


def git_output(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def audit_history() -> dict[str, int | bool]:
    shallow_result = git_output("rev-parse", "--is-shallow-repository")
    shallow = shallow_result.returncode != 0 or shallow_result.stdout.strip() != "false"
    commits = git_output("rev-list", "--count", "--all")
    objects = git_output("rev-list", "--objects", "--all")
    if objects.returncode != 0:
        return {
            "reviewed": False,
            "complete_history_available": False,
            "commit_count": 0,
            "blob_count": 0,
            "identity_bearing_blobs": 0,
            "oversized_blobs_not_scanned": 0,
            "binary_blobs_without_content_aware_scanner": 0,
        }

    paths_by_oid: dict[str, str] = {}
    for line in objects.stdout.splitlines():
        oid, _, path = line.partition(" ")
        if path:
            paths_by_oid.setdefault(oid, path)
    oids = sorted(paths_by_oid)
    checked = git_output(
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_text="\n".join(oids) + "\n",
    )

    blob_count = 0
    identity_blobs = 0
    oversized = 0
    binary_unscanned = 0
    for line in checked.stdout.splitlines():
        oid, object_type, raw_size = line.split(" ", 2)
        if object_type != "blob":
            continue
        blob_count += 1
        size = int(raw_size)
        if size > MAX_HISTORY_BLOB_BYTES:
            oversized += 1
            continue
        blob = subprocess.run(
            ["git", "cat-file", "blob", oid],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if blob.returncode != 0:
            continue
        suffix = Path(paths_by_oid[oid]).suffix.casefold()
        if suffix in TEXT_SUFFIXES:
            text = blob.stdout.decode("utf-8", errors="ignore")
        elif suffix in ARCHIVE_SUFFIXES:
            text, content_aware = extract_archive_text(blob.stdout, suffix)
            binary_unscanned += int(not content_aware)
        else:
            text = blob.stdout.decode("utf-8", errors="ignore")
        identity_blobs += int(contains_identity(text) or STUDENT_ID_IN_PATH.search(paths_by_oid[oid]) is not None)

    return {
        "reviewed": not shallow,
        "complete_history_available": not shallow,
        "commit_count": int(commits.stdout.strip()) if commits.returncode == 0 else 0,
        "blob_count": blob_count,
        "identity_bearing_blobs": identity_blobs,
        "oversized_blobs_not_scanned": oversized,
        "binary_blobs_without_content_aware_scanner": binary_unscanned,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit coursework verification boundaries and optional archive/history")
    parser.add_argument(
        "--full",
        action="store_true",
        help="best-effort current archive and complete local Git-history review",
    )
    args = parser.parse_args(argv)

    files = repository_files()
    verified_violations, archive_review = audit_current_tree(files)
    history_review = audit_history() if args.full else {
        "reviewed": False,
        "complete_history_available": False,
    }
    current_tree_generic_checks_pass = verified_violations == 0 and not any(
        archive_review[key]
        for key in (
            "binary_or_submission_artifacts",
            "identity_bearing_filenames",
            "identity_bearing_text_files",
            "identity_bearing_binary_content_files",
            "binary_files_without_content_aware_scanner",
            "notebook_parse_errors",
            "notebook_cells_with_outputs",
            "notebook_cells_with_execution_counts",
            "notebooks_with_private_metadata",
        )
    )
    repository_wide_safe = (
        args.full
        and current_tree_generic_checks_pass
        and history_review.get("reviewed") is True
        and history_review.get("identity_bearing_blobs") == 0
        and history_review.get("oversized_blobs_not_scanned") == 0
        and history_review.get("binary_blobs_without_content_aware_scanner") == 0
    )
    report = {
        "verified_files_checked": len(VERIFIED_FILES),
        "verified_identity_violations": verified_violations,
        "archive_only_review": archive_review,
        "current_tree_generic_checks_pass": current_tree_generic_checks_pass,
        "history_review": history_review,
        "safe_to_claim_repository_wide_privacy": repository_wide_safe,
        "limitations": [
            "Generic patterns do not prove that personal names, faces, instructor content, or third-party rights are absent.",
            "Notebook source and Markdown remain reviewable coursework; outputs and execution metadata are intentionally absent.",
            "Image/model raw metadata checks are not equivalent to semantic visual or model-content review.",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if current_tree_generic_checks_pass else 1


if __name__ == "__main__":
    sys.exit(main())

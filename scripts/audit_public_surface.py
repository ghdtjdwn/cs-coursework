#!/usr/bin/env python3
"""Audit portfolio publication boundaries without printing matched private data."""

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
CURATED_FILES = {
    ".github/workflows/portfolio.yml",
    "README.md",
    "PUBLICATION_SCOPE.md",
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
    "portfolio_tests/algorithm_harness.cpp",
    "portfolio_tests/test_representative_projects.py",
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
ARCHIVE_SUFFIXES = {".docx", ".ipynb", ".pdf", ".png", ".pth"}
MAX_HISTORY_BLOB_BYTES = 20 * 1024 * 1024
STUDENT_ID = re.compile(r"\b20\d{6}\b")
STUDENT_ID_IN_PATH = re.compile(r"20\d{6}")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def repository_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
    )


def contains_identity(text: str) -> bool:
    return bool(STUDENT_ID.search(text) or EMAIL.search(text))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return ""


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
    curated_violations = 0
    archive_identity_text_files = 0
    archive_identity_filenames = 0
    archive_artifacts = 0
    archive_content_scanned = 0
    archive_identity_content_files = 0
    archive_content_unscanned = 0

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        suffix = path.suffix.casefold()
        if suffix in ARCHIVE_SUFFIXES:
            archive_artifacts += 1
        if STUDENT_ID_IN_PATH.search(relative):
            archive_identity_filenames += 1

        if suffix in TEXT_SUFFIXES:
            identity = contains_identity(read_text(path))
            if relative in CURATED_FILES:
                curated_violations += int(identity)
            elif identity:
                archive_identity_text_files += 1
            continue

        if suffix in ARCHIVE_SUFFIXES:
            try:
                data = path.read_bytes()
            except OSError:
                archive_content_unscanned += 1
                continue
            text, content_aware = extract_archive_text(data, suffix)
            archive_content_scanned += int(content_aware)
            archive_content_unscanned += int(not content_aware)
            archive_identity_content_files += int(contains_identity(text))

    return curated_violations, {
        "binary_or_submission_artifacts": archive_artifacts,
        "identity_bearing_filenames": archive_identity_filenames,
        "identity_bearing_text_files": archive_identity_text_files,
        "content_aware_binary_files_scanned": archive_content_scanned,
        "identity_bearing_binary_content_files": archive_identity_content_files,
        "binary_files_without_content_aware_scanner": archive_content_unscanned,
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
    parser = argparse.ArgumentParser(description="Audit the curated portfolio and optional archive/history")
    parser.add_argument(
        "--full",
        action="store_true",
        help="best-effort current archive and complete local Git-history review",
    )
    args = parser.parse_args(argv)

    files = repository_files()
    curated_violations, archive_review = audit_current_tree(files)
    history_review = audit_history() if args.full else {
        "reviewed": False,
        "complete_history_available": False,
    }
    repository_wide_safe = (
        args.full
        and curated_violations == 0
        and not any(
            archive_review[key]
            for key in (
                "identity_bearing_filenames",
                "identity_bearing_text_files",
                "identity_bearing_binary_content_files",
                "binary_files_without_content_aware_scanner",
            )
        )
        and history_review.get("reviewed") is True
        and history_review.get("identity_bearing_blobs") == 0
        and history_review.get("oversized_blobs_not_scanned") == 0
        and history_review.get("binary_blobs_without_content_aware_scanner") == 0
    )
    report = {
        "curated_files_checked": len(CURATED_FILES),
        "curated_identity_violations": curated_violations,
        "archive_only_review": archive_review,
        "history_review": history_review,
        "safe_to_claim_repository_wide_privacy": repository_wide_safe,
        "limitations": [
            "Generic patterns do not prove that personal names, faces, instructor content, or third-party rights are absent.",
            "Image/model raw metadata checks are not equivalent to semantic visual or model-content review.",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if curated_violations else 0


if __name__ == "__main__":
    sys.exit(main())

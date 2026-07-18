# Publication scope

This repository is a historical coursework archive, not a uniformly curated
public portfolio. The representative, reproducible surface is limited to:

- `Programming_Languages/interpreter.py`, `interpreter.cpp`, and its README
- `Computer_Architecture/src/main.c` and its README
- `Algorithm/src/MyInteger.h`, `hw1_common.h`, `hw1_myheader.h`, and its README
- the build and behavior checks under `portfolio_tests/`

The root README, this publication boundary, the work log, troubleshooting
record, CI workflow, and privacy-audit script are also part of the curated
supporting surface. Together these are the 17 files enforced by the audit.

PDF/DOCX reports, assignment specifications, screenshots, notebooks, trained
model files, and the remaining course directories are archive-only material.
They may contain submission identifiers, personal metadata, instructor-owned
prompts, network details, or third-party content and should not be linked as
portfolio evidence until reviewed individually.

`scripts/audit_public_surface.py` gates generic student-number and email
patterns on the curated files and reports aggregate findings without printing
matched values or paths. With `--full`, it also performs best-effort inspection
of the current archive and all locally fetched Git refs. DOCX, notebook, and PDF
contents receive format-aware text extraction when the required local tool is
available. Image and model files receive only raw metadata/string inspection.

The 2026-07-18 full run produced the following evidence:

- 17 curated files checked; 0 generic identity-marker matches
- 92 archive-only binary/submission artifacts; 76 content-aware scans and 16
  files without a content-aware scanner
- 5 identity-bearing filenames, 5 non-curated text files, and 66 binary contents
  with generic identity-marker matches
- 14 commits and 225 blobs across all currently fetched refs; 74 blobs with a
  generic identity marker, 13 binary blobs without a content-aware scanner, and
  0 oversized blobs skipped
- 0 secret findings from a redacted Gitleaks scan of Git history

These results do not certify the whole repository as privacy-clean. They show
that only the curated surface is suitable as evidence today. Before broader
publication, each archive item still needs manual review for personal names,
faces, instructor-owned prompts, network details, and third-party rights. A
clean publication repository containing only approved files is safer than
rewriting this archive. No file removal or Git-history rewrite was performed.

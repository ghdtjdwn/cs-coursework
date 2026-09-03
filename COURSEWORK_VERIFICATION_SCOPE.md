# Coursework verification scope

This repository is a historical coursework archive. Automated build, behavior,
and generic identity-marker verification covers:

- `Programming_Languages/interpreter.py`, `interpreter.cpp`, and its README
- `Computer_Architecture/src/main.c` and its README
- `Algorithm/src/MyInteger.h`, `hw1_common.h`, `hw1_myheader.h`, and its README
- the build and behavior checks under `coursework_tests/`

The root README, this verification boundary, the work log, troubleshooting
record, CI workflow, and privacy-audit script are included in the same checked
file set. These 17 files define the reproducible build-and-behavior boundary;
the current-tree privacy gate additionally enumerates every tracked file.

The current public tree excludes PDF/DOCX reports, assignment specifications,
screenshots, and trained model files. Jupyter notebooks remain as source files,
but stored outputs, execution counts, Colab execution metadata, and account
metadata are removed. The audit rejects reintroduced deliverables, generic
student-number or e-mail markers, malformed notebooks, stored notebook outputs,
and private execution metadata anywhere in the current tree.

`scripts/audit_public_surface.py` reports aggregate findings without printing
matched values or paths. Its default mode gates the complete current tree as
described above. With `--full`, it also performs best-effort inspection of all
locally fetched Git refs. Historical DOCX, notebook, and PDF contents receive
format-aware text extraction when the required local tool is available. Historical
images and model files receive only raw metadata/string inspection.

The 2026-09-03 current-tree cleanup produces the following default audit result:

- 0 unreviewed report/specification/screenshot/model artifacts
- 30 parseable notebooks; 0 stored outputs, execution counts, or private metadata
- 0 generic identity markers in filenames, text, or notebook content
- current-tree generic checks pass

The full-history audit still refuses a repository-wide privacy claim because
older commits retain removed identifiers and binary artifacts.

At merge commit `07087bf7b3416c47b4b7816f9589591f6959b522`, before the terminology-only
path rename, a clean full-depth checkout verified the same 17-file boundary under its former
names and produced the following evidence on 2026-07-18:

- 17 verified files checked; 0 generic identity-marker matches
- 92 archive-only binary/submission artifacts; 76 content-aware scans and 16
  files without a content-aware scanner
- 5 identity-bearing filenames, 5 text files outside the verified set, and 66
  binary contents with generic identity-marker matches
- 7 commits and 219 unique blobs across the pinned `main` history; 74 blobs with a
  generic identity marker, 13 binary blobs without a content-aware scanner, and
  0 oversized blobs skipped
- 0 secret findings from the post-merge redacted Gitleaks scan of Git history

The script scans every locally present ref with `git rev-list --all`, so commit and blob counts
can increase when another branch or stash is present. The pinned clean-checkout result above is the
comparison baseline; the privacy conclusion does not depend on those counts remaining constant.

Those pinned results describe the repository before the 2026-09-03 current-tree
cleanup. The removed artifacts and identifiers remain reachable from older
commits because Git history was not rewritten. Current-tree checks also cannot
prove that personal names, instructor-owned prompts, network details, or
third-party rights are absent from source prose. A separate clean publication
repository remains safer than treating this historical archive as privacy-clean.

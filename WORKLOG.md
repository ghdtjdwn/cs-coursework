# Work log

## 2026-09-03 — Coursework verification terminology

- Objective: make the documentation and automation use consistent terms for automated guarantees and manual-review boundaries.
- Changes: renamed the workflow, test directory, test module, scope document, and audit fields around coursework verification; aligned README, troubleshooting, and historical work-log wording with the same terminology. The required `build-and-test` job name and all build-and-behavior assertions remain unchanged.
- Validation: `python3 -m unittest discover -s coursework_tests -v`, `python3 scripts/audit_public_surface.py --full`, and `git diff --check` passed against the renamed paths. The six behavioral and privacy tests still cover both interpreters, the RISC-V implementation, four sorting implementations, the verified file set, and locally available history.
- Delivery: prepared as a documentation and verification-tooling update. The repository has no runtime deployment surface.

## 2026-09-03 — Default-branch and dependency security controls

- Objective: prevent unreviewed or unverified changes from reaching the coursework `main` branch and surface known dependency vulnerabilities promptly.
- Changes: activated a GitHub `main` ruleset that blocks branch deletion and force pushes, requires pull requests, and requires the `build-and-test` and `gitleaks` checks. Enabled Dependabot vulnerability alerts and automated security updates.
- Validation: the GitHub rules API reports the four active rule types and both required checks for `main`. The enabled Dependabot alerts API reports zero open alerts.
- Delivery: repository settings are active. This documentation change is delivered through a separate pull request; the repository has no runtime deployment surface.

## 2026-07-29 — Coursework README information hierarchy

- Objective: help readers understand the coursework scope, reproducible evidence, and verification boundary before browsing individual subject folders.
- Changes: moved the CI badge, six-test reproduction command, and privacy boundary to the top; simplified decorative headings and links; and made the twelve-subject table more compact without changing historical coursework or reported outcomes.
- Validation: the six coursework build-and-behavior tests passed. `python3 scripts/audit_public_surface.py --full` reviewed the complete available history, found zero verified-file identity violations, and continued to report that repository-wide privacy cannot be claimed. `git diff --check` passed.
- Delivery: [pull request #3](https://github.com/ghdtjdwn/cs-coursework/pull/3) passed the `build-and-test` and Gitleaks jobs, and its exact head commit was fast-forwarded into `main`. This repository has no runtime deployment surface.

## 2026-07-18 — Reproducible builds and verification boundary

- Objective: make the automatically checked coursework independently reproducible and define
  the limits of the build, behavior, and privacy verification.
- Changes: added build-and-behavior tests for the Python/C++ interpreters, the RISC-V
  disassembler/simulator, and all four instrumented sorting implementations; corrected the
  repeat-until termination condition in both interpreter implementations; replaced an MSVC-only
  `std::exception(message)` construction with portable `std::invalid_argument`; added a privacy audit
  that reports aggregate current-tree and fetched-history findings without logging matched values or
  paths; configured CI to fetch full history, pin third-party actions to immutable commits, and run
  a redacted Gitleaks gate; documented the verified-file boundary and remaining manual review risk.
- Validation: the six coursework tests passed. The
  suite compiles sources in a temporary directory, compares both interpreter implementations,
  exercises valid and malformed RISC-V input, checks four copy-free sorts, and runs the verified-file
  privacy gates without modifying coursework outputs in place. At merge commit `07087bf`, a clean,
  full-depth checkout of `main` inspected 7 commits and 219 unique blobs and correctly refused a
  repository-wide privacy claim; the redacted Gitleaks gate reported zero secret findings.
- Delivery: [pull request #1](https://github.com/ghdtjdwn/cs-coursework/pull/1) was merged into
  `main` as `07087bf7b3416c47b4b7816f9589591f6959b522`. Those files used their original names at
  that commit; the 2026-09-03 entry records validation after the terminology-only path rename. The
  [post-merge workflow](https://github.com/ghdtjdwn/cs-coursework/actions/runs/29646213479)
  passed both `build-and-test` and `gitleaks`. No report/spec file was removed and history was not
  rewritten. The repository has no runtime deployment surface, so merge plus green CI completed
  delivery. See `COURSEWORK_VERIFICATION_SCOPE.md` for aggregate findings and `TROUBLESHOOTING.md` for the
  shallow-clone failure and fix.

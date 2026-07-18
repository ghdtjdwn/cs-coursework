# Work log

## 2026-07-18 — Representative builds and publication boundary

- Objective: make a small, explainable set of coursework independently reproducible and define
  what is and is not suitable as public portfolio evidence.
- Changes: added build-and-behavior tests for the Python/C++ interpreters, the RISC-V
  disassembler/simulator, and all four instrumented sorting implementations; corrected the
  repeat-until termination condition in both interpreter implementations; replaced an MSVC-only
  `std::exception(message)` construction with portable `std::invalid_argument`; added a privacy audit
  that reports aggregate current-tree and fetched-history findings without logging matched values or
  paths; configured CI to fetch full history, pin third-party actions to immutable commits, and run
  a redacted Gitleaks gate; documented the curated publication boundary and remaining manual review risk.
- Validation: `python3 -m unittest discover -s portfolio_tests -v` passed all six tests. The
  suite compiles sources in a temporary directory, compares both interpreter implementations,
  exercises valid and malformed RISC-V input, checks four copy-free sorts, and runs the curated
  privacy gates without modifying coursework outputs in place. At merge commit `07087bf`, a clean,
  full-depth checkout of `main` inspected 7 commits and 219 unique blobs and correctly refused a
  repository-wide privacy claim; the redacted Gitleaks gate reported zero secret findings.
- Delivery: [pull request #1](https://github.com/ghdtjdwn/cs-coursework/pull/1) was merged into
  `main` as `07087bf7b3416c47b4b7816f9589591f6959b522`. The
  [post-merge workflow](https://github.com/ghdtjdwn/cs-coursework/actions/runs/29646213479)
  passed both `build-and-test` and `gitleaks`. No report/spec file was removed and history was not
  rewritten. The repository has no runtime deployment surface, so merge plus green CI completed
  delivery. See `PUBLICATION_SCOPE.md` for aggregate findings and `TROUBLESHOOTING.md` for the
  shallow-clone failure and fix.

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
  privacy gates without modifying coursework outputs in place. The latest full audit inspected 14 commits
  and 225 blobs across fetched refs and correctly refused a repository-wide privacy claim; a redacted
  Gitleaks history scan reported zero secret findings.
- Delivery: prepared on a dedicated feature branch without report/spec removal or history rewrite.
  See `PUBLICATION_SCOPE.md` for aggregate findings and
  `TROUBLESHOOTING.md` for the shallow-clone failure and fix.

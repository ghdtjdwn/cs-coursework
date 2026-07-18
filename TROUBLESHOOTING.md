# Troubleshooting

## 2026-07-18 — Full-history privacy test failed in a shallow clone

### Context and impact

The new full privacy regression test initially failed even though the curated
surface passed. The audit reported that history had not been reviewed, so a
repository-wide or history-reviewed claim would have been unsupported.

### Expected and actual behavior

- Expected: `history_review.reviewed` is true and the test suite can verify all
  locally available history.
- Actual: the clone contained one shallow commit and the audit correctly returned
  `reviewed: false`.

### Evidence and root cause

`git rev-parse --is-shallow-repository` returned `true`. The repository had been
cloned with truncated history, so the audit could inspect the current snapshot
but not the complete ancestry available from the configured remote.

### Resolution

The configured remote history and tags were fetched with `git fetch --unshallow
--tags origin`. The GitHub Actions checkout now uses `fetch-depth: 0`, preventing
the same false assurance or test failure in CI.

### Validation and remaining risk

After the fetch, all six representative tests passed. The latest full audit reported 14
commits and 225 blobs across the currently fetched refs, and a redacted Gitleaks
history scan reported zero secret findings. Generic identity markers and binary
formats without semantic scanners remain in the archive, so publication is still
limited to the curated surface described in `PUBLICATION_SCOPE.md`.

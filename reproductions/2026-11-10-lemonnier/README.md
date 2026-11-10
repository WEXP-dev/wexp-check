# External run by Laurent Lemonnier, 2026-11-10

Laurent Lemonnier ran the unit tests and the corpus comparison of this repository in GitHub Actions in
his own repository, `Laurent-Lemonnier/dps-scitt-decision-layer`
(workflow `.github/workflows/wexp-reproduce.yml`, run
[42801386609](https://github.com/Laurent-Lemonnier/dps-scitt-decision-layer/actions/runs/42801386609),
attempt 1, head `f661d39f7d9191f536ea09b7f7c4bbcc70af6128`), and agreed to the result being recorded under
his name. The commands of the tests and of the comparison from the pinned instructions were run in
GitHub Actions; details of environment preparation are reflected in the saved workflow file.

| Pin | Commit |
| --- | --- |
| `WEXP-dev/wexp-check` | `a2fd1ffd68b234592979a8aa8965bd580ede4d76` |
| `WEXP-dev/wexp-ref` | `56289024c9ee748111f1f1d4f42728ffe04d8d69` |
| `WEXP-dev/wexp-vectors` | `edd67056873502a2c3cecf5dd2b8db71271c2f57` |

Python 3.12.16 on a GitHub-hosted `ubuntu-24.04` runner.

Result:

```
Ran 37 tests ... OK
WEXP-CORE-02-VECTORS-001 wexp_check==expected 89/89; wexp_check==wexp_ref 89/89
WEXP-CORE-02-VECTORS-002 wexp_check==expected 35/35; wexp_check==wexp_ref 35/35
comparison SHA-256 294f4cdc047994b838ede57d655beab8ec8ef3c05342903cc62d8884e1a0c9ab
```

The per-case rows of that comparison are identical to [`comparison.json`](../../comparison.json) in this
repository. The engines were imported from the two pinned checkouts (`imported from` lines in the log).
An earlier run, 42801235872, produced the same corpus result and a byte-identical comparison; it failed
only in its separate SCITT package job.

## Files

- `job-129779506135.log`, `job-129778987815.log`: raw logs of the corpus job of each run, kept byte for byte
  as served by the GitHub API.
- `run-42801386609.json`, `run-42801235872.json`: run metadata; `workflow-<head>.yml`: the workflow at each head.
- `comparison.extracted-from-log.json`: the comparison output reconstructed from the log by
  `extract_comparison_from_log.py`, which removes the runner's timestamp prefix and checks the digest printed
  by `sha256sum` in the same log. The run published no artifacts; this file is extracted from the log, not
  downloaded.
- `RUN-METADATA.json`: pins, results, and the source, retrieval time and SHA-256 of every file.

## Limitations

- Same code: this is a run of this repository's published code and commands, not an independent
  implementation.
- Not blind: the expected results are public in `WEXP-dev/wexp-vectors`.
- Environment: prepared by the workflow (`actions/setup-python`, no virtual environment), not literally by
  the steps in `REPRODUCE.md`.

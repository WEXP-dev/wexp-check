# Replay by an outside project, 19 November 2026

Xinghua Zhao, maintainer of [`zhaoxinghua09-cell/uibc-core`](https://github.com/zhaoxinghua09-cell/uibc-core), ran the unit tests and the corpus comparison on 19 November 2026, following `REPRODUCE.md`.

**What this is, and what it is not.** uibc-core is a separate verifier project in the SCITT space. It is not an implementation of WEXP Core-02, it does not consume Core-02 outputs, and this record makes no claim about which project is better. This is a replay of the published procedure on the published code, on a machine that had never run it before. It does not turn `wexp-check` and `wexp-ref` into two independent implementations: both were written by the same operator, and replaying them elsewhere does not change that.

## Pins

| Repository | Commit |
| --- | --- |
| `WEXP-dev/wexp-check` | `cfe458b5f90c0a95ad1723b7a0dbba1b8d834fae` |
| `WEXP-dev/wexp-ref` | `56289024c9ee748111f1f1d4f42728ffe04d8d69` |
| `WEXP-dev/wexp-vectors` | `edd67056873502a2c3cecf5dd2b8db71271c2f57` |

Machine: cloud Linux host, Python 3.12.11, no virtualenv, nothing installed beyond the standard library.

## Results

| Step | Result |
| --- | --- |
| `python3 -B -m unittest discover -s tests` | `Ran 37 tests`, `OK` |
| `WEXP-CORE-02-VECTORS-001` | `wexp_check==expected 89/89; wexp_check==wexp_ref 89/89` |
| `WEXP-CORE-02-VECTORS-002` | `wexp_check==expected 35/35; wexp_check==wexp_ref 35/35` |
| driver exit status | `0`, with `--baseline comparison.json` |
| row-level comparison | every row of both sets identical to `comparison.json` |

`comparison.json` in this directory is the unedited output of the run. It differs from this repository's copy only in the `engines` block and the Python patch level (`3.12.11` here, `3.12.13` there).

## What was not done

- No GitHub Actions run, so no run URL can be cited; the checkout was local.
- The optional SCITT package registration in `wexp-interop` was not repeated.
- No attempt was made to break or mutate the comparison; that negative control is documented as run 4 in `RUN-RECORD.json` and was not re-run here.

## Files

```
README.md           this file
RUN-METADATA.json   pins, commands, digests, and the limits above in machine-readable form
comparison.json     output of the corpus comparison, byte for byte
```

Correction is welcome: if any value here disagrees with a rerun on another machine, that disagreement is the useful part, and the maintainer would rather be corrected than quoted.

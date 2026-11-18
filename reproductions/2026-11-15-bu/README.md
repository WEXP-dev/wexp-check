# External run by Songbo Bu, 2026-11-15

Songbo Bu ran the unit tests and the corpus comparison of this repository on his own machine and
reported the result by email on 15 November 2026, with the machine-readable comparison output
attached. On 17 November 2026 he repeated the run at the same commits and reported an identical
comparison. In his email of 17 November 2026 he agreed to be credited as Songbo Bu and to the
inclusion of the output file.

| Pin | Commit |
| --- | --- |
| `WEXP-dev/wexp-check` | `63bde685c54fd6329f1217708d1c211b80c3712e` |
| `WEXP-dev/wexp-ref` | `56289024c9ee748111f1f1d4f42728ffe04d8d69` |
| `WEXP-dev/wexp-vectors` | `edd67056873502a2c3cecf5dd2b8db71271c2f57` |

Environment, as reported: macOS 27.2.1 (26B131), arm64, Python 3.12.1. The macOS version was
measured on 17 November; the report of 15 November names macOS and Python 3.12.1.

Commands, as reported (the three repositories checked out side by side at the pins above):

```sh
cd wexp-check
PYTHONPATH=. python3 -B -m unittest discover -s tests
python3 -B scripts/compare_corpora.py --baseline comparison.json . ../wexp-ref comparison.external.json ../wexp-vectors/vectors/WEXP-CORE-02-VECTORS-001/corpus.json ../wexp-vectors/vectors/WEXP-CORE-02-VECTORS-002/corpus.json
```

Result, as reported:

```
37 unit tests passed
WEXP-CORE-02-VECTORS-001: both appraisers equal the frozen expectations, 89/89
WEXP-CORE-02-VECTORS-002: both appraisers equal the frozen expectations, 35/35
no differences from the baseline
```

The output file is kept byte for byte as received. Compared with [`comparison.json`](../../comparison.json)
at `63bde68`, its case identifiers, per-case results, counts and corpus digests are identical. It
differs in the `python` value (`3.12.1`) and in the `engines` member, which the comparison driver
adds (see `REPRODUCE.md`).

## Files

- `WEXP_Core02_Replay_20261115.json`: the comparison output attached to the email of 15 November
  2026, unmodified.
- `RUN-METADATA.json`: pins, reported environment and commands, results, and the source and SHA-256
  of the output file.

## Limitations

- Same code: a run of this repository's published code and commands by another operator on another
  machine, not an independent implementation of the appraisal procedure.
- No mapping: the corpora are already Core-02 inputs; no data from a real system was examined.
- Not blind: the expected results are public in `WEXP-dev/wexp-vectors`.
- Reported, not logged: unlike the 2026-11-10 entry, this run has no hosted log. The evidence is the
  output file and the operator's statements; the environment and commands are as reported.
- Layout: the reported commands use side-by-side checkouts and no virtual environment, rather than
  the `/tmp` paths and the virtual environment of `REPRODUCE.md`.
- The 37 unit tests test the runner; they are counted separately from the 124 corpus cases.

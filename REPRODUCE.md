# Reproduce the comparison record

Requirements: Python 3.12 or newer, `git`, network access to GitHub. Nothing is installed; both
appraisers are standard-library Python and run from their checkouts.

```sh
python3.12 -m venv venv && . venv/bin/activate
git clone https://github.com/WEXP-dev/wexp-ref.git /tmp/wexp-ref && git -C /tmp/wexp-ref checkout 56289024c9ee748111f1f1d4f42728ffe04d8d69
git clone https://github.com/WEXP-dev/wexp-vectors.git /tmp/wexp-vectors && git -C /tmp/wexp-vectors checkout edd67056873502a2c3cecf5dd2b8db71271c2f57
PYTHONPATH=. python3 -B -m unittest discover -s tests
python3 -B scripts/compare_corpora.py --baseline comparison.json . /tmp/wexp-ref /tmp/comparison.json \
    /tmp/wexp-vectors/vectors/WEXP-CORE-02-VECTORS-001/corpus.json \
    /tmp/wexp-vectors/vectors/WEXP-CORE-02-VECTORS-002/corpus.json
```

Expected output of the last command (the counts recorded in `RUN-RECORD.json`, run 3; the two
`imported from` lines, printed once per corpus, name the files the engines were actually loaded from
and must point into the two checkouts given on the command line):

```
wexp_check imported from <this checkout>/wexp_check/__init__.py
wexp_ref imported from /tmp/wexp-ref/src/wexp_ref/core02/appraiser.py
WEXP-CORE-02-VECTORS-001 wexp_check==expected 89/89; wexp_check==wexp_ref 89/89
wexp_check imported from <this checkout>/wexp_check/__init__.py
wexp_ref imported from /tmp/wexp-ref/src/wexp_ref/core02/appraiser.py
WEXP-CORE-02-VECTORS-002 wexp_check==expected 35/35; wexp_check==wexp_ref 35/35
```

Each engine runs in a child interpreter started with `-I`, working directory and `sys.path` set to its
own checkout only; the driver stops if an engine was imported from anywhere else (run 5 in
`RUN-RECORD.json` is the control). The output file records the two import paths, relative to the
checkouts, under `engines`.

The corpora: `WEXP-CORE-02-VECTORS-001` is on `wexp-vectors` main (package revision 2, lock
`d6827a5e`, `corpus.json` SHA-256 `d5d2c9d5…`); `WEXP-CORE-02-VECTORS-002` (`corpus.json` SHA-256
`9e301333…`) is the section 7 boundary matrix set, on `wexp-vectors` main since `34b0b351`.
Commit `edd67056` holds both. `comparison.json` in this repository is the output of the same
comparison with the two local directory paths removed; with `--baseline comparison.json` the driver
checks that each set has exactly its case identifiers and per-case results.

The command exits with status 0 only if every case agrees. It exits non-zero, with a `FAIL` line
naming the set and the case, if an expectation differs, a case is missing or added, an engine raises
or mutates its input, or a `corpus.json` differs from the `manifest.json` beside it. The negative
control of this behaviour is run 4 in `RUN-RECORD.json`.

## Replay it in your own repository

**The short way, with no file to write:** fork this repository, open the Actions tab of your fork,
allow workflows to run there, choose "Replay the corpus comparison" and press "Run workflow". The run uses the three
pinned revisions and needs no secret.

To keep the replay in a repository of your own instead, one small file is enough,
`.github/workflows/wexp-replay.yml`:

```yaml
name: Replay the wexp-check corpus comparison
on: workflow_dispatch
permissions:
  contents: read
jobs:
  replay:
    uses: WEXP-dev/wexp-check/.github/workflows/replay.yml@<commit of this repository>
```

Pin the `uses:` line to a full commit id of this repository, so that what runs cannot change under
you. The workflow needs no secret. It checks out `wexp-check`, `wexp-ref` and `wexp-vectors` at the
revisions above (each can be overridden with `with:`), runs the unit tests and the comparison, prints
the two result lines in the run summary and keeps `comparison.json` as an artifact of your run.

If you run it, a [replay note](https://github.com/WEXP-dev/wexp-check/issues/new?template=replay-note.yml)
is welcome whatever the outcome; a replay that differs from the record is the more useful one. The note
asks whether the replay may be recorded under `reproductions/` and whether to name you.

A replay by another operator repeats the recorded comparison with the published code on the published
inputs. It is not an independent implementation, and it does not make the two appraisers independent
of each other.

To appraise one input by hand:

```sh
python3 -B -m wexp_check --input <normalized-input.json> --profiles <profiles.json>
```

An external run of these commands by Laurent Lemonnier (2026-11-10) is recorded in [`reproductions/2026-11-10-lemonnier/`](reproductions/2026-11-10-lemonnier/README.md).

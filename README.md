# wexp_check

`wexp_check` is an implementation of the normalized-input appraisal procedure of the published
Internet-Draft `draft-sergeev-wexp-core-02` (WEXP Core, semantics version `wexp-core-2`),
written from the published text; the author did not read wexp-ref or any WEXP corpus expectations.
Besides the text, the author received only a short task brief, the representation note now kept as
`docs/REPRESENTATION.md`, the section 13 fixture profile catalog and one input (C01) without its
expected result; `FILES-READ.txt` lists every file opened.
The specification, not this code or its output, is authoritative: where the two disagree, the
text wins and the code is wrong. WEXP appraises how far normalized findings support an exact
execution-related claim (observation, intent, invocation or execution, with the PROV and IV
qualifiers) and returns accept, downgrade or reject together with the supported claim set,
reasons, evaluation gaps and inherited limitations. It does not establish truth, safety, authority,
authorization validity, policy compliance or alignment.

Maturity: pre-alpha. Requires Python 3.12 or newer and has no runtime dependencies (standard
library only). The only semantics version implemented is `wexp-core-2`; any other text value is
rejected with `E_UNSUPPORTED_SEMANTICS_VERSION` as the text requires.

## Quick start

    python -m wexp_check --input <normalized-input.json> --profiles <profiles.json>

The command reads one normalized input in the local JSON representation and the applied profile
catalog, and prints the complete twenty-component Appraisal of section 8.5 as a single JSON object
on stdout with sorted keys and ASCII escaping.

Exit codes:

- `0`: a Core appraisal was produced, including every Core rejection (`verdict` = `reject` with
  the fixed projection of section 8.4; logically malformed input is a Core result, not an error).
- `2`: harness decoding failure before any logical input existed (unreadable file, malformed
  JSON, duplicate JSON object members, `NaN`/`Infinity` or other non-finite numbers, or a profile
  catalog that is not a map of profile identities to `{tokens, relation_tokens, scope_names}`).
  A JSON object `{"harness_error": ..., "core_appraisal_produced": false}` is written to stderr
  and nothing is written to stdout.

Library use: `from wexp_check import appraise`; `appraise(normalized_input, profiles)` returns the
result as a `dict` and does not mutate either argument.

## Representation

The local JSON harness representation is the one described in [`docs/REPRESENTATION.md`](docs/REPRESENTATION.md),
the note handed to the author together with the text: opaque atoms
are JSON strings; profile-scoped atoms and extension keys are two-element arrays
`[profile_identifier, local_name]`; sets and the evaluation-scope map are arrays with logical
set/map semantics; the logical value *unavailable* is `null`; a claim is `{"base", "qualifiers"}`;
`affected_claims` may be the text atom `"all-admissible-claims"`. Set- and map-valued arrays in the
output are emitted sorted by the compact JSON encoding of their members so that equal logical
results serialize identically; comparison by a reader should remain logical, not positional.

Checked behaviour is traceable to the text by section-number comments at each decision point in
the code. Points where the text admitted two readings are listed in `DECISIONS.md` with the reading
chosen.

## Scope and limits

Implemented: sections 6 to 8 and 12 of the published Core-02 text, namely the ordered ingress
checks of section 6.2 with their precedence, the structural pass over every member and closed
enumeration, every cross-field invariant named in sections 6 and 12 (aggregate cardinality and
keys, exact target and context scope, the counter-evidence sentinel, qualifier aggregate
combinations, conditional `ceiling_base` and grounding pairing, evaluation-scope consistency,
extension-key binding, current-scope markers, profile and registry identity and token category),
the supported claim set with qualifiers and the Boundary Ceiling, the verdict, maximal claims and
support relations, the complete claim-required diagnostic matrix of section 8.6, per-entry
counter-evidence handling, the limitation union of section 8.1, profile gap projection, and the
fixed rejection projection of section 8.4.

Not implemented: carrier parsing, carrier authentication, evidence discovery, mapping-profile and
composition-profile execution, and the Coverage companion document. Composed inputs (the C11 and
C12 fixtures of section 13) are appraised only because they arrive as ordinary normalized input.
The local JSON harness representation is not a standardized WEXP carrier and this package defines
no wire format.

## Tests

    PYTHONPATH=. python3.12 -m unittest discover -s tests

The tests include the supplied C01 input end to end against the result derived by hand from the
section 13 table, the other table rows that could be derived from the table text and the stated
common fixture context, targeted tests for each ordered ingress check, and tests for the
diagnostic matrix rows.

## License

Apache License 2.0; see `LICENSE`.

## Comparison record

The code was frozen first ([`FREEZE.md`](FREEZE.md): SHA-256 of every file, committed before
any corpus run) and then run, unchanged, against two Core-02 corpora of
`WEXP-dev/wexp-vectors`: the published `WEXP-CORE-02-VECTORS-001` (89 cases, package revision 2,
lock commit `d6827a5e`) and `WEXP-CORE-02-VECTORS-002` (35 cases, section 7 boundary matrix) at
branch commit `e676fcbb` (on that repository's main branch since 2026-11-08, merge commit `34b0b351`).
Every result was compared component by component, over all twenty members and with set
semantics for the collections the harness defines as sets, both with the frozen expected
results and with the output of `wexp_ref.core02` at `WEXP-dev/wexp-ref` commit `56289024`.

| run | code | set 001: equal to expected / to wexp-ref | set 002: equal to expected / to wexp-ref |
|---|---|---|---|
| 1 | as frozen | 87 / 87 of 89 | 35 / 35 of 35 |
| 2 | after two reading alignments | 89 / 89 of 89 | 35 / 35 of 35 |

The two run-1 differences, P08 and P18, are both places where the published text admits two
readings and this implementation, written without seeing any corpus, took the reading the
corpus did not. Neither is a defect of wexp-ref and neither is an error in a frozen
expectation; an earlier independent re-derivation of the 89 expectations (`WEXP-dev/wexp-vectors`,
branch `evidence/core-02-set-001-rederivation`, commit `a936c891`, directory
`evidence/core-02-set-001-rederivation/`, on main since 2026-11-08, merge commit `edd67056`) had already recorded exactly these two
questions as open. [`CHANGES-AFTER-RUN.md`](CHANGES-AFTER-RUN.md) holds the
classification, the two readings with the text they rest on, and the exact change made.
[`RUN-RECORD.json`](RUN-RECORD.json) identifies the frozen commit, the code digests after the
change, the runner and corpora compared against, and both runs;
[`comparison-before-alignment.json`](comparison-before-alignment.json) and
[`comparison.json`](comparison.json) are the per-case results of runs 1 and 2.

Agreement with a corpus and with another implementation is what it says and nothing more:
the specification remains the authority, the corpora are same-project work, and this record
is not a statement about the correctness or completeness of any implementation.

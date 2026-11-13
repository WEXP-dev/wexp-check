# Changes made after the first corpus run, with their classification

The code was frozen (FREEZE.md, commit of that file) and run once, unchanged, against
the two published Core-02 corpora. `comparison-before-alignment.json` is that run.
Two cases differed from the frozen expectations. Both were classified before any code
was changed; the classification is recorded here together with what was changed and why.

| case | frozen expectation and wexp-ref | wexp_check as frozen | class |
|---|---|---|---|
| P08 | `E_MALFORMED_NORMALIZED_INPUT` | `E_PROFILE_MAPPING_INVALID` | ambiguity of the text (same open question as the re-derivation record's P08) |
| P18 | `E_PROFILE_MAPPING_INVALID` | `E_MALFORMED_NORMALIZED_INPUT` | ambiguity of the text (same open question as the re-derivation record's P18) |

Neither is a defect of wexp-ref and neither is an error in the frozen expectation: an
independent re-derivation of all 89 expectations from the text had already produced the
frozen reading for both cases as its primary reading and recorded the reading wexp_check
took as the alternative. wexp_check, written without seeing either, landed on the
alternative in both. None of the section 7 matrix questions (A1-A6) is involved; set 002
agreed 35 / 35 before any change.

## P08: lone surrogate inside an extension-key atom

Text. Section 13: opaque fixture atoms "compare by exact Unicode scalar text". Section 12:
"A malformed pair or a missing, empty, or non-text atom produces E_MALFORMED_NORMALIZED_INPUT
at the structural check in Section 6.2. For a structurally valid key, an unbound or ambiguous
profile or local-name binding [...] produces E_PROFILE_MAPPING_INVALID".

Readings. (a) A string holding a lone surrogate (U+D800) is not Unicode scalar text, so the
atom is a non-text atom and the key is malformed: structural check 3. (b) Any JSON string is
a text atom; the pair is structurally valid and its profile is unbound: cross-field check 4.
wexp_check as frozen implemented (b) implicitly (it tested `isinstance(value, str)` only); the
frozen corpus, wexp-ref and the re-derivation hold (a).

Change. `wexp_check/ingress.py`: a text atom must be a Python `str` that encodes as UTF-8,
which excludes lone surrogates; applied uniformly to opaque atoms, profile-scoped atom pairs
and extension-key pairs. Section comment `13` added at the check.

## P18: `current_scope_capability` naming a recognized but disallowed capability

Text. Section 6: the marker "names exactly that initial capability" and "a disallowed or
mismatched current-scope marker [...] produces E_PROFILE_MAPPING_INVALID at the cross-field
check"; section 6.2 check 3: "unknown closed-enum value [...] returns
E_MALFORMED_NORMALIZED_INPUT"; section 12 lists the twelve closed initial names.

Readings. (a) The field's closed enumeration is the twelve initial capability names; a
recognized name that is neither authenticity nor composition is a disallowed marker, a
cross-field violation (check 4). An unrecognized name (P19) stays malformed under both
readings. (b) The field's closed enumeration is {authenticity, composition}; anything else is
an unknown closed-enum value (check 3). wexp_check as frozen implemented (b); the frozen
corpus, wexp-ref and the re-derivation hold (a).

Change. `wexp_check/ingress.py`: structural check accepts any of the twelve initial names;
the cross-field pass rejects a marker outside {authenticity, composition} with
`E_PROFILE_MAPPING_INVALID` before the marker-token agreement test. One unit test that
encoded reading (b) for a `target-binding` marker was moved to the cross-field expectation,
and this is noted at the test.

## After the change

`comparison.json`: set 001 89 / 89 equal to the frozen expectations and to wexp-ref; set 002
35 / 35. The unit tests pass. No other file of the frozen code was changed. Both decisions
are now also recorded for a reader of the code at the two comments; `DECISIONS.md` is the
implementation session's own record and was left as delivered.

The re-derivation record referred to above is `evidence/core-02-set-001-rederivation/` in
`WEXP-dev/wexp-vectors`, branch `evidence/core-02-set-001-rederivation`, commit `a936c891`
(not yet on main at the time of writing); its `rederived/AMBIGUITIES.json` lists P08 and P18.

## Changes after the independent review (run 3)

A review of the repository at commit `7b5ab8e` asked for two code changes; neither alters
any corpus result, and the comparison was re-run afterwards as run 3 (`RUN-RECORD.json`):

1. `wexp_check/ingress.py`, ordered check 1: `semantics_version` is now tested with the same
   scalar-text rule as every other atom, so a string holding a lone surrogate is a non-text
   atom and `E_MALFORMED_NORMALIZED_INPUT`, consistent with the P08 alignment above (section
   6.2 check 1: "semantics_version is absent or is not a text atom"). Previously any JSON string
   passed check 1 and fell to check 2. Not exercised by either corpus.
2. `wexp_check/core.py`: `appraise()` now checks the profile catalog shape itself (previously
   only the command line did), so a malformed catalog raises `ValueError` instead of an
   arbitrary `KeyError`. Harness precondition only; no Core semantics involved.

Also in the same commit: `pyproject.toml` build floor raised to `setuptools>=77` (SPDX license
string), `-B` in the test subprocess and a `.gitignore`, the wording of one sentence in
`FREEZE.md`, the citations and set 002 status in `README.md`, and `docs/REPRESENTATION.md`.

## After the push of `391eda17`: the comparison driver

`scripts/compare_corpora.py` (not part of `wexp_check`) exited with status 0 whatever it found, and
a case removed from a corpus went unnoticed. A negative control showed both (run 4, attempt a). The
driver now exits non-zero and names the set and case when any case disagrees, when a case is missing
from or added to the `--baseline` comparison file, when an engine raises or mutates its input, and
when a `corpus.json` differs from the case count or digest of the `manifest.json` beside it. The
per-case output of a passing run is unchanged (identical to `comparison.json`). No file of
`wexp_check/` and no expectation changed.

## Note on wording (added after the runs)

The sections above keep their wording as of the time of the runs; three phrases in them
("independent re-derivation", the implementation not having seen the corpus expectations, and
"independent review" in the run 3 heading), and "isolated implementation session" in
`FREEZE.md`, which is not changed, are qualified here.

wexp_check was written in a separate AI-assisted session operated by the same person as wexp-ref.
That the session did not consult wexp-ref or any WEXP corpus expectations is an operator
declaration and has not been independently verified; the wexp-ref Core-02 module was public before
wexp_check started. Its initial version was frozen before the first recorded corpus comparison
(`FREEZE.md`, `b28d00af`); later changes are documented in this file.

A separate session, operated by the same person, re-derived the 89 set 001 expected results in
`WEXP-dev/wexp-vectors`; that it consulted neither appraiser is an operator declaration and has
not been independently verified.

The original comparison runs were performed under the same operator and do not establish
independent implementation provenance. The reviewer of commit `7b5ab8e` is not named here, and
this record does not establish that the review was independent.

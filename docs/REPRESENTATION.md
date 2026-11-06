# Representation note handed to the author (local JSON harness)

This is the representation description that was given to the implementation session together
with the published text. It is an excerpt of the README of the public corpus package
`WEXP-CORE-02-VECTORS-001` in `WEXP-dev/wexp-vectors` (its "Logical encoding" section), reproduced
unchanged below so that the input and output contract of `wexp_check` can be read from this
repository alone. It describes a local test representation, not a WEXP wire format.

## Logical encoding

The local JSON harness is not a WEXP wire format. Opaque atoms use exact Unicode
scalar text. Scoped atoms and extension keys are ordered two-element arrays;
sets and the capability map are arrays with logical set/map semantics. Null
represents unavailable, not an absent component. Booleans must not compare equal
to numbers. Do not normalize Unicode, URLs, case, atom-pair order or remove
unexpected duplicate output members while comparing results.

Input collections declared as mathematical sets must not contain repeated equal
members in this representation. Duplicate aggregate keys and duplicate capability
keys are retained as explicit mapping-error controls, not silently deduplicated.
Malformed JSON, duplicate JSON object members and resource-limit failures occur
before this logical representation and must not manufacture a Core appraisal.

The fixture profile is `draft-sergeev-wexp-core-02/fixture-1`, exactly as defined
by section 13. Positive extension controls apply a separately identified local
`wexp-core02-test-profile/extension-1`; they do not redefine that normative profile.
Its catalog is carried in the cases. Negative catalog-resolution controls are
explicitly invalid resolutions, not alternative definitions of the fixture.


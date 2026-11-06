# Decisions where the published text admitted two readings

Each entry names the point, the readings seen, and the reading implemented (with the code
location). Section numbers refer to draft-sergeev-wexp-core-02.

## D1. Repeated equal members in a set-valued input collection

- Reading A: a repeated equal member of a mathematical set (qualifiers, basis_refs, reasons,
  limitations, profile_identifiers, affected_claims, fatal_conditions, inherited_limitations, and
  the entry collections recorder_relations, counter_evidence, profile_evaluation_gaps) is a
  "malformed set" and returns E_MALFORMED_NORMALIZED_INPUT at 6.2 step 3.
- Reading B: 6.1 says the carrier "either normalizes repeated representations ... or rejects them
  under its own mapping rules", so a duplicate would be a carrier failure with no Core result.
- Chosen: A (`ingress._set`). The representation document says sets "must not contain repeated
  equal members"; 6.2 step 3 names a malformed set as a Core rejection. Aggregates (base and
  qualifier findings) are instead keyed collections: a duplicate aggregate key, even byte-identical,
  is E_PROFILE_MAPPING_INVALID per 6 and 6.1, and a duplicate evaluation-scope key is
  E_PROFILE_MAPPING_INVALID per 12.

## D2. Binding of profile-scoped atoms to applied profiles

- Reading A: only profile gap entries require their scoped atoms to be bound (6 states "an unbound
  profile-scoped atom produces E_PROFILE_MAPPING_INVALID" in the gap-entry paragraph).
- Reading B: every profile-scoped atom (basis_refs and limitations of every finding, counter entry
  and gap, inherited_limitations, recorder relation subject_ref/object_ref) must name an applied
  profile_identifier, because 6.1 defines a scoped atom as a pair under an applied immutable
  profile identity and 6.2 step 4 lists "profile or registry identity" as a cross-field invariant.
- Chosen: B (`ingress._cross_field.bound`). Binding checks membership in
  evaluation_context.profile_identifiers only; the identity need not be present in the catalog
  (the catalog is consulted for tokens, relation vocabularies and extension names).

## D3. Core tokens versus catalog entries of the same name

- Reading A: a Core token (Table 3) is bound to the semantics version and resolves through the
  Core registry regardless of any catalog entry with the same name.
- Reading B: a profile registering a Core token name creates an ambiguity.
- Chosen: A (`tokens.resolve`). Two applied profiles registering the same non-Core token are
  ambiguous even when their entries agree ("exactly one immutable registry revision").

## D4. Predicate of the E_BASE_EXCEEDS_BOUNDARY row

- Reading A: usable boundary, asserted-base aggregate present, asserted base deeper than the
  ceiling, independently of that aggregate's statuses (8.6: "requires a usable boundary and a
  present asserted-base aggregate whose base is deeper than the ceiling").
- Reading B: only when the present aggregate also passes ("a present supported base excluded by
  the ceiling produces E_BASE_EXCEEDS_BOUNDARY").
- Chosen: A (`core.appraise`, first diagnostic loop). Reading B's sentence is read as a
  consequence, not as a narrower predicate.

## D5. When boundary reasons are projected

- Reading A: the boundary is a premise of every claim, so its registered reasons always project.
- Reading B: 8.6 projects them "from the boundary when it determines the asserted claim or a
  reported support entry": when the boundary is non-passing (status or binding), when its ceiling
  excludes the asserted base, or when at least one support entry exists.
- Chosen: B (`core.appraise`, `projected`). A passing, non-excluding boundary with no supported
  claim does not project its reasons.

## D6. Limitations "attached to findings that determine a reason or gap for the asserted claim"

- Reading A: limitations of every asserted-role finding, whatever it produced.
- Reading B: limitations of a finding that was the source of a matrix row for the asserted claim or
  whose non-empty registered reasons were projected; premises contribute through support entries;
  boundary limitations always (8.1 lists them unconditionally).
- Chosen: B (`core.appraise`, `limitations`). A passing asserted-role finding with no row, no
  reasons and no support entry (for example when the boundary is unsupported) contributes nothing.

## D7. Missing initial capability name in evaluation_scope

- Reading A: a missing initial name is a missing required member, E_MALFORMED_NORMALIZED_INPUT.
- Reading B: it is an evaluation-scope consistency failure, E_PROFILE_MAPPING_INVALID (6.2 step 4
  lists "evaluation-scope consistency"; 12 places duplicate keys there too).
- Chosen: B (`ingress._cross_field`). Structural checks on the scope map cover each entry's shape,
  the closed initial names, and extension-key atoms (12: malformed pair, missing, empty or non-text
  atom are structural).

## D8. Affected-claim sets mixing admissible and inadmissible claims

- Reading A: any inadmissible member invalidates the set.
- Reading B: the set is valid when it "names at least one admissible affected claim" (6); other
  members are carried and never match a claim.
- Chosen: B (`ingress.names_admissible`). A structurally well-formed but inadmissible claim such as
  (intent, {PROV}) is well-formed per 4.4.

## D9. ceiling_base present on a non-supported boundary

- Reading A: the value is ignored entirely.
- Reading B: it is still a closed-enum member and is type-checked at step 3; only its use by the
  algorithm is suppressed.
- Chosen: B (`ingress._BOUNDARY`).

## D10. Shared-role capabilities and the not-evaluated value

- Reading A: every capability set to not-evaluated requires some governed field to be not-evaluated.
- Reading B: 12 states that rule only for base-support capabilities and provenance-support (single
  role); shared roles (target-binding, independent-verification) and boundary-grounding may be
  not-evaluated for an unexercised or unrepresented role. The converse (evaluated with a governed
  not-evaluated field) applies to all finding-backed capabilities.
- Chosen: B (`ingress._cross_field`, `single_role` and the evaluated checks). The claim-required
  presence rule (asserted base, PROV or IV aggregate must exist when its capability is
  not-evaluated) is applied regardless of the asserted claim's admissibility, since step 4 runs
  before step 6.

## D11. Counter-entry limitations in inherited_limitations

- Reading A: only blocking entries contribute limitations.
- Reading B: 8.1 includes limitations from "each counter-evidence or profile-gap entry whose
  affected claims include the asserted claim, a member of SupportedClaims, or
  all-admissible-claims" with no status condition.
- Chosen: B (`core.appraise`, counter loop). A resolved-no-defeat entry affecting the asserted
  claim contributes its limitations without blocking.

## D12. Output ordering of set- and map-valued arrays

- Reading A: carry input arrays through in input order.
- Reading B: emit every set- or map-valued array (including evaluation_scope and counter_evidence)
  sorted by the compact JSON encoding of its members.
- Chosen: B (`core.union`, `ingress._set`). 8.4 says ordering is defined by the result carrier and
  logical sets are order-independent; the carried values are logically unchanged.

## D13. relation_token syntax

- Reading A: the section 15 token syntax applies to relation tokens.
- Reading B: section 15 governs the reason-code registry; a relation token is a member of a
  profile-defined vocabulary and is a text atom bound through the catalog's relation_tokens.
- Chosen: B (`ingress._RELATION`).

## D14. Empty text atoms

- Reading A: every text atom must be non-empty.
- Reading B: only extension-key components are required to be non-empty (12); opaque atoms and
  scoped-atom components are compared, not interpreted.
- Chosen: B. An empty semantics_version is a text atom and fails step 2, not step 1.

## D15. Catalog shape failures

- The text defines no catalog; the brief defines it. A catalog that is not a map of identities to
  `{tokens, relation_tokens, scope_names}` is treated as a harness decoding failure (exit 2), not
  a Core result (`tokens.check_catalog`). An applied identity absent from the catalog is not an
  error by itself; it merely resolves nothing.

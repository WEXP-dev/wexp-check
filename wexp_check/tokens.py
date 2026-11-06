"""Core reason-code registry (section 15, Table 3) and token resolution (section 6)."""

# 15 Table 3: token -> (category, current-scope capability or None).
CORE_TOKENS = {
    "E_MALFORMED_NORMALIZED_INPUT": ("fatal", None),
    "E_UNSUPPORTED_SEMANTICS_VERSION": ("fatal", None),
    "E_CLAIM_OUT_OF_DOMAIN": ("fatal", None),
    "E_UNKNOWN_CRITICAL_SEMANTIC": ("fatal", None),
    "E_INTEGRITY_INVALID": ("fatal", None),
    "E_BINDING_MISMATCH": ("fatal", None),
    "E_PROFILE_MAPPING_INVALID": ("fatal", None),
    "E_CHAIN_DESCRIPTION_INVALID": ("fatal", None),
    "E_CHAIN_UNBOUND": ("substantive", None),
    "E_SHARED_VERIFICATION_ROOT": ("substantive", None),
    "E_BASE_EXCEEDS_BOUNDARY": ("substantive", None),
    "E_BOUNDARY_NOT_SUPPORTED": ("substantive", None),
    "E_EXACT_CLAIM_NOT_SUPPORTED": ("substantive", None),
    "E_MISSING_REQUIRED_EVIDENCE": ("substantive", None),
    "E_EVIDENCE_NOT_BOUND": ("substantive", None),
    "E_EVIDENCE_COVERAGE_MISMATCH": ("substantive", None),
    "E_PROV_NOT_SUPPORTED": ("substantive", None),
    "E_IV_NOT_SUPPORTED": ("substantive", None),
    "E_COUNTER_EVIDENCE_UNRESOLVED": ("substantive", None),
    "E_COUNTER_EVIDENCE_DEFEATING": ("substantive", None),
    "E_COMPOSITION_WARRANT_MISSING": ("substantive", None),
    "E_INDEPENDENCE_NOT_ESTABLISHED": ("substantive", None),
    "E_BASE_NOT_EVALUATED": ("evaluation-gap", None),
    "E_BOUNDARY_NOT_EVALUATED": ("evaluation-gap", None),
    "E_PROV_NOT_EVALUATED": ("evaluation-gap", None),
    "E_IV_NOT_EVALUATED": ("evaluation-gap", None),
    "E_COMPOSITION_NOT_EVALUATED": ("evaluation-gap", "composition"),
    "E_COUNTER_EVIDENCE_NOT_EVALUATED": ("evaluation-gap", None),
}

# 6.2: derived only by the ordered Core checks; invalid as supplied fatal_conditions members.
APPRAISER_DERIVED = frozenset((
    "E_MALFORMED_NORMALIZED_INPUT", "E_UNSUPPORTED_SEMANTICS_VERSION",
    "E_PROFILE_MAPPING_INVALID", "E_CLAIM_OUT_OF_DOMAIN"))


def resolve(token, applied, catalog):
    """Resolve a token to (category, current_scope_capability); None if absent or ambiguous.

    6: a Core token is bound to the semantics version; a non-Core token resolves
    uniquely through exactly one immutable registry revision identified by an
    applied profile_identifier (an applied identity absent from the catalog resolves nothing).
    """
    if token in CORE_TOKENS:
        return CORE_TOKENS[token]
    hits = [catalog[pid]["tokens"][token] for pid in applied
            if pid in catalog and token in catalog[pid]["tokens"]]
    if len(hits) != 1:  # 6: absence or ambiguity
        return None
    return (hits[0]["category"], hits[0].get("current_scope_capability"))


def check_catalog(catalog):
    """Reject a profile catalog that does not have the documented shape (a harness failure)."""
    def entry_ok(e):
        return (isinstance(e, dict) and set(e) <= {"category", "current_scope_capability"}
                and isinstance(e.get("category"), str)
                and isinstance(e.get("current_scope_capability", ""), str))

    def profile_ok(p):
        return (isinstance(p, dict) and set(p) == {"tokens", "relation_tokens", "scope_names"}
                and isinstance(p["tokens"], dict) and all(entry_ok(e) for e in p["tokens"].values())
                and all(isinstance(p[k], list) and all(isinstance(x, str) for x in p[k])
                        for k in ("relation_tokens", "scope_names")))

    if not (isinstance(catalog, dict) and all(profile_ok(p) for p in catalog.values())):
        raise ValueError("profile catalog does not map profile identities to "
                         "{tokens, relation_tokens, scope_names}")

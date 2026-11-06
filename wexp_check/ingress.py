"""Core ingress: the ordered checks of section 6.2 over the logical input of
sections 6, 6.1 and the evaluation-scope contract of section 12.

The structural pass (6.2 step 3) runs completely before the cross-field pass
(6.2 step 4); every check raises ``Rejection`` carrying the fatal token set.
Values are rebuilt into fresh canonical structures (sets sorted by their
compact JSON encoding), so the caller's input is never mutated.
"""
import json
import re

from .tokens import APPRAISER_DERIVED, resolve

VERSION = "wexp-core-2"
ALL = "all-admissible-claims"
BASES = ("observation", "intent", "invocation", "execution")  # 4.2, in depth order
QUALIFIERS = ("PROV", "IV")  # 4.3
TRI = ("supported", "unsupported", "not-evaluated")  # 6
GROUNDING = ("asserted-only", "attributed", "attested", "not-evaluated")  # 6
INDEPENDENCE = TRI + ("not-applicable",)  # 6
COUNTER_STATUS = ("not-supplied", "not-evaluated", "resolved-no-defeat",
                  "unresolved-material", "defeating")  # 6
SCOPE_STATUS = ("evaluated", "not-evaluated")  # 12
CURRENT_SCOPE = ("authenticity", "composition")  # 6
INITIAL_CAPABILITIES = (  # 12: closed initial names for wexp-core-2
    "carrier-mapping", "authenticity", "target-binding", "boundary-grounding",
    "observation-support", "intent-support", "invocation-support", "execution-support",
    "provenance-support", "independent-verification", "composition", "counter-evidence")
TOKEN_RE = re.compile(r"[A-Z][A-Z0-9_]*")  # 15: token syntax
NE = "not-evaluated"


class Rejection(Exception):
    """A Core rejection branch; ``tokens`` is the fatal_reasons set (6.2)."""

    def __init__(self, *tokens):
        super().__init__(", ".join(tokens))
        self.tokens = sorted(tokens)


def cj(value):
    """Compact JSON encoding used as the canonical comparison key of a logical value."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def admissible(claim):
    """4.4: PROV is absent or the base is execution."""
    return "PROV" not in claim["qualifiers"] or claim["base"] == "execution"


def names_admissible(affected):
    """6: an affected-claim set names at least one admissible claim or all-admissible-claims."""
    return affected == ALL or any(admissible(c) for c in affected)


# ---------------------------------------------------------------- 6.2 step 3: structural pass

def _malformed():
    return Rejection("E_MALFORMED_NORMALIZED_INPUT")


def _is_scalar_text(v):
    # 13: opaque atoms are exact Unicode scalar text; a lone surrogate is not a Unicode scalar value
    if not isinstance(v, str):
        return False
    try:
        v.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _text(v):
    if not _is_scalar_text(v):
        raise _malformed()
    return v


def _enum(members):
    def check(v):
        if not isinstance(v, str) or v not in members:  # 6.1: closed enumeration, exact names
            raise _malformed()
        return v
    return check


def _token(v):
    if not isinstance(v, str) or not TOKEN_RE.fullmatch(v):  # 15: token syntax
        raise _malformed()
    return v


def _scoped(v):
    # 6.1: profile-scoped atom == ordered pair (profile_identifier, local_value) of text atoms
    if not isinstance(v, list) or len(v) != 2 or not all(_is_scalar_text(x) for x in v):
        raise _malformed()
    return list(v)


def _list(member):
    def check(v):
        if not isinstance(v, list):
            raise _malformed()
        return [member(x) for x in v]
    return check


def _set(member):
    def check(v):
        out = _list(member)(v)
        keys = [cj(x) for x in out]
        if len(set(keys)) != len(keys):  # 6.1: equal members occur once (DECISIONS D1)
            raise _malformed()
        return [x for _, x in sorted(zip(keys, out))]
    return check


def _record(schema, optional=()):
    def check(v):
        if not isinstance(v, dict):
            raise _malformed()
        required = set(schema) - set(optional)
        if not required <= set(v) <= set(schema):  # 6.2 step 3: missing or unknown member
            raise _malformed()
        return {k: schema[k](v[k]) for k in schema if k in v}
    return check


def _claim_check(v):
    return _record({"base": _enum(BASES), "qualifiers": _set(_enum(QUALIFIERS))})(v)


def _affected(v):
    return ALL if v == ALL else _set(_claim_check)(v)


def _capability(v):
    if isinstance(v, str):
        return _enum(INITIAL_CAPABILITIES)(v)
    # 12: extension key == pair of two non-empty text atoms
    if not isinstance(v, list) or len(v) != 2 or not all(_is_scalar_text(x) and x for x in v):
        raise _malformed()
    return list(v)


_SCOPE = {"target": _text, "evaluation_context_ref": _text}
_SETS = {"basis_refs": _set(_scoped), "reasons": _set(_token), "limitations": _set(_scoped)}
_BOUNDARY = _record(_SCOPE | {"ceiling_base": _enum(BASES), "status": _enum(TRI),
                              "target_binding": _enum(TRI), "grounding": _enum(GROUNDING)} | _SETS,
                    optional=("ceiling_base",))  # 6: ceiling_base REQUIRED only when supported
_BASE_FINDING = _record(_SCOPE | {"base": _enum(BASES), "target_binding": _enum(TRI),
                                  "semantic_validation": _enum(TRI)} | _SETS)
_QUALIFIER_FINDING = _record(_SCOPE | {
    "qualifier": _enum(QUALIFIERS), "qualified_base": _enum(BASES), "target_binding": _enum(TRI),
    "semantic_validation": _enum(TRI), "independence_validation": _enum(INDEPENDENCE)} | _SETS)
_RELATION = _record({"profile_identifier": _text, "relation_token": _text, "subject_ref": _scoped,
                     "object_ref": _scoped, "basis_refs": _set(_scoped), "limitations": _set(_scoped)})
_COUNTER = _record({"status": _enum(COUNTER_STATUS), "affected_claims": _affected} | _SETS)
_GAP = _record(_SCOPE | {"token": _token, "current_scope_capability": _enum(INITIAL_CAPABILITIES),
                         "affected_claims": _affected, "basis_refs": _set(_scoped),
                         "limitations": _set(_scoped)},
               optional=("current_scope_capability",))
_CONTEXT = _record({"id": _text, "evaluated_at": _text, "trust_configuration": _text,
                    "profile_identifiers": _set(_text)})
_INPUT = _record({
    "semantics_version": _text, "target": _text, "asserted_claim": _claim_check,
    "evaluation_context": _CONTEXT, "boundary_finding": _BOUNDARY,
    "base_findings": _list(_BASE_FINDING), "qualifier_findings": _list(_QUALIFIER_FINDING),
    "recorder_relations": _set(_RELATION), "counter_evidence": _set(_COUNTER),
    "evaluation_scope": _list(_record({"capability": _capability, "status": _enum(SCOPE_STATUS)})),
    "profile_evaluation_gaps": _set(_GAP), "inherited_limitations": _set(_scoped),
    "fatal_conditions": _set(_token)})


# ---------------------------------------------------------------- 6.2 step 4: cross-field pass

def _cross_field(n, catalog):
    invalid = Rejection("E_PROFILE_MAPPING_INVALID")
    ctx = n["evaluation_context"]
    applied, target, cid = ctx["profile_identifiers"], n["target"], ctx["id"]

    def bound(atom):  # 6, 6.1: a profile-scoped atom is bound to an applied profile (DECISIONS D2)
        if atom[0] not in applied:
            raise invalid

    def category(token, expected):  # 6: registry identity and token category
        found = resolve(token, applied, catalog)
        if found is None or found[0] != expected:
            raise invalid
        return found

    def scoped_sets(entry):
        for atom in entry["basis_refs"] + entry["limitations"]:
            bound(atom)

    def finding(f):
        if f["target"] != target or f["evaluation_context_ref"] != cid:  # 6: exact scope
            raise invalid
        scoped_sets(f)
        for token in f["reasons"]:  # 6: finding reasons are substantive
            category(token, "substantive")

    boundary = n["boundary_finding"]
    finding(boundary)
    if boundary["status"] == "supported" and "ceiling_base" not in boundary:  # 6: conditional ceiling_base
        raise invalid
    if (boundary["grounding"] == NE) != (boundary["status"] == NE):  # 6: grounding pairing
        raise invalid

    bases, quals = {}, {}
    for f in n["base_findings"]:
        finding(f)
        if f["base"] in bases:  # 6: at most one aggregate per (target, base, context)
            raise invalid
        bases[f["base"]] = f
    for f in n["qualifier_findings"]:
        finding(f)
        key = (f["qualifier"], f["qualified_base"])
        if key in quals:  # 6: at most one aggregate per (target, qualifier, qualified_base, context)
            raise invalid
        quals[key] = f
        if f["qualifier"] == "PROV" and (f["qualified_base"] != "execution"
                                         or f["independence_validation"] != "not-applicable"):
            raise invalid  # 6: PROV aggregate validity
        if f["qualifier"] == "IV" and f["independence_validation"] == "not-applicable":
            raise invalid  # 6: IV aggregate validity

    for r in n["recorder_relations"]:  # 6.1: profile_identifier binds the relation vocabulary
        if r["profile_identifier"] not in applied or r["relation_token"] not in \
                catalog.get(r["profile_identifier"], {}).get("relation_tokens", ()):
            raise invalid
        bound(r["subject_ref"])
        bound(r["object_ref"])
        scoped_sets(r)

    counter = n["counter_evidence"]
    sentinel = [c for c in counter if c["status"] == "not-supplied"]
    if sentinel:  # 6: exactly one empty not-supplied entry when nothing was supplied
        if len(counter) != 1 or any(sentinel[0][k] for k in
                                    ("affected_claims", "basis_refs", "reasons", "limitations")):
            raise invalid
    elif not counter:  # 6: the entry set is never empty
        raise invalid
    for c in counter:
        if c["status"] != "not-supplied" and not names_admissible(c["affected_claims"]):
            raise invalid  # 6: every other entry names an admissible affected claim
        scoped_sets(c)
        for token in c["reasons"]:  # 6: counter reasons are substantive
            category(token, "substantive")

    for token in n["fatal_conditions"]:  # 6, 6.2: supplied fatal members
        if token in APPRAISER_DERIVED:
            raise invalid
        category(token, "fatal")

    markers = set()
    for g in n["profile_evaluation_gaps"]:  # 6: structured profile gaps
        if g["target"] != target or g["evaluation_context_ref"] != cid:
            raise invalid
        scoped_sets(g)
        if not names_admissible(g["affected_claims"]):
            raise invalid
        _, marker_capability = category(g["token"], "evaluation-gap")
        if "current_scope_capability" in g:
            if g["current_scope_capability"] not in CURRENT_SCOPE:  # 6: recognized initial capability that is not authenticity or composition is a disallowed marker (cross-field)
                raise invalid
            if g["current_scope_capability"] != marker_capability:  # 6, 15: marker-token mismatch
                raise invalid
            markers.add(marker_capability)
    for atom in n["inherited_limitations"]:
        bound(atom)

    scope = {}
    for e in n["evaluation_scope"]:  # 12
        cap = e["capability"]
        if isinstance(cap, list) and (cap[0] not in applied or cap[1] not in
                                      catalog.get(cap[0], {}).get("scope_names", ())):
            raise invalid  # 12: unbound extension key
        if cj(cap) in scope:  # 12: duplicate key
            raise invalid
        scope[cj(cap)] = e["status"]
    if any(cj(name) not in scope for name in INITIAL_CAPABILITIES):  # 12: every initial name once
        raise invalid

    def status(name):
        return scope[cj(name)]

    if status("carrier-mapping") != "evaluated":  # 12
        raise invalid
    for cap in CURRENT_SCOPE:  # 12: fully syntactic marker rule
        if (status(cap) == NE) != (cap in markers):
            raise invalid
    findings = [boundary, *bases.values(), *quals.values()]
    if status("target-binding") == "evaluated" and any(f["target_binding"] == NE for f in findings):
        raise invalid  # 12: governed field under an evaluated capability
    if status("boundary-grounding") == "evaluated" and NE in (
            boundary["status"], boundary["target_binding"], boundary["grounding"]):
        raise invalid
    ivs = [f for (q, _), f in quals.items() if q == "IV"]
    if status("independent-verification") == "evaluated" and any(NE in (
            f["target_binding"], f["semantic_validation"], f["independence_validation"]) for f in ivs):
        raise invalid

    def single_role(cap, f):  # 12: present single-role aggregate agrees with its capability
        if f is not None and (status(cap) == NE) != (NE in (f["target_binding"], f["semantic_validation"])):
            raise invalid

    for base in BASES:
        single_role(base + "-support", bases.get(base))
    single_role("provenance-support", quals.get(("PROV", "execution")))

    claim = n["asserted_claim"]  # 12: claim-required not-evaluated capability needs its aggregate
    if status(claim["base"] + "-support") == NE and claim["base"] not in bases:
        raise invalid
    if "PROV" in claim["qualifiers"] and status("provenance-support") == NE \
            and ("PROV", "execution") not in quals:
        raise invalid
    if "IV" in claim["qualifiers"] and status("independent-verification") == NE \
            and ("IV", claim["base"]) not in quals:
        raise invalid


def ingest(value, catalog):
    """Run the ordered checks of 6.2; return the canonical input or raise Rejection."""
    # 6.2 check 1
    if not isinstance(value, dict) or not isinstance(value.get("semantics_version"), str):
        raise _malformed()
    # 6.2 check 2
    if value["semantics_version"] != VERSION:
        raise Rejection("E_UNSUPPORTED_SEMANTICS_VERSION")
    # 6.2 check 3
    n = _INPUT(value)
    # 6.2 check 4
    _cross_field(n, catalog)
    # 6.2 check 5
    if n["fatal_conditions"]:
        raise Rejection(*n["fatal_conditions"])
    # 6.2 check 6
    if not admissible(n["asserted_claim"]):
        raise Rejection("E_CLAIM_OUT_OF_DOMAIN")
    return n

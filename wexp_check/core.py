"""Appraisal procedure: sections 7, 8.1 to 8.6 of draft-sergeev-wexp-core-02."""
from itertools import combinations

from .ingress import ALL, BASES, NE, VERSION, Rejection, cj, ingest

DEPTH = {b: i for i, b in enumerate(BASES)}  # 4.2 structural content-depth order
UNSUPPORTED = "unsupported"
BLOCKING = ("not-evaluated", "unresolved-material", "defeating")  # 8.2
RESULT_KEYS = (
    "semantics_version", "verdict", "fatal_reasons", "target", "asserted_claim",
    "asserted_claim_supported", "support_entries", "supported_claims", "maximal_supported_claims",
    "support_relations", "boundary_ceiling", "boundary_grounding", "recorder_relations",
    "substantive_reasons", "evaluation_gaps", "evaluation_gap_entries", "counter_evidence",
    "inherited_limitations", "evaluation_context", "evaluation_scope")


def leq(c1, c2):
    """4.5 structural order: b1 <= b2 and A1 subset of A2."""
    return DEPTH[c1["base"]] <= DEPTH[c2["base"]] and set(c1["qualifiers"]) <= set(c2["qualifiers"])


def union(*collections):
    """6.1 set union under logical equality, emitted sorted by compact JSON encoding."""
    return [v for _, v in sorted({cj(x): x for c in collections for x in c}.items())]


def rejected_result(tokens):
    """8.4 rejected_result: the fixed rejection projection."""
    result = dict.fromkeys(RESULT_KEYS)
    result.update(semantics_version=VERSION, verdict="reject", fatal_reasons=sorted(tokens),
                  asserted_claim_supported=False)
    for key in ("support_entries", "supported_claims", "maximal_supported_claims",
                "support_relations", "substantive_reasons", "evaluation_gaps",
                "evaluation_gap_entries"):
        result[key] = []
    return result


def appraise(normalized_input, profiles):
    """Appraise one logical AppraisalInput against a profile catalog (8.4). Mutates neither."""
    try:
        n = ingest(normalized_input, profiles)
    except Rejection as rejection:
        return rejected_result(rejection.tokens)

    target, cid = n["target"], n["evaluation_context"]["id"]
    claim, boundary = n["asserted_claim"], n["boundary_finding"]
    bases = {f["base"]: f for f in n["base_findings"]}
    quals = {(f["qualifier"], f["qualified_base"]): f for f in n["qualifier_findings"]}

    def passes(f, *fields):
        return f is not None and all(f[k] == "supported" for k in fields)

    # 7, 8.1 rule 3: only a supported, target-bound, correctly scoped boundary makes the ceiling usable
    usable = (passes(boundary, "status", "target_binding") and boundary["target"] == target
              and boundary["evaluation_context_ref"] == cid)
    ceiling = boundary["ceiling_base"] if usable else None

    # 8.1: B, Q(b), SupportedClaims and support entries, independently of the asserted claim
    supported, entries, premises = [], [], []
    for base, f in bases.items():
        if not (passes(f, "target_binding", "semantic_validation") and usable
                and DEPTH[base] <= DEPTH[ceiling]):  # 8.1 rules 1-4
            continue
        prov = quals.get(("PROV", "execution")) if base == "execution" else None  # 8.1 PROV
        iv = quals.get(("IV", base))  # 8.1 IV
        q_findings = {}
        if passes(prov, "target_binding", "semantic_validation"):
            q_findings["PROV"] = prov
        if passes(iv, "target_binding", "semantic_validation", "independence_validation"):
            q_findings["IV"] = iv
        for size in range(len(q_findings) + 1):
            for subset in combinations(sorted(q_findings), size):
                used = [boundary, f, *(q_findings[q] for q in subset)]
                supported.append({"base": base, "qualifiers": list(subset)})
                entries.append({"claim": supported[-1],
                                "basis_refs": union(*(p["basis_refs"] for p in used)),
                                "limitations": union(*(p["limitations"] for p in used))})
                premises.extend(used)
    maximal = [c for c in supported if not any(leq(c, d) and c != d for d in supported)]  # 8.1
    supported_keys = {cj(c) for c in supported}
    asserted_supported = cj(claim) in supported_keys  # 8.3

    def relation(m):  # 8.3
        if m == claim:
            return "equal"
        if leq(m, claim):
            return "support-below-claim"
        if leq(claim, m):
            return "support-above-claim"
        return "incomparable"

    relations = [{"supported_claim": m, "relation": relation(m)} for m in maximal]

    # 8.4 first diagnostic loop: finding and boundary rows of the 8.6 matrix
    reasons, gaps, determining, asserted_role = set(), [], [], []

    def gap(token, source):  # 8.4: Core-derived gap entry
        gaps.append({"token": token, "target": target, "evaluation_context_ref": cid,
                     "affected_claims": [claim], "basis_refs": source["basis_refs"],
                     "limitations": source["limitations"]})

    def status_rows(f, field, on_unsupported, on_not_evaluated):
        if f[field] == UNSUPPORTED:
            reasons.add(on_unsupported)
            determining.append(f)
        elif f[field] == NE:
            gap(on_not_evaluated, f)
            determining.append(f)

    status_rows(boundary, "status", "E_BOUNDARY_NOT_SUPPORTED", "E_BOUNDARY_NOT_EVALUATED")
    status_rows(boundary, "target_binding", "E_EVIDENCE_NOT_BOUND", "E_BOUNDARY_NOT_EVALUATED")
    base_finding = bases.get(claim["base"])
    if base_finding is None:
        reasons.add("E_MISSING_REQUIRED_EVIDENCE")  # 8.6: asserted-base aggregate absent
    else:
        asserted_role.append(base_finding)
        if usable and DEPTH[claim["base"]] > DEPTH[ceiling]:  # 8.6: usable boundary, deeper base
            reasons.add("E_BASE_EXCEEDS_BOUNDARY")
            determining.extend([boundary, base_finding])
        status_rows(base_finding, "target_binding", "E_EVIDENCE_NOT_BOUND", "E_BASE_NOT_EVALUATED")
        status_rows(base_finding, "semantic_validation", "E_EXACT_CLAIM_NOT_SUPPORTED",
                    "E_BASE_NOT_EVALUATED")
    for qualifier, prefix, extra in (("PROV", "E_PROV", ()),
                                     ("IV", "E_IV", ("independence_validation",))):
        if qualifier not in claim["qualifiers"]:
            continue
        f = quals.get((qualifier, "execution" if qualifier == "PROV" else claim["base"]))
        if f is None:
            reasons.add("E_MISSING_REQUIRED_EVIDENCE")  # 8.6: asserted qualifier aggregate absent
            continue
        asserted_role.append(f)
        governed = ("target_binding", "semantic_validation", *extra)
        if f["target_binding"] == UNSUPPORTED:
            reasons.add("E_EVIDENCE_NOT_BOUND")
            determining.append(f)
        if any(f[k] == NE for k in governed):  # 8.6: one gap row per qualifier aggregate
            gap(prefix + "_NOT_EVALUATED", f)
            determining.append(f)
        if f["semantic_validation"] == UNSUPPORTED:
            reasons.add(prefix + "_NOT_SUPPORTED")
            determining.append(f)
        if extra and f["independence_validation"] == UNSUPPORTED:
            reasons.add("E_INDEPENDENCE_NOT_ESTABLISHED")
            determining.append(f)

    # 8.4 second loop, 8.6: registered reasons of asserted-role findings, support premises and a
    # boundary that determines the asserted claim (DECISIONS D5)
    projected = {id(f): f for f in asserted_role + premises + determining}
    for f in projected.values():
        reasons.update(f["reasons"])

    def affects(affected, keys):  # 6, 8.4 affected-claim predicate
        return affected == ALL or any(cj(c) in keys for c in affected)

    relevant = supported_keys | {cj(claim)}
    limitations = [n["inherited_limitations"], boundary["limitations"]]  # 8.1 union
    limitations += [e["limitations"] for e in entries]
    limitations += [f["limitations"] for f in projected.values()
                    if any(f is d for d in determining) or f["reasons"]]  # 8.1: determine a reason or gap
    for g in n["profile_evaluation_gaps"]:  # 8.4: copied exactly under the affected-claim predicate
        if affects(g["affected_claims"], relevant):
            gaps.append(dict(g))
            limitations.append(g["limitations"])

    # 8.4 counter-entry loop; 8.2 per-entry blocking predicate
    blocked = False
    for c in n["counter_evidence"]:
        if affects(c["affected_claims"], relevant):
            limitations.append(c["limitations"])  # 8.1
        if c["status"] in BLOCKING and affects(c["affected_claims"], {cj(claim)}):
            blocked = True
            reasons.update(c["reasons"])  # 8.6: entry reasons of each blocking applicable entry
            if c["status"] == NE:
                gaps.append({"token": "E_COUNTER_EVIDENCE_NOT_EVALUATED", "target": target,
                             "evaluation_context_ref": cid, "affected_claims": c["affected_claims"],
                             "basis_refs": c["basis_refs"], "limitations": c["limitations"]})
            elif c["status"] == "unresolved-material":
                reasons.add("E_COUNTER_EVIDENCE_UNRESOLVED")
            else:
                reasons.add("E_COUNTER_EVIDENCE_DEFEATING")
    gap_entries = union(gaps)  # 8.4: equal gap entries collapse

    return {
        "semantics_version": VERSION,
        "verdict": "accept" if asserted_supported and not blocked else "downgrade",  # 8.2, 8.4
        "fatal_reasons": [],
        "target": target,
        "asserted_claim": claim,
        "asserted_claim_supported": asserted_supported,
        "support_entries": union(entries),
        "supported_claims": union(supported),
        "maximal_supported_claims": union(maximal),
        "support_relations": union(relations),
        "boundary_ceiling": ceiling,  # 8.5: accepted ceiling only when usable, else unavailable
        "boundary_grounding": boundary["grounding"],  # 7, 8.5: preserved even when unsupported
        "recorder_relations": n["recorder_relations"],
        "substantive_reasons": sorted(reasons),
        "evaluation_gaps": sorted({g["token"] for g in gap_entries}),  # 8.4 token projection
        "evaluation_gap_entries": gap_entries,
        "counter_evidence": n["counter_evidence"],  # 8.5: every entry preserved
        "inherited_limitations": union(*limitations),
        "evaluation_context": n["evaluation_context"],
        "evaluation_scope": union(n["evaluation_scope"]),  # 12: extension pairs and statuses preserved
    }

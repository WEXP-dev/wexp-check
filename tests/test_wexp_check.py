"""Tests for wexp_check, derived from the text of draft-sergeev-wexp-core-02 only.

The section 13 rows below were derived by hand from Table 2 and the common
fixture context stated in section 13; no external expected results were used.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

from wexp_check import appraise
from wexp_check.core import rejected_result

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
# The fixture input and profile catalog handed to the implementation session are kept under tests/fixtures.
HANDOFF = os.path.join(HERE, "fixtures")
P = "draft-sergeev-wexp-core-02/fixture-1"
PROFILES = {P: {"relation_tokens": [], "scope_names": [],
                "tokens": {"P_COUNTER_FAIL": {"category": "substantive"}}}}
CAPABILITIES = ("carrier-mapping", "authenticity", "target-binding", "boundary-grounding",
                "observation-support", "intent-support", "invocation-support", "execution-support",
                "provenance-support", "independent-verification", "composition", "counter-evidence")
LOCAL = {"observation": "O", "intent": "I", "invocation": "N", "execution": "E"}


def atom(name):
    return [P, name]


def claim(base, *qualifiers):
    return {"base": base, "qualifiers": sorted(qualifiers)}


def finding(base, **over):
    f = {"target": "T", "evaluation_context_ref": "C", "base": base, "target_binding": "supported",
         "semantic_validation": "supported", "basis_refs": [atom(LOCAL[base])], "reasons": [],
         "limitations": []}
    return f | over


def qualifier(q, base, **over):
    local = "P(E)" if q == "PROV" else "V(%s)" % LOCAL[base]
    f = {"target": "T", "evaluation_context_ref": "C", "qualifier": q, "qualified_base": base,
         "target_binding": "supported", "semantic_validation": "supported",
         "independence_validation": "not-applicable" if q == "PROV" else "supported",
         "basis_refs": [atom(local)], "reasons": [], "limitations": []}
    return f | over


def counter(status, affected, **over):
    return {"status": status, "affected_claims": affected, "basis_refs": [], "reasons": [],
            "limitations": []} | over


def gap(token, affected, basis, limitation, **over):
    return {"target": "T", "evaluation_context_ref": "C", "token": token, "affected_claims": affected,
            "basis_refs": [atom(basis)], "limitations": [atom(limitation)]} | over


def fixture(asserted, bases=(), quals=(), ceiling="intent", **over):
    """Section 13 common input values with the row's overrides."""
    data = {
        "semantics_version": "wexp-core-2", "target": "T", "asserted_claim": asserted,
        "evaluation_context": {"id": "C", "evaluated_at": "2026-10-12T00:00:00Z",
                               "trust_configuration": "core02-fixture-trust-1",
                               "profile_identifiers": [P]},
        "boundary_finding": {"target": "T", "evaluation_context_ref": "C", "ceiling_base": ceiling,
                             "status": "supported", "target_binding": "supported",
                             "grounding": "attributed", "basis_refs": [atom("bd")], "reasons": [],
                             "limitations": []},
        "base_findings": [finding(b) for b in bases],
        "qualifier_findings": [qualifier(q, b) for q, b in quals],
        "recorder_relations": [],
        "counter_evidence": [counter("not-supplied", [])],
        "evaluation_scope": [{"capability": c, "status": "evaluated"} for c in CAPABILITIES],
        "profile_evaluation_gaps": [], "inherited_limitations": [], "fatal_conditions": []}
    return data | over


def scope(data, **statuses):
    for entry in data["evaluation_scope"]:
        entry["status"] = statuses.get(entry["capability"].replace("-", "_"), entry["status"])
    return data


def entry(c, *locals_):
    return {"claim": c, "basis_refs": sorted(atom(x) for x in locals_), "limitations": []}


def expected(data, verdict, supported, maximal, relations, reasons=(), gaps=(), ceiling=None,
             limitations=(), entries=()):
    """Accept/downgrade result from the common context: unvaried fields carry through."""
    return {
        "semantics_version": "wexp-core-2", "verdict": verdict, "fatal_reasons": [],
        "target": "T", "asserted_claim": data["asserted_claim"],
        "asserted_claim_supported": data["asserted_claim"] in supported,
        "support_entries": sorted(entries, key=ckey),
        "supported_claims": sorted(supported, key=ckey),
        "maximal_supported_claims": sorted(maximal, key=ckey),
        "support_relations": sorted(({"supported_claim": c, "relation": r} for c, r in relations),
                                    key=ckey),
        "boundary_ceiling": ceiling or data["boundary_finding"]["ceiling_base"],
        "boundary_grounding": "attributed", "recorder_relations": [],
        "substantive_reasons": sorted(reasons), "evaluation_gaps": sorted(g["token"] for g in gaps),
        "evaluation_gap_entries": sorted(gaps, key=ckey),
        "counter_evidence": sorted(data["counter_evidence"], key=ckey),
        "inherited_limitations": sorted(limitations),
        "evaluation_context": data["evaluation_context"],
        "evaluation_scope": sorted(data["evaluation_scope"], key=ckey)}


def canonical(value):
    return json.loads(json.dumps(value, sort_keys=True))


def ckey(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


O, I, N, E = (claim(b) for b in LOCAL)
E_P, E_V, N_V, E_PV = claim("execution", "PROV"), claim("execution", "IV"), \
    claim("invocation", "IV"), claim("execution", "PROV", "IV")


class Section13Rows(unittest.TestCase):
    """Rows of Table 2 derived from the text, starting from the supplied C01 input."""

    def check(self, data, result):
        self.assertEqual(canonical(appraise(data, PROFILES)), canonical(result))

    def test_c01_supplied_input_end_to_end(self):
        with open(os.path.join(HANDOFF, "input", "C01.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data, fixture(I, ["intent"]))  # the supplied file is the common context
        result = expected(data, "accept", [I], [I], [(I, "equal")], entries=[entry(I, "bd", "I")])
        self.check(data, result)
        self.assertEqual(appraise(data, PROFILES)["verdict"], "accept")

    def test_c02_support_above_claim(self):
        d = fixture(I, ["execution"], ceiling="execution")
        self.check(d, expected(d, "downgrade", [E], [E], [(E, "support-above-claim")],
                               ["E_MISSING_REQUIRED_EVIDENCE"], entries=[entry(E, "bd", "E")]))

    def test_c03_incomparable_prov_alternative(self):
        d = fixture(E_V, ["execution"], [("PROV", "execution")], ceiling="execution")
        self.check(d, expected(d, "downgrade", [E, E_P], [E_P], [(E_P, "incomparable")],
                               ["E_MISSING_REQUIRED_EVIDENCE"],
                               entries=[entry(E, "bd", "E"), entry(E_P, "bd", "E", "P(E)")]))

    def test_c04_incomparable_iv_alternative(self):
        d = fixture(E_P, ["execution"], [("IV", "execution")], ceiling="execution")
        self.check(d, expected(d, "downgrade", [E, E_V], [E_V], [(E_V, "incomparable")],
                               ["E_MISSING_REQUIRED_EVIDENCE"],
                               entries=[entry(E, "bd", "E"), entry(E_V, "bd", "E", "V(E)")]))

    def test_c05_qualified_accept(self):
        d = fixture(N_V, ["invocation"], [("IV", "invocation")], ceiling="invocation")
        self.check(d, expected(d, "accept", [N, N_V], [N_V], [(N_V, "equal")],
                               entries=[entry(N, "bd", "N"), entry(N_V, "bd", "N", "V(N)")]))

    def test_c06_two_maximal_below(self):
        d = fixture(E_V, ["invocation", "execution"], [("IV", "invocation")], ceiling="execution")
        self.check(d, expected(d, "downgrade", [N, N_V, E], [N_V, E],
                               [(N_V, "support-below-claim"), (E, "support-below-claim")],
                               ["E_MISSING_REQUIRED_EVIDENCE"],
                               entries=[entry(N, "bd", "N"), entry(N_V, "bd", "N", "V(N)"),
                                        entry(E, "bd", "E")]))

    def test_c07_base_exceeds_boundary(self):
        d = fixture(E, ["execution"], ceiling="invocation")
        self.check(d, expected(d, "downgrade", [], [], [], ["E_BASE_EXCEEDS_BOUNDARY"]))

    def test_c08_missing_evidence(self):
        d = fixture(O, ceiling="observation")
        self.check(d, expected(d, "downgrade", [], [], [], ["E_MISSING_REQUIRED_EVIDENCE"]))

    def test_c09_fixed_rejection_projection(self):
        result = appraise(fixture(claim("intent", "PROV"), ["intent"]), PROFILES)
        self.assertEqual(result, rejected_result(["E_CLAIM_OUT_OF_DOMAIN"]))
        self.assertEqual(len(result), 20)
        for key in ("target", "asserted_claim", "boundary_ceiling", "boundary_grounding",
                    "recorder_relations", "counter_evidence", "inherited_limitations",
                    "evaluation_context", "evaluation_scope"):
            self.assertIsNone(result[key])

    def test_c10_counter_unresolved_blocks_supported_claim(self):
        d = fixture(I, ["intent"], counter_evidence=[counter("unresolved-material", [I])])
        self.check(d, expected(d, "downgrade", [I], [I], [(I, "equal")],
                               ["E_COUNTER_EVIDENCE_UNRESOLVED"], entries=[entry(I, "bd", "I")]))

    def test_c13_related_profile_gap_copied(self):
        g = gap("E_IV_NOT_EVALUATED", [E], "u1", "L-upstream")
        d = fixture(E, ["execution"], ceiling="execution", profile_evaluation_gaps=[g])
        self.check(d, expected(d, "accept", [E], [E], [(E, "equal")], gaps=[g],
                               limitations=[atom("L-upstream")], entries=[entry(E, "bd", "E")]))

    def test_c14_entry_scoped_counter_statuses(self):
        d = fixture(E, ["execution"], ceiling="execution",
                    counter_evidence=[counter("defeating", [I]), counter("not-evaluated", [E])])
        g = {"token": "E_COUNTER_EVIDENCE_NOT_EVALUATED", "target": "T", "evaluation_context_ref": "C",
             "affected_claims": [E], "basis_refs": [], "limitations": []}
        self.check(d, expected(d, "downgrade", [E], [E], [(E, "equal")], gaps=[g],
                               entries=[entry(E, "bd", "E")]))

    def test_c15_profile_reason_projected_with_core_token(self):
        c = counter("unresolved-material", [E], reasons=["P_COUNTER_FAIL"], basis_refs=[atom("p1")])
        d = fixture(E, ["execution"], ceiling="execution", counter_evidence=[c])
        result = expected(d, "downgrade", [E], [E], [(E, "equal")],
                          ["E_COUNTER_EVIDENCE_UNRESOLVED", "P_COUNTER_FAIL"],
                          entries=[entry(E, "bd", "E")])
        self.check(d, result)
        self.assertEqual(appraise(d, PROFILES)["counter_evidence"][0]["reasons"], ["P_COUNTER_FAIL"])

    def test_c16_unrelated_profile_gap_not_projected(self):
        g = gap("E_IV_NOT_EVALUATED", [N_V], "u2", "L-unrelated")
        d = fixture(E, ["execution"], ceiling="execution", profile_evaluation_gaps=[g])
        self.check(d, expected(d, "accept", [E], [E], [(E, "equal")], entries=[entry(E, "bd", "E")]))


class OrderedChecks(unittest.TestCase):
    """6.2 ordered rejection checks and their precedence."""

    def reject(self, data, *tokens, profiles=PROFILES):
        self.assertEqual(appraise(data, profiles), rejected_result(tokens))

    def test_check1_not_a_record_or_unreadable_version(self):
        for value in ([], "x", None, {}, {"semantics_version": 2}):
            self.reject(value, "E_MALFORMED_NORMALIZED_INPUT")

    def test_check2_version_precedes_member_rules(self):
        self.reject({"semantics_version": "wexp-core-1"}, "E_UNSUPPORTED_SEMANTICS_VERSION")
        self.reject(fixture(I, ["intent"], semantics_version="wexp-core-3", fatal_conditions=["X"]),
                    "E_UNSUPPORTED_SEMANTICS_VERSION")

    def test_check3_structural(self):
        base = fixture(I, ["intent"])
        cases = [
            fixture(I, ["intent"], extra_member=1),
            {k: v for k, v in base.items() if k != "recorder_relations"},
            fixture(I, ["intent"], target=7),
            fixture(claim("decision"), ["intent"]),
            fixture({"base": "intent", "qualifiers": ["IV", "IV"]}, ["intent"]),
            fixture(I, ["intent"], fatal_conditions=["lowercase"]),
            fixture(I, ["intent"], inherited_limitations=[["p", "x"], ["p", "x"]]),
            fixture(I, ["intent"], inherited_limitations=[["p"]]),
            fixture(I, [], base_findings=[finding("intent", target_binding="maybe")]),
            fixture(I, [], base_findings=[finding("intent", extra=1)]),
            fixture(I, ["intent"], evaluation_scope=[{"capability": "", "status": "evaluated"}]),
            fixture(I, ["intent"], evaluation_scope=[{"capability": [P, ""], "status": "evaluated"}]),
            fixture(I, ["intent"], boundary_finding=base["boundary_finding"] | {"ceiling_base": "x"}),
            fixture(I, ["intent"], counter_evidence=[counter("blocked", [I])]),
            fixture(I, ["intent"], profile_evaluation_gaps=[gap("E_IV_NOT_EVALUATED", "all", "u", "L")]),
            fixture(I, ["intent"], profile_evaluation_gaps=[
                gap("E_IV_NOT_EVALUATED", [I], "u", "L", current_scope_capability="target-binding")]),
        ]
        for data in cases:
            with self.subTest(data=data):
                self.reject(data, "E_MALFORMED_NORMALIZED_INPUT")

    def test_check4_cross_field(self):
        bf = fixture(I, ["intent"])["boundary_finding"]
        cases = [
            fixture(I, [], base_findings=[finding("intent"), finding("intent")]),
            fixture(I, ["intent"], base_findings=[finding("intent", target="T2")]),
            fixture(I, ["intent"], base_findings=[finding("intent", evaluation_context_ref="C2")]),
            fixture(I, ["intent"], boundary_finding=bf | {"target": "other"}),
            fixture(I, ["intent"], boundary_finding={k: v for k, v in bf.items() if k != "ceiling_base"}),
            fixture(I, ["intent"], boundary_finding=bf | {"grounding": "not-evaluated"}),
            fixture(I, ["intent"], boundary_finding=bf | {"status": "not-evaluated"}),
            fixture(I, ["intent"], counter_evidence=[]),
            fixture(I, ["intent"], counter_evidence=[counter("not-supplied", [I])]),
            fixture(I, ["intent"], counter_evidence=[counter("not-supplied", []), counter("defeating", [I])]),
            fixture(I, ["intent"], counter_evidence=[counter("defeating", [])]),
            fixture(I, ["intent"], counter_evidence=[counter("defeating", [claim("intent", "PROV")])]),
            fixture(I, ["intent"], counter_evidence=[counter("defeating", [I], reasons=["E_IV_NOT_EVALUATED"])]),
            fixture(I, ["intent"], counter_evidence=[counter("defeating", [I], reasons=["P_UNKNOWN"])]),
            fixture(I, ["intent"], quals=[("PROV", "intent")]),
            fixture(I, ["intent"], qualifier_findings=[qualifier("PROV", "execution", independence_validation="supported")]),
            fixture(I, ["intent"], qualifier_findings=[qualifier("IV", "intent", independence_validation="not-applicable")]),
            fixture(I, ["intent"], qualifier_findings=[qualifier("IV", "intent"), qualifier("IV", "intent")]),
            fixture(I, ["intent"], fatal_conditions=["E_CLAIM_OUT_OF_DOMAIN"]),
            fixture(I, ["intent"], fatal_conditions=["E_BASE_EXCEEDS_BOUNDARY"]),
            fixture(I, ["intent"], fatal_conditions=["P_COUNTER_FAIL"]),
            fixture(I, ["intent"], base_findings=[finding("intent", reasons=["E_INTEGRITY_INVALID"])]),
            fixture(I, ["intent"], base_findings=[finding("intent", basis_refs=[["other-profile", "I"]])]),
            fixture(I, ["intent"], inherited_limitations=[["other-profile", "L"]]),
            fixture(I, ["intent"], recorder_relations=[{"profile_identifier": P, "relation_token": "r",
                                                        "subject_ref": atom("a"), "object_ref": atom("b"),
                                                        "basis_refs": [], "limitations": []}]),
            fixture(I, ["intent"], profile_evaluation_gaps=[gap("E_IV_NOT_EVALUATED", [], "u", "L")]),
            fixture(I, ["intent"], profile_evaluation_gaps=[gap("E_BASE_EXCEEDS_BOUNDARY", [I], "u", "L")]),
            fixture(I, ["intent"], profile_evaluation_gaps=[gap("E_IV_NOT_EVALUATED", [I], "u", "L", target="X")]),
            fixture(I, ["intent"], profile_evaluation_gaps=[
                gap("E_IV_NOT_EVALUATED", [I], "u", "L", current_scope_capability="composition")]),
            scope(fixture(I, ["intent"]), carrier_mapping="not-evaluated"),
            scope(fixture(I, ["intent"]), composition="not-evaluated"),
            scope(fixture(I, ["intent"]), intent_support="not-evaluated"),
            scope(fixture(I, ["execution"], ceiling="execution"), intent_support="not-evaluated"),
            scope(fixture(I, [], base_findings=[finding("intent", semantic_validation="not-evaluated")]),
                  intent_support="evaluated"),
            scope(fixture(I, [], base_findings=[finding("intent", target_binding="not-evaluated")],
                          ), intent_support="not-evaluated"),  # target-binding still evaluated
            scope(fixture(E_V, ["execution"], ceiling="execution"), independent_verification="not-evaluated"),
            fixture(I, ["intent"], evaluation_scope=fixture(I)["evaluation_scope"] + [
                {"capability": "intent-support", "status": "evaluated"}]),
            fixture(I, ["intent"], evaluation_scope=fixture(I)["evaluation_scope"][1:]),
            fixture(I, ["intent"], evaluation_scope=fixture(I)["evaluation_scope"] + [
                {"capability": [P, "ext"], "status": "evaluated"}]),
        ]
        for data in cases:
            with self.subTest(data=data):
                self.reject(data, "E_PROFILE_MAPPING_INVALID")

    def test_marker_with_matching_capability_is_valid(self):
        g = gap("E_COMPOSITION_NOT_EVALUATED", [E], "u", "L", current_scope_capability="composition")
        d = scope(fixture(E, ["execution"], ceiling="execution", profile_evaluation_gaps=[g]),
                  composition="not-evaluated")
        result = appraise(d, PROFILES)
        self.assertEqual(result["verdict"], "accept")
        self.assertEqual(result["evaluation_gaps"], ["E_COMPOSITION_NOT_EVALUATED"])
        self.assertEqual(result["evaluation_gap_entries"][0]["current_scope_capability"], "composition")

    def test_extension_key_bound_through_catalog(self):
        profiles = copy.deepcopy(PROFILES)
        profiles[P]["scope_names"] = ["ext"]
        d = fixture(I, ["intent"], evaluation_scope=fixture(I)["evaluation_scope"] + [
            {"capability": [P, "ext"], "status": "not-evaluated"}])
        result = appraise(d, profiles)
        self.assertEqual(result["verdict"], "accept")
        self.assertIn({"capability": [P, "ext"], "status": "not-evaluated"}, result["evaluation_scope"])
        self.reject(d, "E_PROFILE_MAPPING_INVALID")  # same input, catalog without the name

    def test_check5_supplied_fatal_set_wins_over_check6(self):
        d = fixture(claim("intent", "PROV"), ["intent"],
                    fatal_conditions=["E_INTEGRITY_INVALID", "E_BINDING_MISMATCH"])
        self.reject(d, "E_BINDING_MISMATCH", "E_INTEGRITY_INVALID")

    def test_check4_wins_over_check5_and_check3_over_check4(self):
        self.reject(fixture(I, ["intent"], fatal_conditions=["E_INTEGRITY_INVALID"],
                            counter_evidence=[]), "E_PROFILE_MAPPING_INVALID")
        self.reject(fixture(I, ["intent"], fatal_conditions=["E_INTEGRITY_INVALID"],
                            counter_evidence=[], target=1), "E_MALFORMED_NORMALIZED_INPUT")

    def test_profile_token_resolution(self):
        d = fixture(I, ["intent"], counter_evidence=[counter("defeating", [I], reasons=["P_COUNTER_FAIL"])])
        self.assertEqual(appraise(d, PROFILES)["verdict"], "downgrade")
        self.reject(d, "E_PROFILE_MAPPING_INVALID", profiles={})  # identity absent from the catalog
        two = {P: PROFILES[P], "other": PROFILES[P]}
        d["evaluation_context"]["profile_identifiers"] = [P, "other"]
        self.reject(d, "E_PROFILE_MAPPING_INVALID", profiles=two)  # ambiguous resolution


class DiagnosticMatrix(unittest.TestCase):
    """8.6 rows not covered by the table, and 8.1 limitation handling."""

    def run_case(self, data):
        return appraise(data, PROFILES)

    def test_boundary_unsupported_preserves_grounding_and_withholds_ceiling(self):
        d = fixture(I, ["intent"])
        d["boundary_finding"] |= {"status": "unsupported", "limitations": [atom("L-b")],
                                  "reasons": ["E_EVIDENCE_COVERAGE_MISMATCH"]}
        r = self.run_case(d)
        self.assertEqual((r["verdict"], r["boundary_ceiling"], r["boundary_grounding"]),
                         ("downgrade", None, "attributed"))
        self.assertEqual(r["substantive_reasons"], ["E_BOUNDARY_NOT_SUPPORTED", "E_EVIDENCE_COVERAGE_MISMATCH"])
        self.assertEqual(r["supported_claims"], [])
        self.assertEqual(r["inherited_limitations"], [atom("L-b")])

    def test_boundary_not_evaluated_gap_entry(self):
        d = scope(fixture(I, ["intent"]), boundary_grounding="not-evaluated")
        d["boundary_finding"] |= {"status": "not-evaluated", "grounding": "not-evaluated"}
        r = self.run_case(d)
        self.assertEqual(r["evaluation_gaps"], ["E_BOUNDARY_NOT_EVALUATED"])
        self.assertEqual(r["evaluation_gap_entries"], [{
            "token": "E_BOUNDARY_NOT_EVALUATED", "target": "T", "evaluation_context_ref": "C",
            "affected_claims": [I], "basis_refs": [atom("bd")], "limitations": []}])
        self.assertEqual(r["boundary_grounding"], "not-evaluated")

    def test_boundary_binding_unsupported(self):
        d = fixture(I, ["intent"])
        d["boundary_finding"]["target_binding"] = "unsupported"
        self.assertEqual(self.run_case(d)["substantive_reasons"], ["E_EVIDENCE_NOT_BOUND"])

    def test_asserted_base_rows(self):
        d = fixture(I, [], base_findings=[finding("intent", target_binding="unsupported",
                                                  semantic_validation="unsupported",
                                                  limitations=[atom("L-i")])])
        r = self.run_case(d)
        self.assertEqual(r["substantive_reasons"], ["E_EVIDENCE_NOT_BOUND", "E_EXACT_CLAIM_NOT_SUPPORTED"])
        self.assertEqual(r["inherited_limitations"], [atom("L-i")])
        d = scope(fixture(I, [], base_findings=[finding("intent", semantic_validation="not-evaluated")]),
                  intent_support="not-evaluated")
        r = self.run_case(d)
        self.assertEqual((r["substantive_reasons"], r["evaluation_gaps"]), ([], ["E_BASE_NOT_EVALUATED"]))

    def test_unrelated_failed_finding_contributes_nothing(self):
        d = fixture(I, ["intent"], base_findings=[finding("intent"), finding(
            "execution", semantic_validation="unsupported", limitations=[atom("L-x")],
            reasons=["E_CHAIN_UNBOUND"])])
        r = self.run_case(d)
        self.assertEqual((r["verdict"], r["substantive_reasons"], r["inherited_limitations"]),
                         ("accept", [], []))

    def test_prov_rows(self):
        d = fixture(E_P, ["execution"], ceiling="execution")
        self.assertEqual(self.run_case(d)["substantive_reasons"], ["E_MISSING_REQUIRED_EVIDENCE"])
        d["qualifier_findings"] = [qualifier("PROV", "execution", semantic_validation="unsupported",
                                             target_binding="unsupported")]
        self.assertEqual(self.run_case(d)["substantive_reasons"], ["E_EVIDENCE_NOT_BOUND", "E_PROV_NOT_SUPPORTED"])
        d["qualifier_findings"] = [qualifier("PROV", "execution", semantic_validation="not-evaluated",
                                             target_binding="not-evaluated")]
        scope(d, provenance_support="not-evaluated", target_binding="not-evaluated")
        r = self.run_case(d)
        self.assertEqual((r["verdict"], r["evaluation_gaps"], len(r["evaluation_gap_entries"])),
                         ("downgrade", ["E_PROV_NOT_EVALUATED"], 1))
        self.assertEqual(r["supported_claims"], [E])

    def test_iv_rows(self):
        d = fixture(E_V, ["execution"], [("IV", "execution")], ceiling="execution")
        d["qualifier_findings"][0]["independence_validation"] = "unsupported"
        r = self.run_case(d)
        self.assertEqual(r["substantive_reasons"], ["E_INDEPENDENCE_NOT_ESTABLISHED"])
        self.assertEqual(r["supported_claims"], [E])
        d["qualifier_findings"][0] |= {"independence_validation": "not-evaluated",
                                       "semantic_validation": "unsupported"}
        scope(d, independent_verification="not-evaluated")
        r = self.run_case(d)
        self.assertEqual((r["substantive_reasons"], r["evaluation_gaps"]),
                         (["E_IV_NOT_SUPPORTED"], ["E_IV_NOT_EVALUATED"]))

    def test_full_qualifier_lattice_and_wl4_wl5_incomparability(self):
        d = fixture(E_PV, ["execution"], [("PROV", "execution"), ("IV", "execution")], ceiling="execution")
        r = self.run_case(d)
        self.assertEqual(r["supported_claims"], sorted([E, E_P, E_V, E_PV], key=ckey))
        self.assertEqual(r["maximal_supported_claims"], [E_PV])
        self.assertEqual(r["verdict"], "accept")
        d["asserted_claim"] = E_P
        r = self.run_case(d)
        self.assertEqual((r["verdict"], r["asserted_claim_supported"]), ("accept", True))
        self.assertEqual(r["support_relations"], [{"supported_claim": E_PV, "relation": "support-above-claim"}])

    def test_limitations_from_premises_and_related_entries(self):
        d = fixture(E, ["execution"], ceiling="execution",
                    inherited_limitations=[atom("L-in")],
                    counter_evidence=[counter("resolved-no-defeat", "all-admissible-claims",
                                              limitations=[atom("L-c")])])
        d["boundary_finding"]["limitations"] = [atom("L-boundary")]
        d["base_findings"][0]["limitations"] = [atom("L-boundary")]
        r = self.run_case(d)
        self.assertEqual(r["verdict"], "accept")
        self.assertEqual(r["support_entries"][0]["limitations"], [atom("L-boundary")])
        self.assertEqual(r["inherited_limitations"],
                         sorted([atom("L-boundary"), atom("L-c"), atom("L-in")]))

    def test_counter_all_admissible_claims_blocks(self):
        d = fixture(I, ["intent"], counter_evidence=[counter("defeating", "all-admissible-claims")])
        r = self.run_case(d)
        self.assertEqual((r["verdict"], r["substantive_reasons"]), ("downgrade", ["E_COUNTER_EVIDENCE_DEFEATING"]))

    def test_appraise_does_not_mutate_arguments(self):
        d = fixture(E_V, ["execution"], [("IV", "execution")], ceiling="execution",
                    profile_evaluation_gaps=[gap("E_IV_NOT_EVALUATED", [E], "u1", "L-upstream")])
        d["asserted_claim"]["qualifiers"] = ["IV"]
        before, profiles = copy.deepcopy(d), copy.deepcopy(PROFILES)
        appraise(d, profiles)
        self.assertEqual((d, profiles), (before, PROFILES))


class CommandLine(unittest.TestCase):
    def run_cli(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "in.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            return subprocess.run(
                [sys.executable, "-m", "wexp_check", "--input", path, "--profiles",
                 os.path.join(HANDOFF, "profiles.json")],
                cwd=OUT, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": OUT})

    def test_c01_via_command_line(self):
        with open(os.path.join(HANDOFF, "input", "C01.json"), encoding="utf-8") as fh:
            text = fh.read()
        proc = self.run_cli(text)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), canonical(appraise(json.loads(text), PROFILES)))
        self.assertEqual(proc.stdout, json.dumps(json.loads(proc.stdout), sort_keys=True) + "\n")
        self.assertEqual(list(json.loads(proc.stdout)), sorted(json.loads(proc.stdout)))

    def test_harness_errors_exit_2(self):
        for text in ('{"semantics_version": "wexp-core-2", "semantics_version": "x"}',
                     '{"target": NaN}', '{"target": 1e999}', '{"target": Infinity}', '{"a": }'):
            proc = self.run_cli(text)
            self.assertEqual(proc.returncode, 2, text)
            self.assertEqual(proc.stdout, "")
            self.assertEqual(json.loads(proc.stderr)["core_appraisal_produced"], False)

    def test_logically_malformed_is_a_core_rejection(self):
        proc = self.run_cli('{"semantics_version": "wexp-core-2"}')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout)["fatal_reasons"], ["E_MALFORMED_NORMALIZED_INPUT"])


if __name__ == "__main__":
    unittest.main()

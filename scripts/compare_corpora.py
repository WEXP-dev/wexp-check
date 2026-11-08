#!/usr/bin/env python3
"""Compare wexp_check and wexp_ref.core02 against frozen Core-02 corpora, component by component.

usage: python3 -B scripts/compare_corpora.py [--baseline <comparison.json>] <wexp-check root> <wexp-ref root> <output.json> <corpus.json> [<corpus.json> ...]

Each engine runs in its own interpreter process with only its own code on PYTHONPATH. Collections the
harness defines as sets are compared as sets; Booleans stay distinct from numbers; null from absence.
The script computes no expectation; it only compares saved expectations with observed results.

Exit status is 0 only if every case of every corpus has wexp_check equal to the saved expectation and to
wexp_ref, no engine raised or mutated its input, each corpus.json matches the case_count and
expanded_corpus_sha256 of the manifest.json beside it (when present), and, with --baseline, each set has
exactly the case identifiers and per-case results of that earlier comparison file. Every failure names
the set and, where one exists, the case."""
import json, subprocess, sys, hashlib, platform
from pathlib import Path
ARGS = sys.argv[1:]; BASELINE = None
if ARGS[:1] == ['--baseline']: BASELINE = json.loads(Path(ARGS[1]).read_bytes()); ARGS = ARGS[2:]
WC = Path(ARGS[0]).resolve(); WR = Path(ARGS[1]).resolve()/'src'; OUT = Path(ARGS[2]).resolve()
SETS = {}
for arg in ARGS[3:]:
    p = Path(arg).resolve(); SETS[json.loads(p.read_bytes())['id']] = p
SET_FIELDS = {'qualifiers','profile_identifiers','basis_refs','reasons','limitations','base_findings','qualifier_findings','recorder_relations','counter_evidence','evaluation_scope','profile_evaluation_gaps','inherited_limitations','fatal_conditions','affected_claims','fatal_reasons','substantive_reasons','evaluation_gaps','evaluation_gap_entries','supported_claims','maximal_supported_claims','support_entries','support_relations'}
def enc(v): return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(',',':'), allow_nan=False)
def logical(v, f=None):
    if type(v) is dict: return {k: logical(x,k) for k,x in v.items()}
    if type(v) is list:
        it=[logical(x) for x in v]; return sorted(it, key=enc) if f in SET_FIELDS else it
    return v
def same(a,b): return enc(logical(a)) == enc(logical(b))
DRIVER = r'''
import json, sys
corpus = json.load(open(sys.argv[2]))
mod = sys.argv[1]
if mod == 'wexp_check':
    from wexp_check import appraise
else:
    from wexp_ref.core02.appraiser import appraise
out = {}
for c in corpus['cases']:
    inp = json.loads(json.dumps(c['input'])); prof = json.loads(json.dumps(c.get('profiles', corpus['profiles'])))
    try:
        out[c['id']] = {'result': appraise(inp, prof), 'error': None}
    except Exception as e:
        out[c['id']] = {'result': None, 'error': type(e).__name__ + ': ' + str(e)[:300]}
    if json.dumps(inp, sort_keys=True) != json.dumps(c['input'], sort_keys=True): out[c['id']]['input_mutated'] = True
print(json.dumps(out, sort_keys=True))
'''
def run(module, path, corpus):
    r = subprocess.run([sys.executable, '-B', '-c', DRIVER, module, str(corpus)], env={'PYTHONPATH': str(path), 'PATH': '/usr/bin:/bin'}, capture_output=True, text=True)
    if r.returncode: raise SystemExit(module + ' driver failed: ' + r.stderr[-800:])
    return json.loads(r.stdout)
report = {'python': platform.python_version(), 'sets': {}}
FAIL = []
for sid, cpath in SETS.items():
    corpus = json.loads(cpath.read_bytes())
    man = cpath.parent/'manifest.json'
    if man.is_file():
        m = json.loads(man.read_bytes()); digest = hashlib.sha256(cpath.read_bytes()).hexdigest()
        if m.get('case_count') != len(corpus['cases']): FAIL.append(f"{sid}: {len(corpus['cases'])} cases, manifest case_count {m.get('case_count')}")
        if m.get('expanded_corpus_sha256') != digest: FAIL.append(f"{sid}: corpus.json sha256 {digest} differs from manifest expanded_corpus_sha256 {m.get('expanded_corpus_sha256')}")
    chk = run('wexp_check', WC, cpath); ref = run('wexp_ref', WR, cpath)
    rows = []; n_eq_exp = n_eq_ref = 0
    for c in corpus['cases']:
        cid = c['id']; o = chk[cid]['result']; rr = ref[cid]['result']; e = c['expected']
        eq_exp = o is not None and same(o, e); eq_ref = o is not None and rr is not None and same(o, rr)
        n_eq_exp += eq_exp; n_eq_ref += eq_ref
        row = {'id': cid, 'check_equals_expected': eq_exp, 'check_equals_ref': eq_ref, 'ref_equals_expected': rr is not None and same(rr, e), 'check_error': chk[cid]['error']}
        if chk[cid].get('input_mutated'): row['check_mutated_input'] = True
        if o is not None and not eq_exp:
            row['differing_components'] = sorted(k for k in e if not same({k: e[k]}, {k: o.get(k)}))
            row['detail'] = {k: {'expected': e[k], 'wexp_check': o.get(k)} for k in row['differing_components']}
        rows.append(row)
    report['sets'][sid] = {'corpus_sha256': hashlib.sha256(cpath.read_bytes()).hexdigest(), 'cases': len(rows), 'check_equals_expected': n_eq_exp, 'check_equals_ref': n_eq_ref, 'rows': rows}
    print(sid, f'wexp_check==expected {n_eq_exp}/{len(rows)}; wexp_check==wexp_ref {n_eq_ref}/{len(rows)}')
    for r in rows:
        if not r['check_equals_expected']: print('  ', r['id'], r.get('differing_components'), r['check_error'])
        bad = [k for k in ('check_equals_expected','check_equals_ref','ref_equals_expected') if not r[k]]
        if bad or r['check_error'] or r.get('check_mutated_input'): FAIL.append(f"{sid} case {r['id']}: " + ', '.join(bad + (['check_error'] if r['check_error'] else []) + (['check_mutated_input'] if r.get('check_mutated_input') else [])) + (f" (components {r['differing_components']})" if r.get('differing_components') else ''))
    if BASELINE is not None:
        base = BASELINE.get('sets', {}).get(sid)
        if base is None: FAIL.append(f'{sid}: not in the baseline')
        else:
            brow = {r['id']: r for r in base['rows']}; now = {r['id']: r for r in rows}
            for cid in sorted(brow.keys() - now.keys()): FAIL.append(f'{sid} case {cid}: in the baseline, missing from the corpus')
            for cid in sorted(now.keys() - brow.keys()): FAIL.append(f'{sid} case {cid}: in the corpus, not in the baseline')
            for cid in sorted(brow.keys() & now.keys()):
                diff = [k for k in ('check_equals_expected','check_equals_ref','ref_equals_expected') if brow[cid].get(k) != now[cid].get(k)]
                if diff: FAIL.append(f'{sid} case {cid}: differs from the baseline in ' + ', '.join(diff))
            if base.get('corpus_sha256') != report['sets'][sid]['corpus_sha256']: FAIL.append(f"{sid}: corpus sha256 {report['sets'][sid]['corpus_sha256']} differs from the baseline {base.get('corpus_sha256')}")
if BASELINE is not None:
    for sid in sorted(BASELINE.get('sets', {}).keys() - SETS.keys()): FAIL.append(f'{sid}: in the baseline, no corpus given')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')
if FAIL:
    for f in FAIL: print('FAIL', f)
    sys.exit(1)

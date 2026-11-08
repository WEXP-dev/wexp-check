#!/usr/bin/env python3
"""Compare wexp_check and wexp_ref.core02 against frozen Core-02 corpora, component by component.

usage: python3 -B scripts/compare_corpora.py <wexp-check root> <wexp-ref root> <output.json> <corpus.json> [<corpus.json> ...]

Each engine runs in its own interpreter process with only its own code on PYTHONPATH. Collections the
harness defines as sets are compared as sets; Booleans stay distinct from numbers; null from absence.
The script computes no expectation; it only compares saved expectations with observed results."""
import json, subprocess, sys, hashlib, platform
from pathlib import Path
WC = Path(sys.argv[1]).resolve(); WR = Path(sys.argv[2]).resolve()/'src'; OUT = Path(sys.argv[3]).resolve()
SETS = {}
for arg in sys.argv[4:]:
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
for sid, cpath in SETS.items():
    corpus = json.loads(cpath.read_bytes())
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
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')

"""E1 - Canonicalisation stability and quantisation ablation (Section 6.1, Tables 6-7).

Steps
  1. Root of the source IFC file (DK-C14N-1.1).
  2. T1: the source re-serialised with IfcOpenShell (open + write).
  3. T2: the source text with all instance numbers randomly reassigned, DATA lines
     shuffled and header / owner-history timestamps changed.
  4. Roots of T1 and T2 under DK-C14N-1.1.
  5. Ablation: number of elements whose canonical record differs between the source
     and T1 under four quantisation rules.

Writes out/e1_stability.json, out/ablation.json and out/tree_rev0.pkl (used by experiments.py).
Peak memory is roughly 6 GB for the 204 MB Snowdon Towers model; models are loaded one at a time.

Usage:  python e1_stability.py [path/to/model.ifc]
"""
import sys, os, re, time, json, pickle, random, hashlib, math, gc
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ifcopenshell
import dkcore

SRC = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    'DK_IFC', os.path.join(HERE, 'input', 'Snowdon_Towers_Sample_Architectural.ifc'))
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
T1 = os.path.join(OUT, 'T1_reserialised.ifc'); T2 = os.path.join(OUT, 'T2_renumbered_shuffled.ifc')

# quantisation rules of the ablation (Table 7); the last one is DK-C14N-1.1
RULES = [
    ('Fixed decimal grid, 1e-6 ft (DK-C14N-1.0)', dict(q=1e6, q_dir=1e6)),
    ('Binary grid, 2^-20 ft, no offset', dict(q=2.0 ** 20, q_dir=2.0 ** 20)),
    ('Binary grid, 2^-10 ft (directions 2^-20), no offset', dict(q=2.0 ** 10, q_dir=2.0 ** 20)),
    ('Binary grid, 2^-10 ft (directions 2^-20), offset 2 - sqrt(2) (DK-C14N-1.1)', None),
]
# The grids without offset use nearest-value rounding (Python round, ties to even), as in DK-C14N-1.0.
_orig_init = dkcore.Canon.__init__
_orig_val = dkcore.Canon.val


def use_rule(rule):
    """Switch dkcore to an ablation rule (None restores DK-C14N-1.1)."""
    if rule is None:
        dkcore.Canon.__init__ = _orig_init; dkcore.Canon.val = _orig_val; return

    def init(self, f, _r=rule):
        _orig_init(self, f); self.q = _r['q']; self.q_dir = _r['q_dir']; self._qcur = self.q

    def val(self, v, decl_is_set=False):
        if isinstance(v, float):
            return 'r' + str(round(v * self._qcur))
        return _orig_val(self, v, decl_is_set)
    dkcore.Canon.__init__ = init; dkcore.Canon.val = val


def leaves(tree):
    """All (GlobalId -> leaf digest) pairs of a tree."""
    out = {}

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == 'leaves':
                    out.update({g: (h.hex() if isinstance(h, bytes) else h) for g, h in v})
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(tree)
    return out


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for ch in iter(lambda: fh.read(1 << 20), b''): h.update(ch)
    return h.hexdigest()


_STR = re.compile(r"'(?:[^']|'')*'")


def make_t2(src, dst, seed=2026):
    """Renumber all instances, shuffle DATA lines and change timestamps at text level."""
    rnd = random.Random(seed)
    txt = open(src, encoding='utf-8', errors='surrogateescape').read()
    head, rest = txt.split('DATA;', 1); data, tail = rest.split('ENDSEC;', 1)
    recs = [r.strip() for r in re.split(r';\s*\n', data) if r.strip()]
    ids = [int(re.match(r'#(\d+)', r).group(1)) for r in recs]
    new = list(range(1, len(ids) + 1)); rnd.shuffle(new); m = dict(zip(ids, new))

    def renum(r):
        parts, pos = [], 0
        for s in _STR.finditer(r):                     # do not touch '#' inside string literals
            parts.append(re.sub(r'#(\d+)', lambda g: '#%d' % m[int(g.group(1))], r[pos:s.start()]))
            parts.append(s.group(0)); pos = s.end()
        parts.append(re.sub(r'#(\d+)', lambda g: '#%d' % m[int(g.group(1))], r[pos:]))
        r = ''.join(parts)
        if r.split('=', 1)[1].lstrip().startswith('IFCOWNERHISTORY'):   # change CreationDate etc.
            r = re.sub(r',(\d{9,10})\)$', lambda g: ',%d)' % (int(g.group(1)) + 86400), r)
        return r
    recs = [renum(r) for r in recs]; rnd.shuffle(recs)
    head = re.sub(r"FILE_NAME\(('(?:[^']|'')*'),'[^']*'", r"FILE_NAME(\1,'2030-01-01T00:00:00'", head, count=1)
    with open(dst, 'w', encoding='utf-8', errors='surrogateescape') as fh:
        fh.write(head + 'DATA;\n' + ';\n'.join(recs) + ';\nENDSEC;' + tail)


def tree_of(f, rule=None):
    use_rule(rule); t = time.time(); tr = dkcore.build_tree(f); dt = time.time() - t; use_rule(None)
    return tr, dt


R = {}
# ---- source
t = time.time(); f = ifcopenshell.open(SRC); t_load = time.time() - t
base, t_tree = tree_of(f)
pickle.dump(base, open(os.path.join(OUT, 'tree_rev0.pkl'), 'wb'))
R['base'] = dict(root=base['root'].hex(), file_sha=sha_file(SRC), t_load=t_load, t_tree=t_tree,
                 leaves=base['n_leaves'], size_mb=os.path.getsize(SRC) / 1e6, n_entities=len(list(f)))
print('BASE', R['base'], flush=True)
src_leaves = [leaves(tree_of(f, r)[0]) if r else leaves(base) for _, r in RULES]
f.write(T1); del f; gc.collect()
make_t2(SRC, T2)

# ---- variants
R['stability'] = [dict(name='Source file (Revit export)', file_sha=R['base']['file_sha'], root=R['base']['root'],
                       size=os.path.getsize(SRC))]
f1 = ifcopenshell.open(T1)
t1_leaves = [leaves(tree_of(f1, r)[0]) for _, r in RULES]
R['stability'].append(dict(name='T1: re-serialised with IfcOpenShell', file_sha=sha_file(T1),
                           root=dkcore.build_tree(f1)['root'].hex(), size=os.path.getsize(T1)))
del f1; gc.collect()
f2 = ifcopenshell.open(T2)
R['stability'].append(dict(name='T2: renumbered, shuffled, timestamps changed', file_sha=sha_file(T2),
                           root=dkcore.build_tree(f2)['root'].hex(), size=os.path.getsize(T2)))
del f2; gc.collect()
for s in R['stability']: print('STAB', s['name'], s['root'][:12], 'equal' if s['root'] == R['base']['root'] else 'DIFFERENT')

abl = []
for (name, _), a, b in zip(RULES, src_leaves, t1_leaves):
    n = sum(1 for g in a if a[g] != b.get(g)); abl.append(dict(rule=name, n=n)); print('ABL', n, name)
json.dump(R, open(os.path.join(OUT, 'e1_stability.json'), 'w'), indent=1)
json.dump(abl, open(os.path.join(OUT, 'ablation.json'), 'w'), indent=1)
print('DONE')

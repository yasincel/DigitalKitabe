"""E7 - Generalisation: stability across models and a third software, embedding, and controlled revisions.

For each model:
  source root (DK-C14N-1.1);
  T1  re-serialised with IfcOpenShell 0.8.4 (reformats real numbers);
  T2  instance numbers reassigned, DATA lines shuffled, timestamps changed (text level);
  T3  re-serialised with web-ifc 0.0.81 (independent C++ STEP parser and writer);
  E   identity embedded with the Digital Kitabe tool (Pset + non-physical emblem);
  and, for comparison, the number of elements whose canonical record differs between source and T1
  under fixed decimal rounding (DK-C14N-1.0).
For the main model (Schependomlaan) three controlled revisions test change localisation.

Usage: python e7_generalisation.py OUTDIR MODEL.ifc [MODEL.ifc ...]
Environment: DK_PAPER (folder with dkcore.py), DK_TOOL (folder with dkitabe.py), WEBIFC (dk-roundtrip binary).
"""
import sys, os, re, gc, json, time, random, hashlib, subprocess, glob, shutil
PAPER = os.environ.get('DK_PAPER', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'paper'))
TOOL = os.environ.get('DK_TOOL', os.path.join(PAPER, '..', 'tool'))
WEBIFC = os.environ.get('WEBIFC', 'dk-roundtrip')
sys.path.insert(0, PAPER)
import ifcopenshell
import dkcore

OUT = sys.argv[1]; MODELS = sys.argv[2:]
os.makedirs(OUT, exist_ok=True)

_STR = re.compile(r"'(?:[^']|'')*'")


def make_t2(src, dst, seed=2026):
    rnd = random.Random(seed)
    txt = open(src, encoding='utf-8', errors='surrogateescape').read()
    head, rest = txt.split('DATA;', 1); data, tail = rest.split('ENDSEC;', 1)
    recs = [r.strip() for r in re.split(r';\s*\n', data) if r.strip()]
    ids = [int(re.match(r'#(\d+)', r).group(1)) for r in recs]
    new = list(range(1, len(ids) + 1)); rnd.shuffle(new); m = dict(zip(ids, new))

    def renum(r):
        parts, pos = [], 0
        for s in _STR.finditer(r):
            parts.append(re.sub(r'#(\d+)', lambda g: '#%d' % m[int(g.group(1))], r[pos:s.start()]))
            parts.append(s.group(0)); pos = s.end()
        parts.append(re.sub(r'#(\d+)', lambda g: '#%d' % m[int(g.group(1))], r[pos:]))
        r = ''.join(parts)
        if r.split('=', 1)[1].lstrip().startswith('IFCOWNERHISTORY'):
            r = re.sub(r',(\d{9,10})\)$', lambda g: ',%d)' % (int(g.group(1)) + 86400), r)
        return r
    recs = [renum(r) for r in recs]; rnd.shuffle(recs)
    head = re.sub(r"FILE_NAME\(('(?:[^']|'')*'),'[^']*'", r"FILE_NAME(\1,'2030-01-01T00:00:00'", head, count=1)
    with open(dst, 'w', encoding='utf-8', errors='surrogateescape') as fh:
        fh.write(head + 'DATA;\n' + ';\n'.join(recs) + ';\nENDSEC;' + tail)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for ch in iter(lambda: fh.read(1 << 20), b''): h.update(ch)
    return h.hexdigest()


def leaves(tree):
    out = {}

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == 'leaves': out.update({g: h for g, h in v})
                else: walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(tree); return out


_init, _val = dkcore.Canon.__init__, dkcore.Canon.val


def tree_c10(f):
    """Tree under fixed decimal rounding (DK-C14N-1.0, 1e-6 in file units, ties to even)."""
    def init(self, f):
        _init(self, f); self.q = 1e6; self.q_dir = 1e6; self._qcur = 1e6

    def val(self, v, decl_is_set=False):
        if isinstance(v, float): return 'r' + str(round(v * self._qcur))
        return _val(self, v, decl_is_set)
    dkcore.Canon.__init__, dkcore.Canon.val = init, val
    try: return dkcore.build_tree(f)
    finally: dkcore.Canon.__init__, dkcore.Canon.val = _init, _val


def open_tree(path, c10=False):
    f = ifcopenshell.open(path)
    t = time.time(); tr = dkcore.build_tree(f); dt = time.time() - t
    t10 = tree_c10(f) if c10 else None
    info = dict(schema=f.schema, entities=len(list(f)), storeys=len(tr['storeys']), elements=tr['n_leaves'])
    return f, tr, dt, t10, info


R = {}
for path in MODELS:
    name = os.path.splitext(os.path.basename(path))[0]
    w = os.path.join(OUT, name); os.makedirs(w, exist_ok=True)
    f, base, t_tree, base10, info = open_tree(path, c10=True)
    app = f.by_type('IfcApplication')
    unit = [u for ua in f.by_type('IfcUnitAssignment') for u in ua.Units if getattr(u, 'UnitType', None) == 'LENGTHUNIT']
    r = dict(file=os.path.basename(path), size_mb=os.path.getsize(path) / 1e6, sha=sha(path), root=base['root'].hex(),
             t_tree=t_tree, app=(app[0].ApplicationFullName + ' ' + app[0].Version) if app else '',
             unit=(unit[0].Prefix or '') + ' ' + (unit[0].Name if unit and unit[0].is_a('IfcSIUnit') else (unit[0].Name if unit else '')),
             **info)
    t1 = os.path.join(w, 'T1_ifcopenshell.ifc'); f.write(t1)
    del f; gc.collect()
    t2 = os.path.join(w, 'T2_renumbered.ifc'); make_t2(path, t2)
    t3 = os.path.join(w, 'T3_webifc.ifc')
    subprocess.run([WEBIFC, path, t3], check=True, capture_output=True)
    var = {}
    for key, p in (('T1', t1), ('T2', t2), ('T3', t3)):
        g, tr, dt, t10, _ = open_tree(p, c10=(key in ('T1', 'T3')))
        d = dict(root_equal=tr['root'] == base['root'], file_sha_equal=sha(p) == r['sha'], t_tree=dt)
        if t10 is not None:
            a, b = leaves(base10), leaves(t10)
            d['c10_elements_differing'] = sum(1 for k in a if a[k] != b.get(k))
        var[key] = d; del g, tr, t10; gc.collect()
    # embedding with the tool
    td = os.path.join(w, 'stamp'); shutil.rmtree(td, ignore_errors=True)
    cp = subprocess.run([sys.executable, os.path.join(TOOL, 'dkitabe.py'), 'stamp', path, '--out', td, '--note', 'E7'],
                        capture_output=True, text=True)
    emb = glob.glob(os.path.join(td, '*_with_kitabe.ifc'))
    if emb:
        g, tr, dt, _, _ = open_tree(emb[0])
        var['E'] = dict(root_equal=tr['root'] == base['root'], file_sha_equal=False, t_tree=dt,
                        dk_objects=len([a for a in g.by_type('IfcAnnotation') if (a.Name or '').startswith('DigitalKitabe')]))
        del g, tr; gc.collect()
    else:
        var['E'] = dict(error=cp.stderr[-400:])
    r['variants'] = var
    for k in (t1, t2, t3): os.remove(k)
    R[name] = r
    print('MODEL', name, json.dumps({k: (v if k != 'variants' else {kk: vv.get('root_equal') for kk, vv in v.items()}) for k, v in r.items() if k != 'sha'}), flush=True)
    del base, base10; gc.collect()
json.dump(R, open(os.path.join(OUT, 'e7_stability.json'), 'w'), indent=1)
print('DONE')

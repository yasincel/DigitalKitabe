"""E11 - Pattern encoding DK-ENC-1.1 versus DK-ENC-1.0 on the Snowdon Towers trees in results/.

Reproduces the rule-conformity check (1,000 patterns from random digests), the channel capacity, the share of the
drawing that stays in place after one storey is inserted, the visible changes of the controlled revisions and the
single-element change proxies. Needs only the Merkle trees in results/merkle_tree_rev*.json (no IFC file).

Usage: python e11_encoding.py [OUTDIR]
"""
import sys, os, json, copy, random, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import dkpattern as dp

RES = os.path.join(HERE, 'results'); OUT = sys.argv[1] if len(sys.argv) > 1 else RES
os.makedirs(OUT, exist_ok=True)
GEN = {'DK-ENC-1.0': dp.rosette_v10, 'DK-ENC-1.1': dp.rosette}
CENTRE = {'DK-ENC-1.0': 8, 'DK-ENC-1.1': 12}


load_tree = dp.load_tree_json


T = [load_tree(os.path.join(RES, f'merkle_tree_rev{k}.json')) for k in range(5)]
base = T[0]; N = len(base['storeys']); codes = list(base['storeys'][0]['disc'].keys())
rnd = random.Random(11)
rb = lambda: bytes(rnd.getrandbits(8) for _ in range(32))


def randomise(tr):
    tr = copy.deepcopy(tr)
    tr['root'] = rb(); tr['nonspatial'] = rb()
    for s in tr['storeys']:
        s['hash'] = rb()
        for d in codes: s['disc'][d]['hash'] = rb()
    return tr


def skeleton(P):   # region layout: geometry of the non-data background polygons
    return tuple((p['region'].split(':')[0], tuple((round(x, 5), round(y, 5)) for x, y in p['poly']))
                 for p in P if p['z'] <= 1 and p['region'] != 'frame' and not p['region'].startswith('disc'))


def cells(P):
    return {(p['fill'], tuple((round(x, 5), round(y, 5)) for x, y in p['poly'])) for p in P}


def storey_orders(P):
    return {p['order'] for p in P if p['region'].startswith('storey') and p['order']}


R = {}
for ver, gen in GEN.items():
    sk0 = skeleton(gen(base)); same_sk = in_pal = compat = 0; orders = set()
    for _ in range(1000):
        P = gen(randomise(base))
        same_sk += skeleton(P) == sk0
        in_pal += all(p['fill'] in dp.PALETTE + [dp.PAPER, dp.EMPTY] for p in P)
        o = storey_orders(P); orders |= o
        compat += all(CENTRE[ver] % k == 0 for k in o)
    sectors = dp.n_sectors(N) if ver == 'DK-ENC-1.1' else N
    # insertion of one storey at each interior position
    keep = []
    for pos in range(1, N):
        tr = copy.deepcopy(base); new = copy.deepcopy(base['storeys'][pos])
        new['hash'] = rb()
        for d in codes: new['disc'][d]['hash'] = rb()
        tr['storeys'].insert(pos, new); tr['root'] = rb(); tr['spatial'] = rb()
        a, b = gen(base), gen(tr)
        ca, cb = cells(a), cells(b)
        keep.append(len(ca & cb) / len(ca))
    R[ver] = dict(patterns=1000, skeleton_identical=same_sk, palette_ok=in_pal, storey_motifs_compatible=compat,
                  storey_motif_orders=sorted(orders), centre_order=CENTRE[ver], storey_sectors=sectors,
                  sectors_multiple_of_centre=sectors % CENTRE[ver] == 0,
                  insertion_unchanged_mean=float(np.mean(keep)), insertion_unchanged_min=float(np.min(keep)),
                  insertion_unchanged_max=float(np.max(keep)), insertion_positions=len(keep),
                  capacity=(dp.capacity_A(base) if ver == 'DK-ENC-1.1' else dp.capacity_A_v10(base)))
    print(ver, {k: v for k, v in R[ver].items()})


# visible changes of the controlled revisions (DK-ENC-1.1)
def changed(Pa, Pb):
    sa, sb = dp.region_signature(Pa), dp.region_signature(Pb)
    return sorted(k for k in sa if sa[k] != sb.get(k))


Ps = [dp.rosette(t) for t in T]
R['revisions_DK-ENC-1.1'] = {f'Rev{k}': changed(Ps[k - 1], Ps[k]) for k in range(1, 5)}
print(R['revisions_DK-ENC-1.1'])

# single-element change proxies (DK-ENC-1.1), same seed and draw order as simulate.py
rnd = random.Random(7)
sig0 = dp.region_signature(dp.rosette(base))
nonempty = [(i, d) for i, s in enumerate(base['storeys']) for d in codes if s['disc'][d]['n']]
hr = hs = hd = 0; n = 400
for _ in range(n):
    i, d = rnd.choice(nonempty)
    tr = copy.deepcopy(base); s = tr['storeys'][i]
    s['disc'][d]['hash'] = rb(); s['hash'] = rb(); tr['root'] = rb(); tr['spatial'] = rb()
    sig = dp.region_signature(dp.rosette(tr)); ch = {k for k in sig if sig[k] != sig0.get(k)}
    hr += 'root' in ch; hs += f'storey:{i}' in ch; hd += f'disc:{i}:{d}' in ch
R['single_change_DK-ENC-1.1'] = dict(trials=n, root=hr / n, storey=hs / n, cell=hd / n)
print(R['single_change_DK-ENC-1.1'])
json.dump(R, open(os.path.join(OUT, 'e11_encoding.json'), 'w'), indent=1)

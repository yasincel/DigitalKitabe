"""Algısal ayırt edilebilirlik için hesaplamalı vekil ölçümler (kullanıcı deneyinin yerini tutmaz)."""
import sys, pickle, os, copy, json, random
import os as _os; HERE = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import dkpattern as dp

base = pickle.load(open(sys.argv[1], 'rb'))
rnd = random.Random(7)
rb = lambda: bytes(rnd.getrandbits(8) for _ in range(32))
codes = list(base['storeys'][0]['disc'].keys())

def visual_regions(tr, fam):
    P = dp.rosette(tr) if fam == 'A' else dp.hexlattice(tr)
    return dp.region_signature(P)

res = {}
for fam in ['A', 'B']:
    sig0 = visual_regions(base, fam)
    # 1) tek eleman değişikliği: rastgele dolu (kat, disiplin) düğümünde yaprak değişir
    nonempty = [(i, d) for i, s in enumerate(base['storeys']) for d in codes if s['disc'][d]['n']]
    hit_storey = hit_disc = hit_root = 0; false_regions = 0; nreg = []
    T = 400
    for _ in range(T):
        i, d = rnd.choice(nonempty)
        tr = copy.copy(base); tr['storeys'] = [dict(s) for s in base['storeys']]
        s = tr['storeys'][i]; s['disc'] = dict(s['disc']); s['disc'][d] = dict(s['disc'][d], hash=rb())
        s['hash'] = rb(); tr['root'] = rb(); tr['spatial'] = rb()
        sig = visual_regions(tr, fam)
        ch = {k for k in sig if sig[k] != sig0.get(k)}
        hit_root += 'root' in ch; hit_storey += f'storey:{i}' in ch; hit_disc += f'disc:{i}:{d}' in ch
        false_regions += len(ch - {'root', f'storey:{i}', f'disc:{i}:{d}'})
        nreg.append(len(ch))
    res[fam] = dict(trials=T, root_visible=hit_root / T, storey_visible=hit_storey / T, disc_visible=hit_disc / T,
                    false_regions=false_regions, regions_total=len(sig0), mean_changed=float(np.mean(nreg)))
    # 2) rastgele iki model: farklı bölge oranı
    fr = []
    for _ in range(150):
        tr = copy.deepcopy(base)
        for s in tr['storeys']:
            s['hash'] = rb()
            for d in codes: s['disc'][d]['hash'] = rb()
        tr['root'] = rb(); tr['nonspatial'] = rb()
        sig = visual_regions(tr, fam)
        fr.append(sum(sig[k] != sig0[k] for k in sig0) / len(sig0))
    res[fam]['random_pair_diff_mean'] = float(np.mean(fr)); res[fam]['random_pair_diff_min'] = float(np.min(fr))
    res[fam]['random_pair_fracs'] = fr
    print(fam, {k: v for k, v in res[fam].items() if k != 'random_pair_fracs'})
json.dump(res, open(sys.argv[2], 'w'), indent=1)

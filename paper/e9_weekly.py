"""E9 - Real revision sequence: weekly 'as planned' exports of the Schependomlaan model (ArchiCAD, IFC2X3).

For consecutive weeks, the Merkle trees are compared: elements added, deleted, changed and unchanged
(by GlobalId and leaf digest), storey and discipline nodes changed, and whether the root changed.

Usage: python e9_weekly.py OUTDIR WEEK1.ifc WEEK2.ifc ...   (in chronological order)
"""
import sys, os, json, gc, time, collections
PAPER = os.environ.get('DK_PAPER', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PAPER)
import ifcopenshell
import dkcore

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)


def summary(path):
    f = ifcopenshell.open(path)
    t = time.time(); tr = dkcore.build_tree(f); dt = time.time() - t
    leaves = {}
    for s in tr['storeys']:
        for d, node in s['disc'].items():
            for g, h in node['leaves']:
                leaves[g] = (s['name'], d, h.hex() if isinstance(h, bytes) else h)
    nodes = {(s['name'], d): (node['hash'].hex() if isinstance(node['hash'], bytes) else node['hash'])
             for s in tr['storeys'] for d, node in s['disc'].items()}
    st = {s['name']: (s['hash'].hex() if isinstance(s['hash'], bytes) else s['hash']) for s in tr['storeys']}
    classes = collections.Counter(p.is_a() for p in f.by_type('IfcProduct'))
    try: hdr = f.header.file_name.time_stamp
    except Exception: hdr = ''
    r = dict(file=os.path.basename(path), size_mb=os.path.getsize(path) / 1e6, root=tr['root'].hex(), t_tree=dt,
             elements=tr['n_leaves'], storeys=len(tr['storeys']), nonspatial=tr['nonspatial'].hex(),
             bld_level=tr['n_bld_level'], timestamp=str(hdr), top_classes=classes.most_common(6))
    del f, tr; gc.collect()
    return r, leaves, nodes, st


prev = None; R = {'weeks': [], 'pairs': []}
for path in sys.argv[2:]:
    r, leaves, nodes, st = summary(path)
    R['weeks'].append(r); print('WEEK', json.dumps({k: r[k] for k in ('file', 'elements', 'storeys', 'root', 't_tree')}), flush=True)
    if prev:
        pr, pl, pn, ps = prev
        common = set(pl) & set(leaves)
        changed = [g for g in common if pl[g][2] != leaves[g][2]]
        moved = [g for g in common if pl[g][:2] != leaves[g][:2]]
        added = set(leaves) - set(pl); deleted = set(pl) - set(leaves)
        touched = set(changed) | added | deleted
        exp_nodes = {leaves[g][:2] for g in set(changed) | added} | {pl[g][:2] for g in set(changed) | deleted}
        nodes_changed = {k for k in set(pn) | set(nodes) if pn.get(k) != nodes.get(k)}
        pair = dict(a=pr['file'], b=r['file'], root_changed=pr['root'] != r['root'],
                    added=len(added), deleted=len(deleted), changed=len(changed), unchanged=len(common) - len(changed),
                    moved_between_nodes=len(moved),
                    storeys_changed=sum(1 for k in set(ps) | set(st) if ps.get(k) != st.get(k)), storeys_total=len(st),
                    disc_nodes_changed=len(nodes_changed), disc_nodes_total=len(set(pn) | set(nodes)),
                    disc_nodes_explained=len(nodes_changed - exp_nodes) == 0,
                    nonspatial_changed=pr['nonspatial'] != r['nonspatial'],
                    changed_by_discipline=collections.Counter(leaves[g][1] for g in changed).most_common(),
                    added_by_storey=collections.Counter(leaves[g][0] for g in added).most_common())
        R['pairs'].append(pair); print('PAIR', json.dumps(pair), flush=True)
    prev = (r, leaves, nodes, st)
json.dump(R, open(os.path.join(OUT, 'e9_weekly.json'), 'w'), indent=1, default=str)
print('DONE')

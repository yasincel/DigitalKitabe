"""E8 - Controlled revisions on a second model (Schependomlaan, ArchiCAD 18, IFC2X3, millimetres).

Four cumulative revisions, each followed by a new tree and a branch comparison with the previous one:
  Rev1 storey 01: a door moved by 500 mm;  Rev2 storey 02: a wall property changed;
  Rev3 storey 03: a railing deleted;       Rev4 a door style renamed (type level, non-spatial branch).
Elements are chosen deterministically (sorted by GlobalId).

Usage: python e8_revisions.py OUTDIR schependomlaan.ifc
"""
import sys, os, json, time, gc, pickle
PAPER = os.environ.get('DK_PAPER', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'paper'))
sys.path.insert(0, PAPER)
import ifcopenshell
import dkcore, dkpattern as dp

OUT, SRC = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
f = ifcopenshell.open(SRC)
st = {s.Name: s for s in f.by_type('IfcBuildingStorey')}


def contained(sname, cls):
    return sorted([e for r in st[sname].ContainsElements for e in r.RelatedElements if e.is_a(cls)], key=lambda e: e.GlobalId)


def rev1(f):
    d = contained('01 eerste verdieping', 'IfcDoor')[0]
    a = d.ObjectPlacement.RelativePlacement
    c = list(a.Location.Coordinates); c[0] += 500.0
    d.ObjectPlacement.RelativePlacement = f.create_entity(
        'IfcAxis2Placement3D', Location=f.create_entity('IfcCartesianPoint', Coordinates=tuple(c)),
        Axis=a.Axis, RefDirection=a.RefDirection)
    return 'Storey 01: door moved by 500 mm', d.GlobalId


def rev2(f):
    for w in contained('02 tweede verdieping', 'IfcWallStandardCase') + contained('02 tweede verdieping', 'IfcWall'):
        for r in w.IsDefinedBy:
            if r.is_a('IfcRelDefinesByProperties') and len(r.RelatedObjects) == 1:
                ps = r.RelatingPropertyDefinition
                if ps.is_a('IfcPropertySet') and ps.Name == 'Pset_WallCommon':
                    props = list(ps.HasProperties)
                    for i, p in enumerate(props):
                        if p.is_a('IfcPropertySingleValue') and p.Name == 'IsExternal' and p.NominalValue is not None:
                            old = p.NominalValue.wrappedValue
                            props[i] = f.create_entity('IfcPropertySingleValue', Name='IsExternal',
                                                       NominalValue=f.create_entity('IfcBoolean', not old))
                            ps.HasProperties = props
                            return f'Storey 02: wall property IsExternal {old} -> {not old}', w.GlobalId
    raise SystemExit('rev2: no suitable wall')


def rev3(f):
    e = contained('03 derde verdieping', 'IfcRailing')[0]
    gid = e.GlobalId
    for r in e.ContainedInStructure:
        r.RelatedElements = [x for x in r.RelatedElements if x != e]
    for r in list(e.IsDefinedBy):
        if len(r.RelatedObjects) == 1: f.remove(r)
        else: r.RelatedObjects = [x for x in r.RelatedObjects if x != e]
    f.remove(e)
    return 'Storey 03: railing deleted', gid


def rev4(f):
    t = sorted(f.by_type('IfcDoorStyle'), key=lambda x: x.GlobalId)[0]
    old = t.Name; t.Name = (old or '') + ' (rev)'
    return f'Door style renamed (type level)', t.GlobalId


R = {}
t0 = time.time(); prev = dkcore.build_tree(f); R['t_tree'] = time.time() - t0
R['root0'] = prev['root'].hex()
dp.to_svg(dp.rosette(prev), f'{OUT}/schependomlaan_rev0.svg')
pickle.dump(prev, open(f'{OUT}/tree_rev0.pkl', 'wb'))
cr = dkcore.chain_root(prev['root'], None, 0)
revs = []
for k, fn in enumerate([rev1, rev2, rev3, rev4], start=1):
    note, gid = fn(f)
    tr = dkcore.build_tree(f)
    d = dkcore.diff(prev, tr)
    ns = tr['nonspatial'] != prev['nonspatial']
    cr = dkcore.chain_root(tr['root'], cr, k)
    n_storeys = len(d); n_disc = sum(len(x[1]) for x in d); n_leaves = sum(len(x[2]) for x in d)
    revs.append(dict(rev=k, note=note, gid=gid, root=tr['root'].hex(), chain_root=cr.hex(),
                     storeys_changed=[x[0] for x in d], disciplines_changed=[x[1] for x in d],
                     leaves_changed=[c for x in d for c in x[2]], nonspatial_changed=ns,
                     n_storeys=n_storeys, n_disc=n_disc, n_leaves=n_leaves,
                     target_found=any(c[1] == gid for x in d for c in x[2]) or (ns and n_storeys == 0)))
    print('REV', k, note, d, 'nonspatial', ns, flush=True)
    dp.to_svg(dp.rosette(tr), f'{OUT}/schependomlaan_rev{k}.svg')
    pickle.dump(tr, open(f'{OUT}/tree_rev{k}.pkl', 'wb'))
    prev = tr; gc.collect()
R['revisions'] = revs
json.dump(R, open(f'{OUT}/e8_revisions.json', 'w'), ensure_ascii=False, indent=1, default=str)
print('DONE')

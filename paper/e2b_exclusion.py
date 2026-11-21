"""E2b - Exclusion rule (v): embedding test and two disguised changes, under the name-based rule of the first
prototype and under the structural rule of DK-C14N-1.1.

For each model:
  EMB  the identity is embedded with the prototype (Pset_DigitalKitabe on IfcProject/IfcBuilding, emblem annotation);
  A1   a copy of an existing wall is added under the name 'DigitalKitabe-Wall' (a real physical change);
  A2   a property set named Pset_DigitalKitabe with a fire rating is attached to an existing wall.
The binding check must keep the root for EMB and must change it for A1 and A2.

Usage: python e2b_exclusion.py OUTDIR MODEL.ifc [MODEL.ifc ...]
"""
import sys, os, json, gc, glob, shutil, subprocess
PAPER = os.environ.get('DK_PAPER', os.path.dirname(os.path.abspath(__file__)))
TOOL = os.environ.get('DK_TOOL', os.path.join(PAPER, '..', 'tool'))
sys.path.insert(0, PAPER)
import ifcopenshell, ifcopenshell.guid
import dkcore

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
STRUCT = dkcore.is_dk


def root(f, rule):
    dkcore.is_dk = rule
    try: return dkcore.build_tree(f)['root'].hex()
    finally: dkcore.is_dk = STRUCT


def walls(f):
    return sorted([w for w in f.by_type('IfcWall') if w.Representation is not None and w.ObjectPlacement is not None],
                  key=lambda w: w.GlobalId)


def attack_copy(f):
    w = walls(f)[0]
    st = [r.RelatingStructure for r in w.ContainedInStructure]
    n = f.create_entity(w.is_a(), GlobalId=ifcopenshell.guid.new(), OwnerHistory=w.OwnerHistory, Name='DigitalKitabe-Wall',
                        ObjectPlacement=w.ObjectPlacement, Representation=w.Representation)
    if st:
        f.create_entity('IfcRelContainedInSpatialStructure', GlobalId=ifcopenshell.guid.new(), OwnerHistory=w.OwnerHistory,
                        RelatedElements=[n], RelatingStructure=st[0])


def attack_pset(f):
    w = walls(f)[1]
    oh = w.OwnerHistory
    p = f.create_entity('IfcPropertySingleValue', Name='FireRating', NominalValue=f.create_entity('IfcLabel', 'REI 30'))
    ps = f.create_entity('IfcPropertySet', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh, Name=dkcore.DK_PSET, HasProperties=[p])
    f.create_entity('IfcRelDefinesByProperties', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                    RelatedObjects=[w], RelatingPropertyDefinition=ps)


R = {}
for path in sys.argv[2:]:
    name = os.path.splitext(os.path.basename(path))[0]
    f = ifcopenshell.open(path)
    r0 = {'name': root(f, dkcore.is_dk_by_name), 'structural': root(f, STRUCT)}
    res = {'source_root_equal_under_both_rules': r0['name'] == r0['structural']}
    # embedding with the tool
    td = os.path.join(OUT, name + '_stamp'); shutil.rmtree(td, ignore_errors=True)
    subprocess.run([sys.executable, os.path.join(TOOL, 'dkitabe.py'), 'stamp', path, '--out', td, '--note', 'E2b'],
                   capture_output=True, text=True)
    g = ifcopenshell.open(glob.glob(os.path.join(td, '*_with_kitabe.ifc'))[0])
    res['EMB'] = {k: root(g, rule) == r0[k] for k, rule in (('name', dkcore.is_dk_by_name), ('structural', STRUCT))}
    del g; gc.collect(); shutil.rmtree(td, ignore_errors=True)
    for key, fn in (('A1_disguised_wall', attack_copy), ('A2_disguised_pset', attack_pset)):
        h = ifcopenshell.open(path); fn(h)
        res[key] = {k: root(h, rule) != r0[k] for k, rule in (('name', dkcore.is_dk_by_name), ('structural', STRUCT))}
        del h; gc.collect()
    R[name] = res
    print(name, json.dumps(res), flush=True)
    del f; gc.collect()
json.dump(R, open(os.path.join(OUT, 'e2b_exclusion.json'), 'w'), indent=1)
print('DONE')

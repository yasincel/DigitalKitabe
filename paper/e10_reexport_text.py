"""E10 - Two exports of the same unchanged Revit model (separate sessions), compared at text level.

Reports which records differ, whether the differences are explained entirely by regenerated GlobalIds,
and which elements and storeys are affected through the type relations of the regenerated objects.
Usage: python e10_reexport_text.py A.ifc B.ifc OUT.json
"""
import re, sys, json, collections
A, B, OUT = sys.argv[1:4]
REC = re.compile(r'^#(\d+)=([A-Z0-9]+)\((.*)\);\s*$')

def load(p):
    d = {}
    with open(p, encoding='utf-8', errors='surrogateescape') as fh:
        for line in fh:
            m = REC.match(line)
            if m: d[int(m.group(1))] = (m.group(2), m.group(3))
    return d

a = load(A); b = load(B)
diff = [k for k in a if b.get(k) != a[k]]
only = (set(a) ^ set(b))
gid = re.compile(r"^'([0-9A-Za-z_$]{22})'")
explained = 0; types = collections.Counter(); regen = {}
for k in diff:
    ta, xa = a[k]; tb, xb = b.get(k, (None, ''))
    ga, gb = gid.match(xa), gid.match(xb)
    if ta == tb and ga and gb and xa[24:] == xb[24:]:
        explained += 1; regen[k] = ta
    types[ta] += 1
# elements related to regenerated type objects
rel_objs = []
for k, (t, x) in a.items():
    if t == 'IFCRELDEFINESBYTYPE':
        refs = [int(r) for r in re.findall(r'#(\d+)', x)]
        if refs and refs[-1] in regen and a[refs[-1]][0] != 'IFCRELDEFINESBYTYPE':
            rel_objs += refs[1:-1]
storey_of = {}
storeys = {k: re.findall(r"'([^']*)'", x)[1] if len(re.findall(r"'([^']*)'", x)) > 1 else str(k) for k, (t, x) in a.items() if t == 'IFCBUILDINGSTOREY'}
for k, (t, x) in a.items():
    if t == 'IFCRELCONTAINEDINSPATIALSTRUCTURE':
        refs = [int(r) for r in re.findall(r'#(\d+)', x)]
        for e in refs[1:-1]: storey_of[e] = refs[-1]
aff = collections.Counter(a[e][0] for e in rel_objs if e in a)
aff_storeys = collections.Counter(storeys.get(storey_of.get(e), 'not directly contained') for e in rel_objs)
R = dict(records_a=len(a), records_b=len(b), records_only_in_one=len(only), records_differing=len(diff),
         differing_by_type=types.most_common(), differences_explained_by_regenerated_globalid=explained,
         regenerated_objects_by_type=collections.Counter(regen.values()).most_common(),
         elements_typed_by_regenerated_types=len(rel_objs), affected_element_classes=aff.most_common(),
         affected_storeys=aff_storeys.most_common(), storeys_total=len(storeys))
json.dump(R, open(OUT, 'w'), indent=1); print(json.dumps(R, indent=1))

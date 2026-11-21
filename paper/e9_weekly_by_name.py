"""E9b - The weekly Synchro exports regenerate every GlobalId. This script asks how much of the element content
is nevertheless unchanged between weeks when elements are matched by Name (which carries the original
authoring-tool id) and GlobalIds are left out of the canonical record.

Usage: python e9_weekly_by_name.py OUTDIR WEEK1.ifc WEEK2.ifc ...
"""
import sys, os, json, gc, collections
PAPER = os.environ.get('DK_PAPER', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PAPER)
import ifcopenshell
import dkcore

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
_ent, _body = dkcore.Canon.ent, dkcore.Canon.body


def ent(self, e):                      # rooted references by Name instead of GlobalId
    if e.is_a('IfcRoot') and getattr(e, 'GlobalId', None):
        return '@' + (e.Name or e.is_a())
    return _ent(self, e)


def body(self, e):                     # drop the GlobalId attribute of the element itself
    s = _body(self, e)
    return s.replace(self.val(e.GlobalId), '', 1) if e.is_a('IfcRoot') else s


def records(path):
    f = ifcopenshell.open(path)
    dkcore.Canon.ent, dkcore.Canon.body = ent, body
    c = dkcore.Canon(f); out = {}; dup = 0
    for p in f.by_type('IfcProduct'):
        if p.is_a('IfcSpatialStructureElement') or dkcore.is_dk(p): continue
        k = (p.is_a(), p.Name)
        if k in out: dup += 1; continue
        out[k] = dkcore.leaf_hash(dkcore.element_record(c, p)).hex()
    dkcore.Canon.ent, dkcore.Canon.body = _ent, _body
    gids = {p.GlobalId for p in f.by_type('IfcProduct')}
    del f; gc.collect()
    return out, dup, gids


R = []; prev = None
for path in sys.argv[2:]:
    rec, dup, gids = records(path)
    if prev:
        pr, pg = prev
        common = set(pr) & set(rec)
        same = sum(1 for k in common if pr[k] == rec[k])
        R.append(dict(a=os.path.basename(sys.argv[2 + len(R)]), b=os.path.basename(path), elements_b=len(rec),
                      globalids_shared=len(pg & gids), matched_by_name=len(common), content_unchanged=same,
                      content_changed=len(common) - same, added=len(set(rec) - set(pr)), removed=len(set(pr) - set(rec)),
                      duplicate_names_skipped=dup,
                      changed_by_class=collections.Counter(k[0] for k in common if pr[k] != rec[k]).most_common(5)))
        print(json.dumps(R[-1]), flush=True)
    prev = (rec, gids)
json.dump(R, open(os.path.join(OUT, 'e9_weekly_by_name.json'), 'w'), indent=1)
print('DONE')

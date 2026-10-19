"""Snowdon Towers vaka çalışması: kararlılık, revizyon, gömme ve zincir testleri."""
import sys, time, pickle, hashlib, json, random, re, os
import os as _os; HERE = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, HERE); import numpy as np
import ifcopenshell, ifcopenshell.guid
import dkcore, dkpattern as dp
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

SRC = _os.environ.get('DK_IFC', _os.path.join(HERE, 'input', 'Snowdon_Towers_Sample_Architectural.ifc'))
OUT = _os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
R = {}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for ch in iter(lambda: fh.read(1 << 20), b''): h.update(ch)
    return h.hexdigest()


def timed_tree(f):
    t = time.time(); tr = dkcore.build_tree(f); return tr, time.time() - t


import gc
PREV = json.load(open(f'{OUT}/e1_stability.json'))  # written by e1_stability.py
# ------------------------------------------------------------ 0. taban
t = time.time(); f = ifcopenshell.open(SRC); tl = time.time() - t
base = pickle.load(open(f'{OUT}/tree_rev0.pkl', 'rb')); tt = PREV['base']['t_tree']
R['base'] = PREV['base']
print('BASE', R['base'], flush=True)

R['stability'] = PREV['stability']

# ------------------------------------------------------------ 2. gömme (Pset + IfcAnnotation)
def world_matrix(lp):
    M = np.eye(4)
    chain = []
    while lp is not None:
        chain.append(lp.RelativePlacement); lp = lp.PlacementRelTo
    for a in reversed(chain):
        o = np.array(a.Location.Coordinates + (0,) * (3 - len(a.Location.Coordinates)))
        z = np.array(a.Axis.DirectionRatios) if getattr(a, 'Axis', None) else np.array([0, 0, 1.])
        x = np.array(a.RefDirection.DirectionRatios) if getattr(a, 'RefDirection', None) else np.array([1, 0, 0.])
        z = z / np.linalg.norm(z); x = x - z * (x @ z); x /= np.linalg.norm(x); y = np.cross(z, x)
        A = np.eye(4); A[:3, 0] = x; A[:3, 1] = y; A[:3, 2] = z; A[:3, 3] = o
        M = M @ A
    return M

entrance = [d for d in f.by_type('IfcDoor') if 'Revolving' in (d.Name or '')][0]
Mw = world_matrix(entrance.ObjectPlacement)
R['entrance'] = dict(gid=entrance.GlobalId, name=entrance.Name, origin=Mw[:3, 3].tolist(), x=Mw[:3, 0].tolist(),
                     storey=dkcore.storey_of(entrance, {}).Name)
print('ENTRANCE', R['entrance'], flush=True)

keys = {r: Ed25519PrivateKey.generate() for r in ['Mimar', 'İşveren', 'Belediye']}
ledger = []  # yerel, salt-eklenir test defteri (simülasyon)


def seal(tree, rev, prev, note):
    cr = dkcore.chain_root(tree['root'], prev, rev)
    msg = b'DK|' + cr + rev.to_bytes(4, 'big')
    sigs = {r: k.sign(msg).hex() for r, k in keys.items()}
    for r, k in keys.items():
        k.public_key().verify(bytes.fromhex(sigs[r]), msg)
    prev_block = ledger[-1]['block_hash'] if ledger else '00' * 32
    blk = dict(index=len(ledger), rev=rev, model_root=tree['root'].hex(), chain_root=cr.hex(),
               prev_chain_root=(prev or b'\0' * 32).hex(), note=note, signers=list(sigs), sigs=sigs,
               c14n=dkcore.C14N_VERSION, enc=dp.ENC_VERSION, prev_block=prev_block,
               timestamp=f'2026-10-{16 + rev:02d}T12:00:00+03:00')
    blk['block_hash'] = hashlib.sha256(json.dumps({k: v for k, v in blk.items() if k != 'block_hash'}, sort_keys=True).encode()).hexdigest()
    ledger.append(blk)
    return cr, blk


def embed(g, tree, rev, cr, prev_cr, blk, entrance_gid):
    """Pset_DigitalKitabe + IfcAnnotation (desen geometrisi) ekler."""
    oh = g.by_type('IfcOwnerHistory')[0]
    proj = g.by_type('IfcProject')[0]; bld = g.by_type('IfcBuilding')[0]
    def sv(n, v, t='IfcText'):
        return g.create_entity('IfcPropertySingleValue', Name=n, NominalValue=g.create_entity(t, v))
    props = [sv('ModelRootHash', tree['root'].hex()), sv('ChainRootHash', cr.hex()),
             sv('PreviousRootHash', (prev_cr or b'\0' * 32).hex()), sv('RevisionIndex', rev, 'IfcInteger'),
             sv('HashAlgorithm', 'SHA-256', 'IfcLabel'), sv('CanonicalizationVersion', dkcore.C14N_VERSION, 'IfcLabel'),
             sv('LedgerID', 'DK-TESTNET-LOCAL', 'IfcLabel'), sv('TransactionID', blk['block_hash']),
             sv('Signers', 'Architect;Client;Municipality (Ed25519)'), sv('PatternFamily', 'Star rosette (star-and-polygon)', 'IfcLabel'),
             sv('SymmetryGroup', 'C8 centre / C18 storey ring', 'IfcLabel'),
             sv('Channels', 'colour(2b);motif variant(2b);chirality(1b);rotation(1b)'),
             sv('EncodingSchemeVersion', dp.ENC_VERSION, 'IfcLabel'),
             sv('RegionMap', 'root=centre+crown; storey=inner ring (by elevation, clockwise); storey x discipline=outer ring; non-spatial=corners'),
             sv('SourcePlate', 'Plates XIV, XXVII, XXV (layout principle)')]
    ps = g.create_entity('IfcPropertySet', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh, Name=dkcore.DK_PSET, HasProperties=props)
    g.create_entity('IfcRelDefinesByProperties', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                    Name='DigitalKitabe-Rel', RelatedObjects=[proj, bld], RelatingPropertyDefinition=ps)
    # Emblem geometry: a non-physical project symbol in the annotation context, placed in the
    # local XY plane at the building origin (Rev0 at the origin, repair kitabes in a row beside it).
    ctx = [c for c in g.by_type('IfcGeometricRepresentationSubContext') if c.ContextIdentifier == 'Annotation'][0]
    P = dp.rosette(tree)
    s0 = 0.9 / 0.3048 / 1.18          # 1.8 m emblem, model unit ft
    s = s0 if rev == 0 else s0 * 0.32
    ox = 0.0 if rev == 0 else 4.4 + (rev - 1) * 2.1
    curves = []
    for p in P:
        pts = [g.create_entity('IfcCartesianPoint', Coordinates=(x * s, y * s, 0.0)) for x, y in p['poly']]
        pts.append(pts[0])
        curves.append(g.create_entity('IfcPolyline', Points=pts))
    gcs = g.create_entity('IfcGeometricCurveSet', Elements=curves)
    rep = g.create_entity('IfcShapeRepresentation', ContextOfItems=ctx, RepresentationIdentifier='Annotation',
                          RepresentationType='GeometricCurveSet', Items=[gcs])
    loc = g.create_entity('IfcAxis2Placement3D', Location=g.create_entity('IfcCartesianPoint', Coordinates=(float(ox), 0.0, 0.0)))
    lp = g.create_entity('IfcLocalPlacement', PlacementRelTo=bld.ObjectPlacement, RelativePlacement=loc)
    ann = g.create_entity('IfcAnnotation', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                          Name=f'DigitalKitabe-Rev{rev}', Description='Digital Kitabe emblem (non-physical project symbol)',
                          ObjectType='DigitalKitabeEmblem',
                          ObjectPlacement=lp, Representation=g.create_entity('IfcProductDefinitionShape', Representations=[rep]))
    g.create_entity('IfcRelContainedInSpatialStructure', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                    Name='DigitalKitabe-Containment', RelatedElements=[ann], RelatingStructure=bld)
    doc = g.create_entity('IfcDocumentReference', Location=f'digital_kitabe_rev{rev}_emblem.png', ItemReference=cr.hex()[:16],
                          Name=f'DigitalKitabe-Emblem-Rev{rev}')
    g.create_entity('IfcRelAssociatesDocument', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                    Name='DigitalKitabe-Doc', RelatedObjects=[ann], RelatingDocument=doc)
    return len(curves), sum(len(p['poly']) for p in P)

cr0, blk0 = seal(base, 0, None, 'Design approval (Rev0)')
ncurves, npts = embed(f, base, 0, cr0, None, blk0, entrance.GlobalId)
dp.to_svg(dp.rosette(base), f'{OUT}/digital_kitabe_rev0.svg')
pk = f'{OUT}/Snowdon_DK_rev0.ifc'; f.write(pk)
del f; gc.collect()
g = ifcopenshell.open(pk); trk, _ = timed_tree(g)
ann = [a for a in g.by_type('IfcAnnotation') if (a.Name or '').startswith('DigitalKitabe')]
psk = [p for p in g.by_type('IfcPropertySet') if p.Name == dkcore.DK_PSET]
R['embed'] = dict(root_after=trk['root'].hex(), equal=trk['root'] == base['root'], n_ann=len(ann), n_pset=len(psk),
                  curves=ncurves, points=npts, file_sha=sha_file(pk), size_mb=os.path.getsize(pk) / 1e6,
                  pset_values={p.Name: p.NominalValue.wrappedValue for p in psk[0].HasProperties})
print('EMBED', R['embed']['equal'], R['embed']['root_after'], flush=True)
# negatif kontrol: dışlama kuralı olmasaydı
dkcore_DK = dkcore.DK_PREFIX
dkcore.DK_PREFIX = '__none__'; dkcore.DK_PSET_SAVE = dkcore.DK_PSET; dkcore.DK_PSET = '__none__'
trn, _ = timed_tree(g)
dkcore.DK_PREFIX = dkcore_DK; dkcore.DK_PSET = dkcore.DK_PSET_SAVE
R['embed']['root_without_exclusion'] = trn['root'].hex()
del trn; gc.collect()

# ------------------------------------------------------------ 3. kontrollü revizyonlar (birikimli)
f = g
st = {s.Name: s for s in f.by_type('IfcBuildingStorey')}
def contained(sname, cls):
    return [e for r in st[sname].ContainsElements for e in r.RelatedElements if e.is_a(cls)]

def rev1(f):
    d = [x for x in contained('L3', 'IfcDoor')][5]
    lp = d.ObjectPlacement; a = lp.RelativePlacement
    c = list(a.Location.Coordinates); c[0] += 0.5 / 0.3048
    na = f.create_entity('IfcAxis2Placement3D', Location=f.create_entity('IfcCartesianPoint', Coordinates=tuple(c)),
                         Axis=a.Axis, RefDirection=a.RefDirection)
    lp.RelativePlacement = na
    return f'Storey L3: door ({d.Name.split(":")[0]}) moved by 0.50 m', d.GlobalId

def rev2(f):
    w = contained('L4', 'IfcWallStandardCase')[10]
    for r in w.IsDefinedBy:
        if r.is_a('IfcRelDefinesByProperties') and r.RelatingPropertyDefinition.Name == 'Pset_ConcreteElementGeneral':
            ps = r.RelatingPropertyDefinition
            old = ps.HasProperties[0]
            ps.HasProperties = [f.create_entity('IfcPropertySingleValue', Name='FireRating', NominalValue=f.create_entity('IfcLabel', '1 HR'))]
            return f'Storey L4: wall FireRating changed {old.NominalValue.wrappedValue} -> 1 HR', w.GlobalId

def rev3(f):
    e = contained('L2', 'IfcFurnishingElement')[3]
    gid = e.GlobalId; nm = e.Name.split(':')[0]
    for r in e.ContainedInStructure:
        r.RelatedElements = [x for x in r.RelatedElements if x != e]
    for r in list(e.IsDefinedBy):
        if len(r.RelatedObjects) == 1: f.remove(r)
        else: r.RelatedObjects = [x for x in r.RelatedObjects if x != e]
    f.remove(e)
    return f'Storey L2: furnishing element ({nm}) deleted', gid

def rev4(f):
    t = f.by_type('IfcDoorStyle')[0]
    for ps in t.HasPropertySets:
        if ps.is_a('IfcPropertySet') and ps.Name == 'Pset_DoorCommon':
            ps.HasProperties = [f.create_entity('IfcPropertySingleValue', Name='FireRating', NominalValue=f.create_entity('IfcLabel', '120 MIN'))]
            return f'Door type "{t.Name}": FireRating 180 MIN -> 120 MIN (type level)', t.GlobalId

trees = [base]; revs = []
prev_cr = cr0
for k, fn in enumerate([rev1, rev2, rev3, rev4], start=1):
    note, gid = fn(f)
    tr, tt = timed_tree(f)
    d = dkcore.diff(trees[-1], tr)
    ns_changed = tr['nonspatial'] != trees[-1]['nonspatial']
    cr, blk = seal(tr, k, prev_cr, note)
    embed(f, tr, k, cr, prev_cr, blk, entrance.GlobalId)  # onarım kitabesi
    dp.to_svg(dp.rosette(tr), f'{OUT}/digital_kitabe_rev{k}.svg')
    revs.append(dict(rev=k, note=note, gid=gid, root=tr['root'].hex(), chain_root=cr.hex(), diff=d,
                     nonspatial_changed=ns_changed, t_tree=tt))
    print('REV', k, note, d, ns_changed, flush=True)
    pickle.dump(tr, open(f'{OUT}/tree_rev{k}.pkl', 'wb'))
    trees.append(tr); prev_cr = cr
    trees[-2] = None if len(trees) > 2 else trees[-2]
    gc.collect()
R['revisions'] = revs
R['ledger'] = ledger

# ------------------------------------------------------------ 4. zincir doğrulaması (alıcı tarafı)
ok = True
for i, b in enumerate(ledger):
    exp_prev = ledger[i - 1]['block_hash'] if i else '00' * 32
    ok &= b['prev_block'] == exp_prev
    ok &= dkcore.chain_root(bytes.fromhex(b['model_root']), bytes.fromhex(b['prev_chain_root']) if i else None, b['rev']).hex() == b['chain_root']
R['ledger_ok'] = ok
json.dump(R, open(f'{OUT}/results.json', 'w'), ensure_ascii=False, indent=1, default=str)
json.dump(ledger, open(f'{OUT}/ledger.json', 'w'), ensure_ascii=False, indent=1)
print('DONE', ok)

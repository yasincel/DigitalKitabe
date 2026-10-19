#!/usr/bin/env python3
"""Digital Kitabe – command-line tool.

  python dkitabe.py stamp  MODEL.ifc [--previous KAYIT.json] [--out KLASOR] [--no-embed]
  python dkitabe.py verify MODEL.ifc KAYIT.json [--out KLASOR]
  python dkitabe.py identify DESEN.png KAYIT_KLASORU

stamp : computes the canonical Merkle root, draws the pattern (SVG + PNG),
        embeds Pset_DigitalKitabe + IfcAnnotation into a copy of the IFC and
        writes a record (JSON). With --previous it creates the next revision
        (repair kitabe) and a comparison image.
verify: recomputes the root of a received IFC and compares it with a record;
        lists changed storeys, disciplines and elements and draws a comparison.
"""
import argparse, hashlib, json, os, sys, time, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import ifcopenshell, ifcopenshell.guid
except ImportError:
    sys.exit('IfcOpenShell bulunamadı / not found.  Kurulum / install:  pip install ifcopenshell')
import dkcore, dkpattern as dp

DISC_EN = {'YAP': 'STR', 'DUV': 'WAL', 'CEP': 'FAC', 'ACK': 'OPN', 'DOL': 'CIR', 'DON': 'FUR', 'MEK': 'SPC', 'DIG': 'OTH'}
DISC_NAME = {'YAP': 'Structure/slabs', 'DUV': 'Walls', 'CEP': 'Facade/windows', 'ACK': 'Doors/openings',
             'DOL': 'Circulation', 'DON': 'Furnishing/fixtures', 'MEK': 'Spaces', 'DIG': 'Other'}
TOOL_VERSION = '1.0.0'


def log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------ record <-> tree
def tree_to_record(tr):
    return dict(
        root=tr['root'].hex(), spatial=tr['spatial'].hex(), nonspatial=tr['nonspatial'].hex(),
        n_leaves=tr['n_leaves'], n_types=tr['n_types'], n_materials=tr['n_mats'],
        storeys=[dict(gid=s['gid'], name=s['name'], elevation=s['elev'], hash=s['hash'].hex(),
                      disc={d: dict(n=v['n'], hash=v['hash'].hex(), leaves={g: h.hex() for g, h in v['leaves']})
                            for d, v in s['disc'].items()}) for s in tr['storeys']])


def record_to_tree(r):
    b = bytes.fromhex
    return dict(root=b(r['root']), spatial=b(r['spatial']), nonspatial=b(r['nonspatial']),
                n_leaves=r['n_leaves'],
                storeys=[dict(gid=s['gid'], name=s['name'], elev=s['elevation'], hash=b(s['hash']),
                              disc={d: dict(n=v['n'], hash=b(v['hash']), leaves=sorted((g, b(h)) for g, h in v['leaves'].items()))
                                    for d, v in s['disc'].items()}) for s in r['storeys']])


def compare(old, new):
    """old/new: trees. Returns list of changes and the set of changed pattern regions."""
    changes = []
    if [s['gid'] for s in old['storeys']] != [s['gid'] for s in new['storeys']]:
        changes.append(dict(level='storeys', what='storey list changed (added, removed or reordered storeys)'))
    for a, b in zip(old['storeys'], new['storeys']):
        if a['hash'] == b['hash']:
            continue
        for d in a['disc']:
            if a['disc'][d]['hash'] != b['disc'][d]['hash']:
                la, lb = dict(a['disc'][d]['leaves']), dict(b['disc'][d]['leaves'])
                for g in sorted(set(la) | set(lb)):
                    if la.get(g) != lb.get(g):
                        kind = 'added' if g not in la else 'deleted' if g not in lb else 'modified'
                        changes.append(dict(level='element', storey=b['name'], discipline=DISC_EN[d], gid=g, change=kind))
        if not any(c.get('storey') == b['name'] for c in changes):
            changes.append(dict(level='storey', storey=b['name'], what='storey attributes changed'))
    if old['nonspatial'] != new['nonspatial']:
        changes.append(dict(level='non-spatial', what='types, materials or project data changed'))
    if old['spatial'] != new['spatial'] and not changes:
        changes.append(dict(level='building', what='building-level elements or site/building attributes changed'))
    return changes


def pattern_tree(tr):
    """Compact tree (no leaves) that is sufficient to redraw the pattern of a revision."""
    return dict(root=tr['root'].hex(), spatial=tr['spatial'].hex(), nonspatial=tr['nonspatial'].hex(), n_leaves=tr['n_leaves'],
                storeys=[dict(gid=s['gid'], name=s['name'], elevation=s['elev'], hash=s['hash'].hex(),
                              disc={d: dict(n=v['n'], hash=v['hash'].hex(), leaves={}) for d, v in s['disc'].items()}) for s in tr['storeys']])


# ------------------------------------------------------------------ drawing
def save_pattern(tree, base):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    P = dp.rosette(tree)
    dp.to_svg(P, base + '.svg')
    fig, ax = plt.subplots(figsize=(6, 6)); dp.draw(ax, P)
    fig.savefig(base + '.png', dpi=200, bbox_inches='tight', facecolor='white'); plt.close(fig)


def save_comparison(old, new, path, title_old='Approved', title_new='Received'):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Circle
    import numpy as np
    Pa, Pb = dp.rosette(old), dp.rosette(new)
    sa, sb = dp.region_signature(Pa), dp.region_signature(Pb)
    ch = {k for k in sa if sa[k] != sb.get(k)}
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.6))
    dp.draw(axs[0], Pa); dp.draw(axs[1], Pb)
    for p in Pb:
        r = p['region']
        if r in ch and (r.startswith('disc') or r.startswith('storey')) and p['z'] == 1:
            axs[1].add_patch(Polygon(p['poly'], closed=True, fc='none', ec='#d01c1c', lw=2.4, zorder=10))
        if r in ch and r == 'nonspatial' and p['z'] == 2 and len(p['poly']) == 16:
            c = np.mean(np.array(p['poly']), 0); rad = np.max(np.linalg.norm(np.array(p['poly']) - c, axis=1)) * 1.25
            axs[1].add_patch(Circle(tuple(c), rad, fc='none', ec='#d01c1c', lw=2.2, zorder=10))
    axs[0].set_title(f'{title_old}\nroot {old["root"].hex()[:12]}…', fontsize=10)
    axs[1].set_title(f'{title_new}\nroot {new["root"].hex()[:12]}…', fontsize=10)
    fig.savefig(path, dpi=170, bbox_inches='tight', facecolor='white'); plt.close(fig)


# ------------------------------------------------------------------ embedding
def world_matrix(lp):
    import numpy as np
    M = np.eye(4); chain = []
    while lp is not None:
        chain.append(lp.RelativePlacement); lp = getattr(lp, 'PlacementRelTo', None)
    for a in reversed(chain):
        o = np.array(list(a.Location.Coordinates) + [0.0] * (3 - len(a.Location.Coordinates)))
        z = np.array(a.Axis.DirectionRatios) if getattr(a, 'Axis', None) else np.array([0, 0, 1.])
        x = np.array(a.RefDirection.DirectionRatios) if getattr(a, 'RefDirection', None) else np.array([1, 0, 0.])
        z = z / np.linalg.norm(z); x = x - z * (x @ z); x /= np.linalg.norm(x); y = np.cross(z, x)
        A = np.eye(4); A[:3, 0] = x; A[:3, 1] = y; A[:3, 2] = z; A[:3, 3] = o
        M = M @ A
    return M


def pick_entrance(f):
    doors = f.by_type('IfcDoor')
    for key in ('Revolving', 'Entrance', 'Main', 'Giriş', 'Giris'):
        for d in doors:
            if key.lower() in (d.Name or '').lower():
                return d
    for d in doors:
        for r in getattr(d, 'IsDefinedBy', ()) or ():
            pd = getattr(r, 'RelatingPropertyDefinition', None)
            if pd is not None and getattr(pd, 'Name', '') == 'Pset_DoorCommon':
                for p in getattr(pd, 'HasProperties', ()) or ():
                    if p.Name == 'IsExternal' and getattr(p.NominalValue, 'wrappedValue', False):
                        return d
    return doors[0] if doors else None


def length_scale(f):
    """model units per metre"""
    for ua in f.by_type('IfcUnitAssignment'):
        for u in ua.Units:
            if getattr(u, 'UnitType', None) == 'LENGTHUNIT':
                if u.is_a('IfcConversionBasedUnit'):
                    return 1.0 / float(u.ConversionFactor.ValueComponent.wrappedValue)
                if u.is_a('IfcSIUnit'):
                    pre = {'MILLI': 1e-3, 'CENTI': 1e-2, 'DECI': 1e-1, None: 1.0}.get(u.Prefix, 1.0)
                    return 1.0 / pre
    return 1.0


def embed(f, tree, rev, chain_root, prev_chain, record_id, svg_name):
    oh = (f.by_type('IfcOwnerHistory') or [None])[0]
    proj = f.by_type('IfcProject')[0]; bld = (f.by_type('IfcBuilding') or [None])[0]
    def sv(n, v, t='IfcText'):
        return f.create_entity('IfcPropertySingleValue', Name=n, NominalValue=f.create_entity(t, v))
    props = [sv('ModelRootHash', tree['root'].hex()), sv('ChainRootHash', chain_root.hex()),
             sv('PreviousRootHash', (prev_chain or b'\0' * 32).hex()), sv('RevisionIndex', rev, 'IfcInteger'),
             sv('HashAlgorithm', 'SHA-256', 'IfcLabel'), sv('CanonicalizationVersion', dkcore.C14N_VERSION, 'IfcLabel'),
             sv('LedgerID', 'LOCAL-RECORD', 'IfcLabel'), sv('TransactionID', record_id),
             sv('PatternFamily', 'Star rosette (star-and-polygon)', 'IfcLabel'),
             sv('SymmetryGroup', f'C8 centre / C{len(tree["storeys"])} storey ring', 'IfcLabel'),
             sv('Channels', 'colour(2b);motif variant(2b);chirality(1b);rotation(1b)'),
             sv('EncodingSchemeVersion', dp.ENC_VERSION, 'IfcLabel'),
             sv('RegionMap', 'root=centre+crown; storey=inner ring (by elevation, clockwise); storey x discipline=outer ring; non-spatial=corners')]
    ps = f.create_entity('IfcPropertySet', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh, Name=dkcore.DK_PSET, HasProperties=props)
    f.create_entity('IfcRelDefinesByProperties', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh, Name='DigitalKitabe-Rel',
                    RelatedObjects=[x for x in (proj, bld) if x is not None], RelatingPropertyDefinition=ps)
    ctxs = [c for c in f.by_type('IfcGeometricRepresentationSubContext') if c.ContextIdentifier == 'Annotation']
    if not ctxs:
        ctxs = [c for c in f.by_type('IfcGeometricRepresentationContext') if not c.is_a('IfcGeometricRepresentationSubContext')]
    ctx = ctxs[0]
    u = length_scale(f)                      # model units per metre
    P = dp.rosette(tree)
    s0 = 0.9 / 1.18 * u                      # 1.8 m emblem
    s = s0 if rev == 0 else s0 * 0.32
    ox = 0.0 if rev == 0 else (1.34 + (rev - 1) * 0.64) * u
    curves = []
    for p in P:
        pts = [f.create_entity('IfcCartesianPoint', Coordinates=(float(x * s), float(y * s), 0.0)) for x, y in p['poly']]
        pts.append(pts[0]); curves.append(f.create_entity('IfcPolyline', Points=pts))
    rep = f.create_entity('IfcShapeRepresentation', ContextOfItems=ctx, RepresentationIdentifier='Annotation',
                          RepresentationType='GeometricCurveSet', Items=[f.create_entity('IfcGeometricCurveSet', Elements=curves)])
    host = bld or (f.by_type('IfcSite') or [None])[0]
    loc = f.create_entity('IfcAxis2Placement3D', Location=f.create_entity('IfcCartesianPoint', Coordinates=(float(ox), 0.0, 0.0)))
    lp = f.create_entity('IfcLocalPlacement', PlacementRelTo=host.ObjectPlacement if host is not None else None, RelativePlacement=loc)
    ann = f.create_entity('IfcAnnotation', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh, Name=f'DigitalKitabe-Rev{rev}',
                          Description='Digital Kitabe emblem (non-physical project symbol)', ObjectType='DigitalKitabeEmblem',
                          ObjectPlacement=lp, Representation=f.create_entity('IfcProductDefinitionShape', Representations=[rep]))
    if host is not None:
        f.create_entity('IfcRelContainedInSpatialStructure', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh,
                        Name='DigitalKitabe-Containment', RelatedElements=[ann], RelatingStructure=host)
    idk = 'ItemReference' if f.schema == 'IFC2X3' else 'Identification'
    doc = f.create_entity('IfcDocumentReference', Location=svg_name.replace('.svg', '_emblem.png'), Name=f'DigitalKitabe-Emblem-Rev{rev}', **{idk: chain_root.hex()[:16]})
    f.create_entity('IfcRelAssociatesDocument', GlobalId=ifcopenshell.guid.new(), OwnerHistory=oh, Name='DigitalKitabe-Doc',
                    RelatedObjects=[ann], RelatingDocument=doc)
    return 'emblem at building origin (non-physical symbol)'


# ------------------------------------------------------------------ building summary
def building_summary(f, tr):
    def nm(x): return (getattr(x, 'LongName', None) or getattr(x, 'Name', None) or '') if x is not None else ''
    proj = (f.by_type('IfcProject') or [None])[0]; bld = (f.by_type('IfcBuilding') or [None])[0]
    site = (f.by_type('IfcSite') or [None])[0]
    addr = ''
    a = getattr(bld, 'BuildingAddress', None) if bld is not None else None
    if a is not None:
        addr = ', '.join(x for x in list(getattr(a, 'AddressLines', None) or []) + [getattr(a, 'Town', None) or '', getattr(a, 'Country', None) or ''] if x)
    app = ''
    for h in f.by_type('IfcApplication')[:1]:
        app = f'{h.ApplicationFullName or ""} {h.Version or ""}'.strip()
    disc_tot = {DISC_EN[d]: sum(s['disc'][d]['n'] for s in tr['storeys']) for d in dkcore.DISC_CODES}
    return dict(project=nm(proj), project_number=getattr(proj, 'Name', '') or '', building=nm(bld), site=nm(site),
                address=addr, schema=f.schema, authoring_application=app, length_unit_per_metre=round(length_scale(f), 6),
                elements=tr['n_leaves'], storeys=len(tr['storeys']), types=tr['n_types'], materials=tr['n_mats'],
                elements_per_discipline=disc_tot,
                storey_list=[dict(name=s['name'], elevation=s['elev'], elements=sum(v['n'] for v in s['disc'].values())) for s in tr['storeys']])


# ------------------------------------------------------------------ identify (pattern image -> record)
PAL_LABELS = [('#173d7a', 'C0'), ('#2a9d9a', 'C1'), ('#e0a526', 'C2'), ('#b5452c', 'C3'), ('#f6f1e6', 'PAPER'), ('#e7e1d3', 'EMPTY'), ('#141414', 'INK')]


def _rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _rasterise(P, S):
    """Draws pattern P into an S x S label image and a region-id image (frame square = full image)."""
    from PIL import Image, ImageDraw
    import numpy as np
    lab_of = {h: i for i, (h, _) in enumerate(PAL_LABELS)}
    L = Image.new('L', (S, S), lab_of['#f6f1e6']); dl = ImageDraw.Draw(L)
    regs = sorted({p['region'] for p in P}); rid = {r: k + 1 for k, r in enumerate(regs)}
    Rg = Image.new('I', (S, S), 0); dr = ImageDraw.Draw(Rg)
    tf = lambda pts: [((x + 1.18) / 2.36 * (S - 1), (1.18 - y) / 2.36 * (S - 1)) for x, y in pts]
    for p in sorted(P, key=lambda q: q['z']):
        q = tf(p['poly'])
        dl.polygon(q, fill=lab_of.get(p['fill'], 4))
        if p['region'] not in ('frame', 'disc-bg'):
            dr.polygon(q, fill=rid[p['region']])
    return np.array(L), np.array(Rg), {v: k for k, v in rid.items()}


def _locate_pattern(im):
    """Finds the square pattern panel in an image (plain pattern PNG, screenshot or emblem sheet)."""
    import numpy as np
    try:
        from scipy import ndimage
    except ImportError:
        return im
    nonwhite = im.sum(2) < 735
    lab, n = ndimage.label(nonwhite)
    if n == 0: return im
    H, W = nonwhite.shape; best = None
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        if h < 0.15 * min(H, W) or (h > 0.92 * H and w > 0.92 * W):
            continue          # too small, or the outer page frame
        if not (0.94 < h / w < 1.06):
            continue          # inscription bands are not square
        area = h * w
        if best is None or area > best[0]: best = (area, sl)
    if best is None: return im
    sl = best[1]; m = 3
    return im[max(sl[0].start - m, 0):sl[0].stop + m, max(sl[1].start - m, 0):sl[1].stop + m]


def _image_labels(path, S):
    from PIL import Image
    import numpy as np
    if path.lower().endswith('.svg'):
        sys.exit('SVG için önce PNG kullanın / please provide the PNG export of the pattern')
    im = np.array(Image.open(path).convert('RGB')).astype(float)
    im = _locate_pattern(im)
    dark = (im.sum(2) < 600)   # anything clearly darker than the paper tone (frame line, ink, colours)
    ys, xs = np.where(dark)
    if len(xs) == 0: sys.exit('Desen bulunamadı / no pattern found in image')
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    # the frame is drawn with a stroke centred on its edge: shrink the box by half the stroke width
    row = dark[(y0 + y1) // 2, x0:x1 + 1]
    t = int(np.argmax(~row)) if (~row).any() else 0
    h = t // 2
    y0, y1, x0, x1 = y0 + h, y1 - h, x0 + h, x1 - h
    crop = Image.fromarray(im[y0:y1 + 1, x0:x1 + 1].astype('uint8')).resize((S, S), Image.BILINEAR)
    a = np.array(crop).astype(float)
    pal = np.array([_rgb(h) for h, _ in PAL_LABELS], float)
    d = ((a[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(3)
    lab = d.argmin(2)
    lab[lab == 5] = 4        # paper and empty-cell tones are merged (robust to JPEG/screen colour shifts)
    return lab


def _erode(mask, e):
    import numpy as np
    S0, S1 = mask.shape
    pad = np.pad(mask, e, constant_values=False)
    out = mask.copy()
    for dy in range(-e, e + 1):
        for dx in range(-e, e + 1):
            out &= pad[e + dy:e + dy + S0, e + dx:e + dx + S1]
    return out


def region_scores(img_lab, tree, S):
    """Share of agreeing pixels per pattern region (regions eroded to ignore outlines and edge bleeding)."""
    import numpy as np
    exp_lab, reg, names = _rasterise(dp.rosette(tree), S)
    exp_lab = exp_lab.copy(); exp_lab[exp_lab == 5] = 4
    PAPER, INK = 4, len(PAL_LABELS) - 1
    # pixels close to drawn outlines carry anti-aliasing blends: ignore a band around every ink pixel
    halo = ~_erode(img_lab != INK, 3)
    out = {}
    for k, r in names.items():
        core = _erode(reg == k, 3) & ~halo
        if core.sum() < 20:
            continue
        drawn = core & ((img_lab != PAPER) | (exp_lab != PAPER))
        if drawn.sum() < 0.03 * core.sum():
            out[r] = 1.0            # background-only (empty node) in both images
            continue
        out[r] = float((img_lab[drawn] == exp_lab[drawn]).mean())
    return out


def cmd_identify(a):
    S = 700
    recs = []
    for root, _, files in os.walk(a.registry):
        for fn in files:
            if fn.endswith('_record.json'):
                try:
                    recs.append((os.path.join(root, fn), json.load(open(os.path.join(root, fn), encoding='utf-8'))))
                except Exception:
                    pass
    if not recs: sys.exit(f'Kayıt bulunamadı / no *_record.json in {a.registry}')
    img = _image_labels(a.image, S)
    results = []
    for path, r in recs:
        tr = record_to_tree(r['tree'])
        sc = region_scores(img, tr, S)
        if not sc: continue
        match = [k for k, v in sc.items() if v >= 0.5]
        root_ok = sc.get('root', 0) >= 0.5
        results.append((len(match) / len(sc), root_ok, path, r, sc))
    results.sort(key=lambda t: (t[1], t[0]), reverse=True)
    best = results[0]
    frac, root_ok, path, r, sc = best
    log(f'{len(recs)} kayıt tarandı / records searched')
    if root_ok and frac >= 0.99:
        log('\nEŞLEŞTİ / MATCH: desen bu kayda aittir / the pattern belongs to this record')
    elif frac > 0.6:
        log('\nKISMİ EŞLEŞME / PARTIAL MATCH: en yakın kayıt aynı binanın farklı bir sürümü olabilir')
    else:
        log('\nEŞLEŞME YOK / NO MATCH: kayıtlı hiçbir modelle uyuşmuyor'); 
    log(f'  benzerlik / similarity: {frac * 100:.1f}% bölge / of regions   kayıt / record: {path}')
    b = r.get('building', {})
    log('\nBİNA BİLGİLERİ / BUILDING INFORMATION (kayıttan / from record)')
    for k, lab in (('project', 'Proje'), ('project_number', 'Proje no'), ('building', 'Bina'), ('site', 'Arazi'), ('address', 'Adres'),
                   ('schema', 'IFC şeması'), ('authoring_application', 'Yazılım'), ('elements', 'Eleman'), ('storeys', 'Kat'),
                   ('types', 'Tip'), ('materials', 'Malzeme')):
        if b.get(k) not in (None, ''): log(f'  {lab:12s}: ' + ' '.join(str(b[k]).split()))
    if not b:
        log(f"  Dosya: {r.get('source_file')}  eleman: {r['tree']['n_leaves']}  kat: {len(r['tree']['storeys'])}")
    if b.get('elements_per_discipline'):
        log('  Disiplinler : ' + ', '.join(f'{k} {v}' for k, v in b['elements_per_discipline'].items()))
    if b.get('storey_list'):
        log('  Katlar      : ' + '; '.join(f"{x['name']} ({x['elements']})" for x in b['storey_list']))
    log(f"  Kaynak dosya: {r.get('source_file')}   oluşturma/created: {r.get('created')}")
    log(f"  Revizyon    : {r.get('revision')}  {r.get('note', '')}")
    log(f"  Model kökü  : {r.get('model_root')}")
    for h in r.get('history', []):
        log(f"    Rev{h['revision']}: {h['model_root'][:16]}…  {h.get('note', '')}")
    bad = sorted(k for k, v in sc.items() if v < 0.5)
    if bad:
        tr = record_to_tree(r['tree'])
        def rn(x):
            if x.startswith('storey:'): return tr['storeys'][int(x.split(':')[1])]['name'] + ' (kat sektörü)'
            if x.startswith('disc:'):
                _, i, d = x.split(':'); return tr['storeys'][int(i)]['name'] + ' · ' + DISC_EN[d]
            return {'root': 'kök (merkez)', 'nonspatial': 'tipler/malzemeler (köşeler)'}.get(x, x)
        log('  Kayıttan farklı görünen bölgeler / regions that differ from the record:')
        for x in bad: log(f'    - {rn(x)}')
    if len(results) > 1:
        log('\nDiğer adaylar / other candidates:')
        for fr, ro, p, rr, _ in results[1:4]:
            log(f"  {fr * 100:5.1f}%  {os.path.basename(p)}")
    log('\nNot: Görsel okuma bir tanıma kolaylığıdır; bağlayıcı doğrulama için IFC dosyasıyla `verify` kullanın.')


# ------------------------------------------------------------------ commands
def load(path):
    t = time.time(); log(f'IFC okunuyor / reading: {path}')
    f = ifcopenshell.open(path); log(f'  {time.time() - t:.1f} s, şema/schema {f.schema}')
    t = time.time(); log('Kanonik özet ve Merkle ağacı hesaplanıyor / computing canonical Merkle tree …')
    tr = dkcore.build_tree(f); log(f'  {time.time() - t:.1f} s, {tr["n_leaves"]} eleman/elements')
    return f, tr


def cmd_stamp(a):
    name = os.path.splitext(os.path.basename(a.model))[0]
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.model)), name + '_kitabe')
    os.makedirs(out, exist_ok=True)
    f, tr = load(a.model)
    prev = json.load(open(a.previous, encoding='utf-8')) if a.previous else None
    rev = prev['revision'] + 1 if prev else 0
    prev_chain = bytes.fromhex(prev['chain_root']) if prev else None
    chain = dkcore.chain_root(tr['root'], prev_chain, rev)
    rec_summary = building_summary(f, tr)
    rec = dict(tool='digital-kitabe', tool_version=TOOL_VERSION, building=rec_summary, c14n=dkcore.C14N_VERSION, encoding=dp.ENC_VERSION,
               created=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
               source_file=os.path.basename(a.model), source_file_sha256=sha_file(a.model),
               revision=rev, model_root=tr['root'].hex(), chain_root=chain.hex(),
               previous_chain_root=(prev_chain or b'\0' * 32).hex(), note=a.note or '',
               history=(prev.get('history', []) if prev else []) + [dict(revision=rev, model_root=tr['root'].hex(), chain_root=chain.hex(), note=a.note or '',
                                                                          date=datetime.date.today().isoformat(), pattern=pattern_tree(tr))],
               tree=tree_to_record(tr))
    rec['record_id'] = hashlib.sha256(json.dumps({k: v for k, v in rec.items() if k != 'tree'}, sort_keys=True).encode()).hexdigest()
    base = os.path.join(out, f'{name}_rev{rev}_kitabe')
    save_pattern(tr, base)
    import dksheet
    hist = rec['history']
    meta = dict(project=rec_summary.get('project') or name, number=rec_summary.get('project_number', ''),
                building=rec_summary.get('building', ''), date=datetime.date.today().isoformat(),
                revision=rev, root=tr['root'].hex(), c14n=dkcore.C14N_VERSION, enc=dp.ENC_VERSION)
    meds = [(f"Rev{h['revision']}", record_to_tree(h['pattern'])) for h in hist[:-1] if 'pattern' in h]
    dksheet.draw_sheet(base + '_emblem.png', tr, meta, meds)
    if prev:
        old = record_to_tree(prev['tree'])
        rec['changes_since_previous'] = compare(old, tr)
        save_comparison(old, tr, os.path.join(out, f'{name}_rev{prev["revision"]}_vs_rev{rev}.png'), f'Rev{prev["revision"]}', f'Rev{rev}')
    if not a.no_embed:
        loc = embed(f, tr, rev, chain, prev_chain, rec['record_id'], os.path.basename(base) + '.svg')
        ifc_out = os.path.join(out, f'{name}_rev{rev}_with_kitabe.ifc')
        log(f'Kimlik gömülüyor / embedding identity (konum/location: {loc}) …'); f.write(ifc_out)
        rec['stamped_file'] = os.path.basename(ifc_out)
    json.dump(rec, open(base + '_record.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    log('\nTAMAM / DONE')
    log(f'  Model kökü / model root : {tr["root"].hex()}')
    log(f'  Revizyon / revision      : {rev}')
    log(f'  Çıktılar / outputs       : {out}')
    if prev:
        print_changes(rec['changes_since_previous'])


def print_changes(ch):
    if not ch:
        log('  Önceki kayda göre değişiklik yok / no changes since previous record'); return
    log(f'  Değişiklikler / changes ({len(ch)}):')
    for c in ch[:50]:
        if c['level'] == 'element':
            log(f"    - {c['storey']} · {c['discipline']}: {c['change']} {c['gid']}")
        else:
            log(f"    - {c.get('storey', c['level'])}: {c['what']}")
    if len(ch) > 50: log(f'    … +{len(ch) - 50}')


def cmd_verify(a):
    rec = json.load(open(a.record, encoding='utf-8'))
    if rec.get('c14n') != dkcore.C14N_VERSION:
        log(f"UYARI / WARNING: kayıt {rec.get('c14n')} ile, araç {dkcore.C14N_VERSION} ile hesaplıyor")
    f, tr = load(a.model)
    old = record_to_tree(rec['tree'])
    ok = tr['root'] == old['root']
    out = a.out or os.path.dirname(os.path.abspath(a.model))
    name = os.path.splitext(os.path.basename(a.model))[0]
    log('')
    if ok:
        log('DOĞRULANDI / VERIFIED: model, kayıttaki onaylı sürümle aynı içeriğe sahip.')
        log(f'  root {tr["root"].hex()}  (revision {rec["revision"]})')
    else:
        log('UYUŞMUYOR / MISMATCH: model, kayıttaki onaylı sürümden farklı.')
        log(f'  kayıt / record  : {old["root"].hex()}')
        log(f'  model           : {tr["root"].hex()}')
        ch = compare(old, tr); print_changes(ch)
        img = os.path.join(out, f'{name}_verify_comparison.png')
        save_comparison(old, tr, img, f'Record rev{rec["revision"]}', 'Received model')
        json.dump(ch, open(os.path.join(out, f'{name}_verify_changes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        log(f'  Karşılaştırma görseli / comparison image: {img}')
    sys.exit(0 if ok else 2)


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for ch in iter(lambda: fh.read(1 << 20), b''): h.update(ch)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description='Digital Kitabe: IFC model identity (Merkle root + historical pattern)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('stamp', help='kimlik üret ve göm / create and embed identity')
    s.add_argument('model'); s.add_argument('--previous', help='önceki kayıt (revizyon için) / previous record JSON')
    s.add_argument('--out', help='çıktı klasörü / output folder'); s.add_argument('--note', help='revizyon notu / revision note')
    s.add_argument('--no-embed', action='store_true', help='IFC kopyası yazma / do not write stamped IFC')
    v = sub.add_parser('verify', help='gelen IFC dosyasını kayda göre doğrula / verify against record')
    v.add_argument('model'); v.add_argument('record'); v.add_argument('--out')
    i = sub.add_parser('identify', help='desen görselinden kaydı ve bina bilgisini bul / identify a pattern image')
    i.add_argument('image', help='desen PNG / pattern PNG'); i.add_argument('registry', help='kayıt klasörü / folder with *_record.json')
    a = ap.parse_args()
    {'stamp': cmd_stamp, 'verify': cmd_verify, 'identify': cmd_identify}[a.cmd](a)


if __name__ == '__main__':
    main()

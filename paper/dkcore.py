"""Dijital Kitabe - prototip çekirdeği (kanonikleştirme + Merkle ağacı).

Kanonikleştirme sürümü: DK-C14N-1.0
  * OwnerHistory alanları ve IfcOwnerHistory varlıkları dışlanır.
  * Varlık kimlikleri (#n) kullanılmaz; köklenmiş (GlobalId'li) nesneler GlobalId ile,
    köklenmemiş nesneler içerikleriyle (özyinelemeli) temsil edilir.
  * Gerçek sayılar birim sistemine uygun bir ızgaraya nicemlenir: imparatorluk birimlerinde
    (ft, in) ikili ızgara 2^-10 ft (kesirli inç değerleri ızgara noktasına düşer), metrik
    birimlerde ondalık ızgara 1e-4 m; yön kosinüsleri 2^-20. Izgara sınırı irrasyonel bir
    kaymayla (2 - sqrt 2) ötelenir. Sürüm 1.0'daki 1e-6 ondalık
    yuvarlama, 1/128 ft gibi ikili kesirlerde yuvarlama sınırına düşüp ve 15/17 haneli
    yazım farklarında yazılımlar arası farklı kök üretmişti.
  * Kümeler (SET) sıralanır; listeler (LIST) sırası korunur.
  * Dijital Kitabe nesneleri (Name 'DigitalKitabe' ile başlayan nesneler ve
    Pset_DigitalKitabe) özet hesaplanmadan önce çıkarılır (kendine gönderme kuralı).
"""
import hashlib, sys, math
import ifcopenshell

C14N_VERSION = 'DK-C14N-1.1'
# Kaydırılmış nicemleme: sınır, ızgara adımının kesirli kısmı (sqrt(2)-1) ≈ 0,4142 noktasına düşer.
# Küçük paydalı rasyonel değerler (ikili inç kesirleri, 1/3 katları, ondalık değerler) bu sınırdan
# uzak kaldığı için 15/17 haneli yazım gürültüsü nicemlenmiş değeri değiştirmez.
Q_OFFSET = 2.0 - math.sqrt(2.0)
DK_PREFIX = 'DigitalKitabe'
DK_PSET = 'Pset_DigitalKitabe'

DISCIPLINES = [
    ('YAP', 'Taşıyıcı ve döşeme', ('IfcColumn', 'IfcBeam', 'IfcSlab', 'IfcRoof', 'IfcFooting')),
    ('DUV', 'Duvarlar', ('IfcWall', 'IfcWallStandardCase')),
    ('CEP', 'Cephe ve pencere', ('IfcCurtainWall', 'IfcPlate', 'IfcMember', 'IfcWindow')),
    ('ACK', 'Kapı ve açıklıklar', ('IfcDoor', 'IfcOpeningElement')),
    ('DOL', 'Dolaşım', ('IfcStair', 'IfcStairFlight', 'IfcRamp', 'IfcRampFlight', 'IfcRailing', 'IfcTransportElement')),
    ('DON', 'Donatı ve armatür', ('IfcFurnishingElement', 'IfcFlowTerminal', 'IfcDistributionPort')),
    ('MEK', 'Mekânlar', ('IfcSpace',)),
    ('DIG', 'Diğer', ()),
]
DISC_CODES = [d[0] for d in DISCIPLINES]


def discipline_of(p):
    for code, _, classes in DISCIPLINES:
        if any(p.is_a(c) for c in classes):
            return code
    return 'DIG'


def H(tag: bytes, *parts: bytes) -> bytes:
    h = hashlib.sha256(); h.update(tag)
    for x in parts:
        h.update(len(x).to_bytes(4, 'big')); h.update(x)
    return h.digest()


def leaf_hash(record: str) -> bytes:
    return H(b'\x00', record.encode('utf-8'))


def node_hash(label: str, children) -> bytes:
    return H(b'\x01', label.encode('utf-8'), *children)


def is_dk(e):
    try:
        n = e.Name
    except Exception:
        return False
    return isinstance(n, str) and (n.startswith(DK_PREFIX) or n == DK_PSET)


_SETMASK = {}


def set_mask(e):
    t = e.is_a()
    m = _SETMASK.get(t)
    if m is None:
        decl = e.wrapped_data.declaration().as_entity()
        m = []
        for a in decl.all_attributes():
            at = a.type_of_attribute()
            m.append(hasattr(at, 'type_of_aggregation_string') and at.type_of_aggregation_string() == 'set')
        _SETMASK[t] = m
    return m


class Canon:
    def __init__(self, f):
        self.f = f
        self.memo = {}
        self.imperial = False
        for ua in f.by_type('IfcUnitAssignment'):
            for u in ua.Units:
                if getattr(u, 'UnitType', None) == 'LENGTHUNIT' and u.is_a('IfcConversionBasedUnit'):
                    self.imperial = (u.Name or '').upper() in ('FOOT', 'INCH', 'YARD')
        # uzunluk ve genel gerçek sayılar: kaba ızgara (imparatorluk 2^-10 ft ≈ 0,30 mm; metrik 1e-4 m)
        # yön kosinüsleri (IfcDirection, |x| <= 1): ince ızgara 2^-20
        self.q = float(2 ** 10) if self.imperial else 1e4
        self.q_dir = float(2 ** 20)
        self._qcur = self.q

    def val(self, v, decl_is_set=False):
        if isinstance(v, ifcopenshell.entity_instance):
            return self.ent(v)
        if isinstance(v, float):
            return 'r' + str(math.floor(v * self._qcur + Q_OFFSET))
        if isinstance(v, (tuple, list)):
            items = [self.val(x) for x in v]
            if decl_is_set:
                items.sort()
            return '(' + ','.join(items) + ')'
        if v is None:
            return '$'
        if isinstance(v, bool):
            return '.T.' if v else '.F.'
        if isinstance(v, int):
            return str(v)
        return repr(v)

    def ent(self, e):
        if e.is_a('IfcOwnerHistory'):
            return '*'
        if e.id() == 0:  # typed value e.g. IfcLabel('x')
            return e.is_a() + '(' + self.val(e.wrappedValue) + ')'
        gid = getattr(e, 'GlobalId', None) if e.is_a('IfcRoot') else None
        if gid:
            return '@' + gid
        k = e.id()
        m = self.memo.get(k)
        if m is not None:
            return m
        sets = set_mask(e)
        if e.is_a('IfcDirection'):
            self._qcur = self.q_dir
            out = e.is_a() + '(' + ','.join(self.val(x, sets[i]) for i, x in enumerate(e)) + ')'
            self._qcur = self.q
        else:
            out = e.is_a() + '(' + ','.join(self.val(x, sets[i]) for i, x in enumerate(e)) + ')'
        if len(out) > 256:  # uzun alt grafikleri özetle -> bellek kontrolü
            out = '~' + hashlib.sha256(out.encode()).hexdigest()[:32]
        self.memo[k] = out
        return out

    def body(self, e):
        """Köklenmiş nesnenin kendi içeriği (GlobalId referansı yerine)."""
        parts = []
        sets = set_mask(e)
        for i, x in enumerate(e):
            if e.attribute_name(i) == 'OwnerHistory':
                parts.append('*'); continue
            parts.append(self.val(x, sets[i]))
        return e.is_a() + '(' + ','.join(parts) + ')'


def element_record(c: Canon, p):
    """Bir ürünün kanonik kaydı: kendi gövdesi + özellik setleri + tipi + malzemesi."""
    rec = [c.body(p)]
    psets = []
    for r in getattr(p, 'IsDefinedBy', ()) or ():
        if r.is_a('IfcRelDefinesByProperties'):
            pd = r.RelatingPropertyDefinition
            if is_dk(pd):
                continue
            psets.append(c.body(pd) + '{' + ','.join(sorted(c.body(x) for x in getattr(pd, 'HasProperties', ()) or ())) + '}')
        elif r.is_a('IfcRelDefinesByType'):
            psets.append('TYPE@' + r.RelatingType.GlobalId)
    rec.append('P[' + '|'.join(sorted(psets)) + ']')
    mats = []
    for r in getattr(p, 'HasAssociations', ()) or ():
        if r.is_a('IfcRelAssociatesMaterial'):
            mats.append(c.ent(r.RelatingMaterial))
    rec.append('M[' + '|'.join(sorted(mats)) + ']')
    return '\n'.join(rec)


def storey_of(p, cache):
    k = p.id()
    if k in cache: return cache[k]
    s = None
    if p.is_a('IfcBuildingStorey'):
        s = p
    else:
        for r in getattr(p, 'ContainedInStructure', ()) or ():
            s = r.RelatingStructure; break
        if s is None:
            for r in getattr(p, 'Decomposes', ()) or ():
                s = storey_of(r.RelatingObject, cache); break
        if s is None:
            for r in getattr(p, 'VoidsElements', ()) or ():
                s = storey_of(r.RelatingBuildingElement, cache); break
        if s is None and p.is_a('IfcDistributionPort'):
            for r in getattr(p, 'ContainedIn', ()) or ():
                s = storey_of(r.RelatedElement, cache); break
        if s is not None and not s.is_a('IfcBuildingStorey'):
            s = None
    cache[k] = s
    return s


def build_tree(f):
    """Merkle ağacı: KÖK -> [MEKÂNSAL -> bina -> katlar -> disiplinler -> elemanlar,
                              MEKÂNSAL OLMAYAN -> tipler, malzemeler, proje]"""
    c = Canon(f)
    storeys = sorted(f.by_type('IfcBuildingStorey'), key=lambda s: (s.Elevation or 0, s.GlobalId))
    groups = {s.GlobalId: {d: [] for d in DISC_CODES} for s in storeys}
    bld_level = []
    cache = {}
    n = 0
    for p in f.by_type('IfcProduct'):
        if p.is_a('IfcSpatialStructureElement') and not p.is_a('IfcSpace'):
            continue
        if is_dk(p):
            continue
        s = storey_of(p, cache)
        lh = leaf_hash(element_record(c, p))
        n += 1
        if s is None:
            bld_level.append((p.GlobalId, lh))
        else:
            groups[s.GlobalId][discipline_of(p)].append((p.GlobalId, lh))
    tree = {'storeys': [], 'n_leaves': n}
    st_hashes = []
    for s in storeys:
        dnodes = {}
        for d in DISC_CODES:
            leaves = sorted(groups[s.GlobalId][d])
            dnodes[d] = {'n': len(leaves), 'hash': node_hash('D:' + d, [h for _, h in leaves]), 'leaves': leaves}
        sh = node_hash('S:' + c.body(s), [dnodes[d]['hash'] for d in DISC_CODES])
        tree['storeys'].append({'gid': s.GlobalId, 'name': s.Name, 'elev': s.Elevation, 'hash': sh, 'disc': dnodes})
        st_hashes.append(sh)
    bl = sorted(bld_level)
    bld = f.by_type('IfcBuilding')[0]
    bh_level = node_hash('BLD-LEVEL', [h for _, h in bl])
    spatial = node_hash('SPATIAL:' + c.body(bld) + '|' + c.body(f.by_type('IfcSite')[0]), [bh_level] + st_hashes)
    # mekânsal olmayan dal
    types = sorted((t.GlobalId, leaf_hash(c.body(t) + '{' + ','.join(sorted(c.body(x) + '{' + ','.join(sorted(c.body(y) for y in (getattr(x, 'HasProperties', ()) or ()))) + '}' for x in (t.HasPropertySets or ()) if not is_dk(x))) + '}'))
                   for t in f.by_type('IfcTypeObject'))
    mats = sorted(leaf_hash(c.ent(m)) for m in f.by_type('IfcMaterial'))
    proj = f.by_type('IfcProject')[0]
    proj_rec = c.body(proj)
    nonsp = node_hash('NONSPATIAL', [node_hash('TYPES', [h for _, h in types]), node_hash('MATERIALS', mats), leaf_hash(proj_rec)])
    root = node_hash('ROOT:' + C14N_VERSION, [spatial, nonsp])
    tree.update(root=root, spatial=spatial, nonspatial=nonsp, bld_level=bh_level, n_types=len(types), n_mats=len(mats), n_bld_level=len(bl))
    return tree


def chain_root(model_root: bytes, prev_root: bytes | None, rev: int) -> bytes:
    """Onarım kitabesi: revizyon kökü, model kökünü ve bir önceki revizyon kökünü bağlar."""
    return H(b'\x02', model_root, prev_root or b'\x00' * 32, rev.to_bytes(4, 'big'))


def diff(t1, t2):
    out = []
    for a, b in zip(t1['storeys'], t2['storeys']):
        if a['hash'] != b['hash']:
            dd = [d for d in DISC_CODES if a['disc'][d]['hash'] != b['disc'][d]['hash']]
            changed = []
            for d in dd:
                la = dict(a['disc'][d]['leaves']); lb = dict(b['disc'][d]['leaves'])
                for g in set(la) | set(lb):
                    if la.get(g) != lb.get(g):
                        changed.append((d, g, 'eklendi' if g not in la else 'silindi' if g not in lb else 'değişti'))
            out.append((a['name'], dd, changed))
    return out

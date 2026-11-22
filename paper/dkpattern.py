"""Dijital Kitabe - desen üreticisi.

Aile A  'Yıldız rozeti' (yıldız-çokgen ailesi; Levha XIV, XXVII-1/2, XXV düzen ilkesi)
   merkez sekiz kollu yıldız  -> Merkle kökü
   16 yapraklı taç           -> Merkle kökü (ek bitler)
   18 kat sektörü            -> kat düğümleri (kot sırasıyla, saat yönünde, tepeden)
   18 x 8 dış hücre          -> kat x disiplin düğümleri
   4 köşelik (köşe dolgusu)  -> mekânsal olmayan dal (tipler, malzemeler, proje)
Aile B  'Altıgen örgü' (Levha XII, XX, XXXIII): satır = kat, sütun = disiplin.

Kodlama sürümleri (bit akışı her ikisinde de SHA-256(düğüm özeti || aile || bölge)):
  DK-ENC-1.0  ilk sürüm: sekiz kollu merkez, 16 yaprak, kat sayısı kadar sektör, 3-5-6-8 mertebeli motifler
              (yıldız rozetinin simetri kuralını bozar; yalnızca karşılaştırma için tutulur: rosette_v10).
  DK-ENC-1.1  güncel sürüm: on iki kollu merkez (C12), 24 yapraklı taç, S = max(24, 12*ceil(N/12)) sektör,
              yalnızca 6 ve 12 mertebeli motifler; katı olmayan sektörler nötr altı kollu yıldızı taşır.
Kat ve hücre kanallarının bitleri iki sürümde aynıdır; yalnızca çizim değişir.
"""
import hashlib, math
import numpy as np

ENC_VERSION = 'DK-ENC-1.1'

# Selçuklu çini paletinden esinli, parlaklık farkı yüksek 4 renk + nötr
PALETTE = ['#173d7a', '#2a9d9a', '#e0a526', '#b5452c']  # lacivert, firuze, aşı sarısı, kiremit
PAL_NAMES = ['lacivert', 'firuze', 'aşı sarısı', 'kiremit']
INK = '#141414'
PAPER = '#f6f1e6'
EMPTY = '#e7e1d3'


class Bits:
    def __init__(self, h: bytes, label: str):
        self.buf = b''
        i = 0
        while len(self.buf) < 64:
            self.buf += hashlib.sha256(h + label.encode() + bytes([i])).digest(); i += 1
        self.v = int.from_bytes(self.buf, 'big'); self.pos = 0

    def take(self, nbits):
        x = (self.v >> self.pos) & ((1 << nbits) - 1); self.pos += nbits; return x


def star(cx, cy, r_out, r_in, n, rot):
    pts = []
    for k in range(2 * n):
        r = r_out if k % 2 == 0 else r_in
        a = rot + math.pi * k / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def ngon(cx, cy, r, n, rot):
    return [(cx + r * math.cos(rot + 2 * math.pi * k / n), cy + r * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]


def annular(r0, r1, a0, a1, steps=8):
    pts = [(r0 * math.cos(a), r0 * math.sin(a)) for a in np.linspace(a0, a1, steps)]
    pts += [(r1 * math.cos(a), r1 * math.sin(a)) for a in np.linspace(a1, a0, steps)]
    return pts


def ang(i, n):
    """Tepeden (90°) başlayıp saat yönünde ilerleyen sektör açıları."""
    w = 2 * math.pi / n
    a1 = math.pi / 2 - i * w
    return a1 - w, a1


# ---------------------------------------------------------------- Aile A
def rosette_v10(tree, family='A'):
    """DK-ENC-1.0 (ilk sürüm). Döndürür: list of dict(poly, fill, region, lw, z, order)"""
    P = []
    def add(poly, fill, region, lw=0.6, z=1, order=None):
        P.append(dict(poly=poly, fill=fill, region=region, lw=lw, z=z, order=order))

    root = tree['root']; ns = tree['nonspatial']
    # çerçeve (kitabe levhası)
    add([(-1.18, -1.18), (1.18, -1.18), (1.18, 1.18), (-1.18, 1.18)], PAPER, 'frame', lw=1.6, z=0)
    # köşelikler -> mekânsal olmayan dal
    b = Bits(ns, 'A/corner')
    for q, (sx, sy) in enumerate([(1, 1), (-1, 1), (-1, -1), (1, -1)]):
        col = PALETTE[b.take(2)]; var = b.take(2)
        cx, cy = sx * 1.02, sy * 1.02
        rot = math.pi / 8 * var
        add(star(cx, cy, 0.13, 0.065, 8, rot), col, 'nonspatial', z=2)
        add(ngon(cx, cy, 0.04 + 0.012 * var, 8, rot), PAPER, 'nonspatial', z=3)
    add(ngon(0, 0, 1.0, 120, 0), PAPER, 'disc-bg', lw=1.2, z=0.5)

    storeys = tree['storeys']; N = len(storeys)
    codes = list(storeys[0]['disc'].keys())
    # dış halka: kat x disiplin (4 radyal sıra x 2 açısal sütun)
    r_in, r_out = 0.655, 0.985
    for i, s in enumerate(storeys):
        a0, a1 = ang(i, N)
        for j, d in enumerate(codes):
            row, colm = j // 2, j % 2
            rr0 = r_in + (r_out - r_in) * row / 4; rr1 = r_in + (r_out - r_in) * (row + 1) / 4
            aa0 = a0 + (a1 - a0) * colm / 2; aa1 = a0 + (a1 - a0) * (colm + 1) / 2
            node = s['disc'][d]
            reg = f'disc:{i}:{d}'
            if node['n'] == 0:
                add(annular(rr0, rr1, aa0, aa1, 5), EMPTY, reg, lw=0.35)
                continue
            bb = Bits(node['hash'], 'A/disc')
            col = PALETTE[bb.take(2)]; chi = bb.take(1)
            add(annular(rr0, rr1, aa0, aa1, 5), col, reg, lw=0.35)
            # içte eşkenar dörtgen; kiralite = hangi köşeye yaslandığı
            rm = (rr0 + rr1) / 2; am = (aa0 + aa1) / 2; da = (aa1 - aa0) / 2 * 0.62; dr = (rr1 - rr0) / 2 * 0.62
            sh = (1 if chi else -1) * da * 0.45
            dia = [(rm + dr) * math.cos(am + sh), (rm + dr) * math.sin(am + sh)], [rm * math.cos(am + da), rm * math.sin(am + da)], \
                  [(rm - dr) * math.cos(am - sh), (rm - dr) * math.sin(am - sh)], [rm * math.cos(am - da), rm * math.sin(am - da)]
            add([tuple(p) for p in dia], PAPER, reg, lw=0.3, z=2)

    # kat halkası
    r0, r1 = 0.335, 0.635
    for i, s in enumerate(storeys):
        a0, a1 = ang(i, N)
        bb = Bits(s['hash'], 'A/storey')
        col = PALETTE[bb.take(2)]; var = bb.take(2); chi = bb.take(1)
        reg = f'storey:{i}'
        add(annular(r0, r1, a0, a1, 8), PAPER, reg, lw=0.6)
        am = (a0 + a1) / 2; rm = (r0 + r1) / 2 + 0.01
        cx, cy = rm * math.cos(am), rm * math.sin(am)
        rad = 0.072
        rot = am + (0.18 if chi else -0.18)
        if var == 0:      # altı kollu yıldız
            add(star(cx, cy, rad, rad * 0.55, 6, rot), col, reg, z=2, order=6)
        elif var == 1:    # sekiz kollu yıldız
            add(star(cx, cy, rad, rad * 0.62, 8, rot), col, reg, z=2, order=8)
        elif var == 2:    # altıgen içinde fırıldak (kiral)
            add(ngon(cx, cy, rad, 6, rot), col, reg, z=2, order=3)
            for k in range(3):
                a = rot + 2 * math.pi * k / 3
                tri = [(cx, cy), (cx + rad * math.cos(a), cy + rad * math.sin(a)),
                       (cx + rad * 0.62 * math.cos(a + (0.9 if chi else -0.9)), cy + rad * 0.62 * math.sin(a + (0.9 if chi else -0.9)))]
                add(tri, PAPER, reg, lw=0.3, z=3)
        else:             # beş kollu yıldız + merkez
            add(star(cx, cy, rad, rad * 0.45, 5, rot), col, reg, z=2, order=5)
        # radyal kenarlarda yarım yıldız uçları (desen sürekliliği)
        rr = r0 + 0.035
        add(ngon(rr * math.cos(am), rr * math.sin(am), 0.016, 4, am), col, reg, lw=0.3, z=2)

    # taç: 16 yaprak -> kök
    bb = Bits(root, 'A/crown')
    for k in range(16):
        a = math.pi / 2 - 2 * math.pi * k / 16
        w = math.pi / 16
        pet = [(0.205 * math.cos(a - w), 0.205 * math.sin(a - w)), (0.318 * math.cos(a), 0.318 * math.sin(a)),
               (0.205 * math.cos(a + w), 0.205 * math.sin(a + w)), (0.17 * math.cos(a), 0.17 * math.sin(a))]
        add(pet, PALETTE[bb.take(2)], 'root', lw=0.5, z=2)
    # merkez sekiz kollu yıldız -> kök
    bb = Bits(root, 'A/center')
    col = PALETTE[bb.take(2)]; var = bb.take(2); rot = math.pi / 2 + (math.pi / 8 if bb.take(1) else 0)
    add(star(0, 0, 0.2, 0.2 * 0.62, 8, rot), col, 'root', lw=0.8, z=3, order=8)
    if var == 0: add(ngon(0, 0, 0.07, 8, rot), PAPER, 'root', z=4)
    elif var == 1: add(ngon(0, 0, 0.05, 60, 0), PAPER, 'root', z=4)
    elif var == 2: add(star(0, 0, 0.09, 0.05, 8, rot + math.pi / 8), PAPER, 'root', z=4)
    else: add(ngon(0, 0, 0.08, 4, rot), PAPER, 'root', z=4)
    return P


def n_sectors(N):
    """DK-ENC-1.1: sektör sayısı merkez mertebesinin (12) katıdır ve en az 24'tür."""
    return max(24, 12 * math.ceil(N / 12))


def rosette(tree, family='A'):
    """DK-ENC-1.1. Döndürür: list of dict(poly, fill, region, lw, z, order)"""
    P = []
    def add(poly, fill, region, lw=0.6, z=1, order=None):
        P.append(dict(poly=poly, fill=fill, region=region, lw=lw, z=z, order=order))

    root = tree['root']; ns = tree['nonspatial']
    add([(-1.18, -1.18), (1.18, -1.18), (1.18, 1.18), (-1.18, 1.18)], PAPER, 'frame', lw=1.6, z=0)
    # köşelikler -> mekânsal olmayan dal (on iki kollu yıldız; renk 2 + dolgu 2 bit)
    b = Bits(ns, 'A/corner')
    for q, (sx, sy) in enumerate([(1, 1), (-1, 1), (-1, -1), (1, -1)]):
        col = PALETTE[b.take(2)]; var = b.take(2)
        cx, cy = sx * 1.02, sy * 1.02
        add(star(cx, cy, 0.13, 0.075, 6, math.pi / 2), col, 'nonspatial', z=2, order=6)
        inner = [ngon(cx, cy, 0.05, 6, math.pi / 2), ngon(cx, cy, 0.045, 12, math.pi / 2),
                 star(cx, cy, 0.055, 0.03, 6, math.pi / 2 + math.pi / 6), ngon(cx, cy, 0.04, 60, 0)][var]
        add(inner, PAPER, 'nonspatial', z=3, order=[6, 12, 6, 12][var])
    add(ngon(0, 0, 1.0, 120, 0), PAPER, 'disc-bg', lw=1.2, z=0.5)

    storeys = tree['storeys']; N = len(storeys); S = n_sectors(N)
    codes = list(storeys[0]['disc'].keys())
    r_in, r_out = 0.655, 0.985
    for i in range(S):
        a0, a1 = ang(i, S)
        for j, d in enumerate(codes):
            row, colm = j // 2, j % 2
            rr0 = r_in + (r_out - r_in) * row / 4; rr1 = r_in + (r_out - r_in) * (row + 1) / 4
            aa0 = a0 + (a1 - a0) * colm / 2; aa1 = a0 + (a1 - a0) * (colm + 1) / 2
            if i >= N:
                add(annular(rr0, rr1, aa0, aa1, 5), EMPTY, f'reserved:{i}', lw=0.35); continue
            node = storeys[i]['disc'][d]; reg = f'disc:{i}:{d}'
            if node['n'] == 0:
                add(annular(rr0, rr1, aa0, aa1, 5), EMPTY, reg, lw=0.35); continue
            bb = Bits(node['hash'], 'A/disc')
            col = PALETTE[bb.take(2)]; chi = bb.take(1)
            add(annular(rr0, rr1, aa0, aa1, 5), col, reg, lw=0.35)
            rm = (rr0 + rr1) / 2; am = (aa0 + aa1) / 2; da = (aa1 - aa0) / 2 * 0.62; dr = (rr1 - rr0) / 2 * 0.62
            sh = (1 if chi else -1) * da * 0.45
            dia = [(rm + dr) * math.cos(am + sh), (rm + dr) * math.sin(am + sh)], [rm * math.cos(am + da), rm * math.sin(am + da)], \
                  [(rm - dr) * math.cos(am - sh), (rm - dr) * math.sin(am - sh)], [rm * math.cos(am - da), rm * math.sin(am - da)]
            add([tuple(p) for p in dia], PAPER, reg, lw=0.3, z=2)

    # kat halkası: motif varyantı (2 bit) yalnızca 6 ve 12 mertebeli; dönüş (1 bit) = 15°
    r0, r1 = 0.335, 0.635
    for i in range(S):
        a0, a1 = ang(i, S)
        am = (a0 + a1) / 2; rm = (r0 + r1) / 2 + 0.01
        cx, cy = rm * math.cos(am), rm * math.sin(am); rad = 0.055
        if i >= N:
            reg = f'reserved:{i}'
            add(annular(r0, r1, a0, a1, 8), PAPER, reg, lw=0.6)
            add(star(cx, cy, rad, rad * 0.55, 6, am), EMPTY, reg, z=2, order=6)
            continue
        bb = Bits(storeys[i]['hash'], 'A/storey')
        col = PALETTE[bb.take(2)]; var = bb.take(2); chi = bb.take(1)
        reg = f'storey:{i}'
        add(annular(r0, r1, a0, a1, 8), PAPER, reg, lw=0.6)
        rot = am + (math.pi / 12 if chi else 0)
        if var == 0:      # altı kollu yıldız
            add(star(cx, cy, rad, rad * 0.55, 6, rot), col, reg, z=2, order=6)
        elif var == 1:    # sivri altı kollu yıldız
            add(star(cx, cy, rad, rad * 0.36, 6, rot), col, reg, z=2, order=6)
        elif var == 2:    # altıgen içinde altı kollu yıldız
            add(ngon(cx, cy, rad, 6, rot), col, reg, z=2, order=6)
            add(star(cx, cy, rad * 0.8, rad * 0.45, 6, rot + math.pi / 6), PAPER, reg, lw=0.3, z=3, order=6)
        else:             # on iki kollu yıldız
            add(star(cx, cy, rad, rad * 0.72, 12, rot), col, reg, z=2, order=12)

    # taç: 24 yaprak -> kök (2 bit renk)
    bb = Bits(root, 'A/crown')
    for k in range(24):
        a = math.pi / 2 - 2 * math.pi * k / 24; w = math.pi / 24
        pet = [(0.205 * math.cos(a - w), 0.205 * math.sin(a - w)), (0.318 * math.cos(a), 0.318 * math.sin(a)),
               (0.205 * math.cos(a + w), 0.205 * math.sin(a + w)), (0.17 * math.cos(a), 0.17 * math.sin(a))]
        add(pet, PALETTE[bb.take(2)], 'root', lw=0.5, z=2)
    # merkez on iki kollu yıldız -> kök (renk 2 + dolgu 2 + dönüş 1 bit)
    bb = Bits(root, 'A/center')
    col = PALETTE[bb.take(2)]; var = bb.take(2); rot = math.pi / 2 + (math.pi / 12 if bb.take(1) else 0)
    add(star(0, 0, 0.2, 0.2 * 0.72, 12, rot), col, 'root', lw=0.8, z=3, order=12)
    if var == 0: add(ngon(0, 0, 0.08, 12, rot), PAPER, 'root', z=4, order=12)
    elif var == 1: add(ngon(0, 0, 0.06, 60, 0), PAPER, 'root', z=4, order=12)
    elif var == 2: add(star(0, 0, 0.1, 0.06, 12, rot + math.pi / 12), PAPER, 'root', z=4, order=12)
    else: add(ngon(0, 0, 0.09, 3, rot), PAPER, 'root', z=4, order=3)
    return P


def capacity_A_v10(tree):
    N = len(tree['storeys']); nonempty = sum(1 for s in tree['storeys'] for d in s['disc'].values() if d['n'])
    return dict(root=5 + 32, storey=N * 5, disc=nonempty * 3, nonspatial=4 * 4,
                total=5 + 32 + N * 5 + nonempty * 3 + 16)


def capacity_A(tree):
    N = len(tree['storeys']); nonempty = sum(1 for s in tree['storeys'] for d in s['disc'].values() if d['n'])
    return dict(root=5 + 48, storey=N * 5, disc=nonempty * 3, nonspatial=4 * 4,
                total=5 + 48 + N * 5 + nonempty * 3 + 16, sectors=n_sectors(N), nonempty_cells=nonempty)


# ---------------------------------------------------------------- Aile B
def hexlattice(tree):
    P = []
    def add(poly, fill, region, lw=0.5, z=1):
        P.append(dict(poly=poly, fill=fill, region=region, lw=lw, z=z))
    storeys = tree['storeys']; codes = list(storeys[0]['disc'].keys())
    R = 1.0; w = math.sqrt(3) * R
    def hexc(col, row):
        return (col * w + (w / 2 if row % 2 else 0), -row * 1.5 * R)
    def tile(cx, cy, h, label, region, empty=False):
        if empty:
            add(ngon(cx, cy, R, 6, math.pi / 6), EMPTY, region, lw=0.4); return
        bb = Bits(h, 'B/' + label)
        c1 = PALETTE[bb.take(2)]; chi = bb.take(1)
        add(ngon(cx, cy, R, 6, math.pi / 6), PAPER, region, lw=0.5)
        # Y-örgü / fırıldak: 3 kanat, kiralite
        for k in range(3):
            a = math.pi / 6 + 2 * math.pi * k / 3
            s = 1 if chi else -1
            p = [(cx, cy), (cx + R * math.cos(a), cy + R * math.sin(a)),
                 (cx + R * math.cos(a + s * math.pi / 3), cy + R * math.sin(a + s * math.pi / 3)),
                 (cx + 0.5 * R * math.cos(a + s * math.pi / 3), cy + 0.5 * R * math.sin(a + s * math.pi / 3))]
            add(p, c1, region, lw=0.4, z=2)
    # başlık satırı: kök (10 altıgen)
    for k in range(10):
        cx, cy = hexc(k, 0)
        tile(cx, cy, tree['root'] + bytes([k]), 'root', 'root')
    for i, s in enumerate(storeys):
        row = i + 1
        cx, cy = hexc(0, row); tile(cx, cy, s['hash'], 'storey', f'storey:{i}')
        for j, d in enumerate(codes):
            cx, cy = hexc(j + 1, row)
            node = s['disc'][d]
            tile(cx, cy, node['hash'], 'disc', f'disc:{i}:{d}', empty=node['n'] == 0)
        cx, cy = hexc(9, row); tile(cx, cy, tree['nonspatial'] + bytes([i]), 'ns', 'nonspatial')
    return P


def draw(ax, P, highlight=None, dim_others=False):
    from matplotlib.patches import Polygon
    for p in sorted(P, key=lambda q: q['z']):
        fc = p['fill']
        alpha = 1.0
        if highlight is not None and dim_others and p['region'] not in highlight and p['region'] not in ('frame', 'disc-bg'):
            alpha = 0.25
        ax.add_patch(Polygon(p['poly'], closed=True, fc=fc, ec=INK, lw=p['lw'], alpha=alpha, joinstyle='round'))
    xs = [x for p in P for x, _ in p['poly']]; ys = [y for p in P for _, y in p['poly']]
    pad = 0.04 * (max(xs) - min(xs))
    ax.set_xlim(min(xs) - pad, max(xs) + pad); ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_aspect('equal'); ax.axis('off')


def region_signature(P):
    """Bölge -> görsel imza (renk + geometri yuvarlanmış) : değişen bölgeleri bulmak için."""
    sig = {}
    for p in P:
        key = p['region']
        sig.setdefault(key, []).append((p['fill'], tuple((round(x, 4), round(y, 4)) for x, y in p['poly'])))
    return {k: hashlib.sha1(repr(v).encode()).hexdigest() for k, v in sig.items()}


def to_svg(P, path, size=800):
    xs = [x for p in P for x, _ in p['poly']]; ys = [y for p in P for _, y in p['poly']]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    s = size / max(x1 - x0, y1 - y0)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">']
    for p in sorted(P, key=lambda q: q['z']):
        pts = ' '.join(f'{(x - x0) * s:.2f},{(y1 - y) * s:.2f}' for x, y in p['poly'])
        out.append(f'<polygon points="{pts}" fill="{p["fill"]}" stroke="{INK}" stroke-width="{p["lw"] * 1.2:.2f}" data-region="{p["region"]}"/>')
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out))


def load_tree_json(path):
    """Merkle tree saved by experiments.py (results/merkle_tree_rev*.json) -> tree dict with bytes digests."""
    import json
    t = json.load(open(path)); b = bytes.fromhex
    t['root'], t['spatial'], t['nonspatial'] = b(t['root']), b(t['spatial']), b(t['nonspatial'])
    for s in t['storeys']:
        s['hash'] = b(s['hash'])
        for d in s['disc'].values(): d['hash'] = b(d['hash'])
    return t


def kitabe_layout(rev):
    """Giriş kapısı yerel koordinatlarında (ft) levha ölçeği ve merkezi.
    Rev0: 1,8 m'lik ana levha, kapı üstündeki saçak (kitabe) bandı hizasında, portik önünde (≈2 m).
    Revk: ana levhanın sağında sıralanan küçük onarım kitabeleri."""
    s0 = 0.9 / 0.3048 / 1.18
    if rev == 0:
        return s0, (3.2, 6.6, 14.5)
    return s0 * 0.32, (3.2 - (4.4 + (rev - 1) * 2.1), 6.6, 12.5)

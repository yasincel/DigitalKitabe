"""PIL tabanlı ressam algoritmasıyla aksonometrik model görüntüleri."""
import sys, pickle, json, math
import os as _os; HERE = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import dkpattern as dp, dkcore

OUT = _os.path.join(HERE, 'out'); FIG = _os.path.join(HERE, 'figures')
CAT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
DCOL = {c: CAT[i] for i, c in enumerate(dkcore.DISC_CODES)}
G = pickle.load(open(f'{OUT}/geom.pkl', 'rb'))
R = json.load(open(f'{OUT}/results.json'))
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def hex2rgb(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def camera(az, el):
    az, el = math.radians(az), math.radians(el)
    d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])  # göze doğru
    right = np.cross([0, 0, 1], d); right /= np.linalg.norm(right)
    up = np.cross(d, right)
    return d, right, up


def render(path, az=-60, el=28, W=2400, H=1700, colour=None, focus=None, zoom=1.0, extra_polys=(), labels=(), skip_cls=(), ss=2, ontop=()):
    d, right, up = camera(az, el)
    light = np.array([0.4, -0.6, 0.75]); light /= np.linalg.norm(light)
    polys = []
    allv = []
    for o in G:
        if o['cls'] in skip_cls: continue
        v = o['v'].astype(float); f = o['f']
        if len(f) == 0: continue
        tri = v[f]  # (n,3,3)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(n, axis=1); ok = ln > 1e-9
        tri = tri[ok]; n = n[ok] / ln[ok, None]
        base = colour(o) if colour else hex2rgb(DCOL[o['disc']])
        if base is None: continue
        sh = 0.55 + 0.45 * np.abs(n @ light)
        depth = tri.mean(1) @ d
        if o['gid'] in ontop: depth = depth + 1e7
        polys.append((tri, depth, sh, base))
        allv.append(tri.reshape(-1, 3))
    allv = np.concatenate(allv)
    P2 = lambda X: np.stack([X @ right, X @ up], -1)
    xy = P2(allv)
    if focus is not None:
        c = P2(np.array(focus)); sy = (xy.max(0) - xy.min(0)).max() / zoom
        half = np.array([sy * W / H, sy]) / 2
        lo = c - half; hi = c + half
    else:
        lo, hi = xy.min(0), xy.max(0)
        pad = 0.03 * (hi - lo); lo -= pad; hi += pad
    sc = min(W * ss / (hi[0] - lo[0]), H * ss / (hi[1] - lo[1]))
    ox = (W * ss - sc * (hi[0] - lo[0])) / 2; oy = (H * ss - sc * (hi[1] - lo[1])) / 2
    def to_px(X):
        q = P2(X)
        return np.stack([ox + (q[..., 0] - lo[0]) * sc, H * ss - (oy + (q[..., 1] - lo[1]) * sc)], -1)
    tri = np.concatenate([p[0] for p in polys]); depth = np.concatenate([p[1] for p in polys])
    col = np.concatenate([np.clip(p[3][None, :] * p[2][:, None], 0, 255) for p in polys])
    for ep in extra_polys:  # (pts3d, rgb, outline)
        pass
    order = np.argsort(depth)
    px = to_px(tri)
    img = Image.new('RGB', (W * ss, H * ss), (255, 255, 255)); dr = ImageDraw.Draw(img)
    # ekstra çokgenleri derinliğe göre araya yerleştir
    gd = float(np.mean(np.concatenate([np.array(pts) for pts, _, _ in extra_polys]) @ d)) if extra_polys else 0
    ex = [(gd, pts, rgb, oc) for pts, rgb, oc in extra_polys]; ei = 0
    for k in order:
        while ei < len(ex) and ex[ei][0] < depth[k]:
            _, pts, rgb, oc = ex[ei]; q = to_px(np.array(pts))
            dr.polygon([tuple(x) for x in q], fill=rgb, outline=oc); ei += 1
        c = tuple(int(x) for x in col[k])
        dr.polygon([tuple(x) for x in px[k]], fill=c, outline=c)
    for _, pts, rgb, oc in ex[ei:]:
        q = to_px(np.array(pts)); dr.polygon([tuple(x) for x in q], fill=rgb, outline=oc)
    img = img.resize((W, H), Image.LANCZOS)
    dr = ImageDraw.Draw(img)
    for li, (pt3, text) in enumerate(labels):
        q = to_px(np.array([pt3]))[0] / ss
        fnt = ImageFont.truetype(FONT, 34)
        dy = -160 - 90 * li
        tw = dr.textlength(text, font=fnt)
        dx = 80 if li % 2 == 0 else -80
        tx = q[0] + dx + (8 if dx > 0 else -tw - 8)
        dr.line([tuple(q), (q[0] + dx, q[1] + dy)], fill=(208, 28, 28), width=4)
        dr.ellipse([q[0] - 26, q[1] - 26, q[0] + 26, q[1] + 26], outline=(208, 28, 28), width=5)
        tb = dr.textbbox((tx, q[1] + dy - 40), text, font=fnt)
        dr.rectangle([tb[0] - 8, tb[1] - 6, tb[2] + 8, tb[3] + 6], fill=(255, 255, 255), outline=(208, 28, 28), width=2)
        dr.text((tx, q[1] + dy - 40), text, fill=(20, 20, 20), font=fnt)
    img.save(path)
    return img


def legend(img, items, path, title=None):
    W, H = img.size
    pad = 70 + 50 * ((len(items) + 3) // 4)
    canvas = Image.new('RGB', (W, H + pad), 'white'); canvas.paste(img, (0, 0))
    dr = ImageDraw.Draw(canvas); fnt = ImageFont.truetype(FONT, 30)
    for i, (c, t) in enumerate(items):
        x = 60 + (i % 4) * (W - 120) // 4; y = H + 20 + (i // 4) * 50
        dr.rounded_rectangle([x, y, x + 34, y + 34], 6, fill=c); dr.text((x + 48, y), t, fill=(40, 40, 40), font=fnt)
    canvas.save(path)


if __name__ == '__main__':
    names = {c: n for c, n, _ in dkcore.DISCIPLINES}
    if 'en' in sys.argv:
        names = {'YAP': 'STR · Structure and slabs', 'DUV': 'WAL · Walls', 'CEP': 'FAC · Facade and windows', 'ACK': 'OPN · Doors and openings', 'DOL': 'CIR · Circulation', 'DON': 'FUR · Furnishing and fixtures', 'MEK': 'SPC · Spaces', 'DIG': 'OTH · Other'}
    skip = ('IfcFurnishingElement',)
    if 'm3d' in sys.argv:
        img = render(f'{FIG}/F_model3d.png', skip_cls=())
        img.save(f'{FIG}/Fig02_model3d_nolegend.png')
        legend(img, [(DCOL[c], names[c] if 'en' in sys.argv else f'{c} · {names[c]}') for c in dkcore.DISC_CODES], f'{FIG}/F_model3d.png')
        print('model3d ok', flush=True)
    # revizyonlarda değişen elemanlar
    chg = {r['gid']: r['rev'] for r in R['revisions'] if r['rev'] <= 3}
    hl = {1: (208, 28, 28), 2: (23, 61, 122), 3: (224, 165, 38)}
    def col(o):
        if o['gid'] in chg: return np.array(hl[chg[o['gid']]], float) / 0.9
        return np.array([214, 212, 205], float)
    if 'door' in sys.argv:  # door-mounted placement of an earlier draft; not used in the article
        # kitabe levhası (Rev0) dünya koordinatlarında
        import pickle as pk
        t0 = pk.load(open(f'{OUT}/tree_rev0.pkl', 'rb'))
        e = R['entrance']; O = np.array(e['origin']); X = np.array(e['x']); Z = np.array([0, 0, 1.0]); Y = np.cross(Z, X)
        s = 0.9 / 0.3048 / 1.18
        def W(x, y, rev=0):
            sc, (ox, oy, oz) = dp.kitabe_layout(rev)
            return (O + X * (ox + x * sc) + Y * oy + Z * (oz + y * sc)) * 0.3048
        ex = []
        for rv in range(5):
            tk = pk.load(open(f'{OUT}/tree_rev{rv}.pkl', 'rb'))
            for p in sorted(dp.rosette(tk), key=lambda q: q['z']):
                rgb = tuple(int(p['fill'][i:i + 2], 16) for i in (1, 3, 5))
                ex.append(([W(x, y, rv) for x, y in p['poly']], rgb, (20, 20, 20)))
        # ressam algoritması derinliği: aynı düzlemdeki çokgenler z sırasına göre
    gids_present = {o['gid'] for o in G}
    lab = []
    if 'rev' in sys.argv:
        labs = []
        names_r = {1: 'Rev1: L3 kapısı (0,50 m)', 2: 'Rev2: L4 duvarı (Pset)', 3: 'Rev3: L2 tezgâh (silindi)'}
        if 'en' in sys.argv: names_r = {1: 'Rev1: door on L3 (0.50 m)', 2: 'Rev2: wall on L4 (Pset)', 3: 'Rev3: counter top on L2 (deleted)'}
        for o in G:
            if o['gid'] in chg:
                labs.append((o['v'].astype(float).mean(0), names_r[chg[o['gid']]]))
        img = render(f'{FIG}/F_model_revizyon.png', colour=col, labels=labs, az=-60, el=28, ontop=set(chg))
        print('rev ok', flush=True)
    if 'door' in sys.argv:  # door-mounted placement of an earlier draft; not used in the article
        # giriş cephesi yakın görünüm + kitabe
        img = render(f'{FIG}/F_giris_kitabe.png', colour=lambda o: np.array([226, 222, 212.]) if o['disc'] != 'ACK' else np.array([200, 190, 170.]), focus=W(-1.6, -1.2), zoom=5.0, extra_polys=ex, az=-62, el=10, W=4000, H=3000)
        print('entrance ok', flush=True)

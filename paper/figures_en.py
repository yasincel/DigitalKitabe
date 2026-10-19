import sys, pickle, json, math
import os as _os; HERE = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch, Circle, Wedge
import dkpattern as dp, dkcore

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': '#8a8984',
                     'axes.labelcolor': '#52514e', 'xtick.color': '#52514e', 'ytick.color': '#52514e'})
OUT = _os.path.join(HERE, 'out'); FIG = _os.path.join(HERE, 'figures')
CAT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
EN = {'YAP': 'STR', 'DUV': 'WAL', 'CEP': 'FAC', 'ACK': 'OPN', 'DOL': 'CIR', 'DON': 'FUR', 'MEK': 'SPC', 'DIG': 'OTH'}
DNAME = {'YAP': 'Structure and slabs', 'DUV': 'Walls', 'CEP': 'Facade and windows', 'ACK': 'Doors and openings', 'DOL': 'Circulation', 'DON': 'Furnishing and fixtures', 'MEK': 'Spaces', 'DIG': 'Other'}
T = [pickle.load(open(f'{OUT}/tree_rev{k}.pkl', 'rb')) for k in range(5)]
R = json.load(open(f'{OUT}/results.json'))
base = T[0]; codes = dkcore.DISC_CODES; N = len(base['storeys'])
TXT1, TXT2 = '#0b0b0b', '#52514e'


def save(fig, name, dpi=400):
    fig.savefig(f'{FIG}/{name}.png', dpi=dpi, bbox_inches='tight', facecolor='white'); plt.close(fig)


# ---------------------------------------------------------------- Şekil: kat x disiplin dağılımı
def fig_distribution():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    names = [s['name'] for s in base['storeys']]
    left = np.zeros(N)
    for j, d in enumerate(codes):
        v = np.array([s['disc'][d]['n'] for s in base['storeys']])
        ax.barh(range(N), v, left=left, color=CAT[j], edgecolor='white', linewidth=1.0, height=0.72, label=f'{EN[d]} · {DNAME[d]}')
        left += v
    for i, t in enumerate(left):
        ax.text(t + 12, i, f'{int(t)}', va='center', fontsize=7.5, color=TXT2)
    ax.set_yticks(range(N)); ax.set_yticklabels(names, fontsize=7.5); ax.invert_yaxis()
    ax.set_xlabel('Number of Merkle leaves (elements)')
    ax.spines[['top', 'right']].set_visible(False); ax.grid(axis='x', color='#e6e5e0', lw=0.6); ax.set_axisbelow(True)
    ax.legend(fontsize=7, frameon=False, loc='lower right', ncol=2)
    save(fig, 'Fig03_distribution')


# ---------------------------------------------------------------- Şekil: Merkle ağacı (örnek dal)
def fig_merkle():
    fig, ax = plt.subplots(figsize=(7.4, 4.2)); ax.axis('off'); ax.set_xlim(-4, 102); ax.set_ylim(0, 64)
    def box(x, y, w, h, t1, t2, fc='#f6f5f1', ec='#8a8984', bold=False):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle='round,pad=0.3,rounding_size=1.2', fc=fc, ec=ec, lw=0.9))
        ax.text(x, y + 1.1, t1, ha='center', va='center', fontsize=7.6, color=TXT1, weight='bold' if bold else 'normal')
        ax.text(x, y - 1.6, t2, ha='center', va='center', fontsize=6.4, color=TXT2, family='DejaVu Sans Mono')
    def ln(x0, y0, x1, y1): ax.plot([x0, x1], [y0, y1], color='#b5b4ae', lw=0.8, zorder=0)
    h = lambda b: b.hex()[:10] + '…'
    box(50, 54, 30, 6, f'ROOT  ({dkcore.C14N_VERSION})', h(base['root']), fc='#e3eefb', ec='#2a78d6', bold=True)
    box(28, 43, 28, 6, 'Spatial branch', h(base['spatial'])); box(76, 43, 30, 6, 'Non-spatial branch', h(base['nonspatial']))
    ln(50, 51, 28, 46); ln(50, 51, 76, 46)
    box(76, 31, 30, 6, f"Types ({base['n_types']}) · Materials ({base['n_mats']})", 'IfcTypeObject, IfcMaterial'); ln(76, 40, 76, 34)
    sts = [base['storeys'][i] for i in (0, 6, 7, 17)]
    xs = [6, 20, 34, 48]
    for x, s in zip(xs, sts):
        box(x, 31, 13, 6, s['name'][:12], h(s['hash'])[:8] + '…'); ln(28, 40, x, 34)
    ax.text(41, 31, '…', fontsize=12, ha='center', va='center', color=TXT2)
    ax.text(27, 25.2, f'{N} storey nodes (by elevation) + building level ({base["n_bld_level"]} elements)', fontsize=6.6, ha='center', color=TXT2)
    L3 = base['storeys'][6]
    xs2 = [4, 15.5, 27, 38.5]
    for x, d in zip(xs2, ['YAP', 'DUV', 'ACK', 'DON']):
        box(x, 17, 10.5, 6, f"{EN[d]} ({L3['disc'][d]['n']})", h(L3['disc'][d]['hash'])[:7] + '…'); ln(20, 28, x, 20)
    ax.text(46, 17, '… 8 disciplines', fontsize=7, ha='left', va='center', color=TXT2)
    lv = L3['disc']['ACK']['leaves'][:3]
    for k, (g, hh) in enumerate(lv):
        box(12 + k * 14, 5, 13, 6, g[:9] + '…', hh.hex()[:8] + '…', fc='white'); ln(27, 14, 12 + k * 14, 8)
    ax.text(54, 5, f"… {L3['disc']['ACK']['n']} leaves under L3 · OPN (record: body + Psets + type + material)", fontsize=6.6, va='center', color=TXT2)
    save(fig, 'Fig04_merkle')


# ---------------------------------------------------------------- Şekil: okuma anahtarı
def fig_key():
    fig, axs = plt.subplots(1, 2, figsize=(10, 5.2), gridspec_kw=dict(width_ratios=[1, 1]))
    P = dp.rosette(base); dp.draw(axs[0], P)
    axs[0].set_title('(a) Rev0 Digital Kitabe (Family A: star rosette)', fontsize=9.5, loc='left', color=TXT1)
    ax = axs[1]; ax.set_aspect('equal'); ax.axis('off'); ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.25, 1.25)
    ax.add_patch(Polygon([(-1.18, -1.18), (1.18, -1.18), (1.18, 1.18), (-1.18, 1.18)], fc='white', ec='#8a8984', lw=1))
    ax.add_patch(Wedge((0, 0), 0.985, 0, 360, width=0.33, fc='#e3eefb', ec='#8a8984', lw=0.6))
    ax.add_patch(Wedge((0, 0), 0.635, 0, 360, width=0.30, fc='#fdebe2', ec='#8a8984', lw=0.6))
    ax.add_patch(Circle((0, 0), 0.318, fc='#fff3d6', ec='#8a8984', lw=0.6))
    for i in range(N):
        a0, a1 = dp.ang(i, N)
        for r0, r1 in [(0.335, 0.985)]:
            ax.plot([r0 * math.cos(a1), r1 * math.cos(a1)], [r0 * math.sin(a1), r1 * math.sin(a1)], color='#b5b4ae', lw=0.4)
        am = (a0 + a1) / 2
        if i in (0, 4, 5, 6, 7, 8, 13, 17):
            nm = base['storeys'][i]['name'].replace('L1 - Block ', 'L1-B').replace(' - Parapet', '-Par').replace('Green Roof Hardscape', 'Green roof')
            ax.text(1.08 * math.cos(am), 1.08 * math.sin(am), nm, fontsize=5.6, ha='center', va='center', rotation=math.degrees(am) - 90 if abs(math.degrees(am) - 90) < 90 or True else 0, color=TXT2)
    # tek sektörün disiplin hücreleri
    a0, a1 = dp.ang(6, N)
    for j, d in enumerate(codes):
        row, colm = j // 2, j % 2
        rr = 0.655 + 0.33 * (row + 0.5) / 4; aa = a0 + (a1 - a0) * (colm + 0.5) / 2
        ax.text(rr * math.cos(aa), rr * math.sin(aa), EN[d], fontsize=4.6, ha='center', va='center', color=TXT1, rotation=math.degrees(aa) - 90)
    ax.text(0, 0.05, 'ROOT', ha='center', fontsize=8.5, weight='bold', color=TXT1)
    ax.text(0, -0.08, 'central star\n+ 16-petal crown', ha='center', va='top', fontsize=6.2, color=TXT2)
    ax.text(0, -0.49, 'STOREY RING', ha='center', fontsize=7, weight='bold', color=TXT1, bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.85))
    ax.text(0, -0.56, '18 sectors · clockwise from top, by elevation', ha='center', fontsize=5.6, color=TXT2, bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.85))
    ax.text(0, -0.80, 'STOREY × DISCIPLINE RING', ha='center', fontsize=7, weight='bold', color=TXT1, bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.85))
    ax.text(0, -0.87, '4 rows × 2 cells per sector (STR WAL / FAC OPN / CIR FUR / SPC OTH)', ha='center', fontsize=5.4, color=TXT2, bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.85))
    for sx, sy in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        ax.add_patch(Circle((sx * 1.02, sy * 1.02), 0.11, fc='#e8f6ef', ec='#8a8984', lw=0.6))
    for sx, sy in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        ax.text(sx * 1.02, sy * 1.02, 'corner:\nnon-spatial\nbranch', ha='center', va='center', fontsize=4.6, color=TXT1)
    ax.set_title('(b) Reading key: pattern regions ↔ Merkle levels', fontsize=9.5, loc='left', color=TXT1)
    save(fig, 'Fig05_reading_key')


# ---------------------------------------------------------------- Şekil: revizyon karşılaştırması
def changed_regions(Pa, Pb):
    sa, sb = dp.region_signature(Pa), dp.region_signature(Pb)
    return {k for k in sa if sa[k] != sb.get(k)}


def region_outline(ax, P, regions, color='#d01c1c'):
    for p in P:
        if p['region'] in regions and (p['region'].startswith('disc') or p['region'].startswith('storey') or p['region'] == 'nonspatial') and p['z'] == 1:
            ax.add_patch(Polygon(p['poly'], closed=True, fc='none', ec=color, lw=2.2, zorder=10))
        if p['region'] in regions and p['region'] == 'nonspatial' and p['z'] == 2 and len(p['poly']) == 16:
            c = np.mean(np.array(p['poly']), 0); r = np.max(np.linalg.norm(np.array(p['poly']) - c, axis=1)) * 1.25
            ax.add_patch(Circle(tuple(c), r, fc='none', ec=color, lw=2.0, zorder=10))


def fig_revisions(fam='A'):
    gen = dp.rosette if fam == 'A' else dp.hexlattice
    Ps = [gen(t) for t in T]
    fig, axs = plt.subplots(1, 5, figsize=(13, 3.6) if fam == 'A' else (12, 4.6))
    info = []
    for k, ax in enumerate(axs):
        dp.draw(ax, Ps[k])
        if k:
            ch = changed_regions(Ps[k - 1], Ps[k]); region_outline(ax, Ps[k], ch)
            info.append(sorted(ch))
        root = T[k]['root'].hex()[:8]
        lab = 'Rev0 (approved)' if k == 0 else f'Rev{k}'
        ax.set_title(f'{lab}\nroot {root}…', fontsize=8, color=TXT1)
    save(fig, f'Fig_rev_{fam}')
    return info


def fig_rev_zoom():
    """Rev0 ve Rev1 yan yana, değişen bölgeler vurgulu, diğerleri soluk."""
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.9))
    P0, P1 = dp.rosette(T[0]), dp.rosette(T[1])
    ch = changed_regions(P0, P1)
    dp.draw(axs[0], P0); axs[0].set_title('(a) Rev0', fontsize=9, loc='left')
    dp.draw(axs[1], P1); region_outline(axs[1], P1, ch)
    hidden = {'disc:6:ACK'} - ch
    for p in P1:
        if p['region'] in hidden and p['z'] == 1:
            axs[1].add_patch(Polygon(p['poly'], closed=True, fc='none', ec='#141414', lw=1.6, ls=(0, (2, 1.5)), zorder=11))
    axs[1].set_title('(b) Rev1 (door on L3 moved)', fontsize=9, loc='left')
    dp.draw(axs[2], P1, highlight=ch | {'root'}, dim_others=True); region_outline(axs[2], P1, ch)
    axs[2].set_title('(c) Visibly changed: root + L3 sector', fontsize=9, loc='left')
    save(fig, 'Fig_rev1_detail')
    return sorted(ch)


# ---------------------------------------------------------------- Şekil: simülasyon
def fig_sim():
    S = json.load(open(f'{OUT}/sim.json'))
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.3), gridspec_kw=dict(width_ratios=[1.15, 1]))
    ax = axs[0]
    labels = ['Root region', 'Affected storey sector', 'Affected storey×discipline cell']
    keys = ['root_visible', 'storey_visible', 'disc_visible']
    x = np.arange(3); w = 0.36
    for j, fam in enumerate(['A', 'B']):
        v = [S[fam][k] * 100 for k in keys]
        b = ax.bar(x + (j - 0.5) * w, v, w * 0.92, color=CAT[j], label=f'Family {fam}')
        for xi, vi in zip(x + (j - 0.5) * w, v): ax.text(xi, vi + 1.2, f'{vi:.1f}', ha='center', fontsize=7, color=TXT2)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5); ax.set_ylim(0, 125); ax.set_ylabel('Visibly changed (%)')
    ax.spines[['top', 'right']].set_visible(False); ax.legend(frameon=False, fontsize=7.5, loc='upper right', ncol=2)
    ax.set_title('(a) Single-element change (n = 400)', fontsize=8.5, loc='left')
    ax = axs[1]
    for j, fam in enumerate(['A', 'B']):
        ax.hist(np.array(S[fam]['random_pair_fracs']) * 100, bins=np.arange(55, 76, 1), color=CAT[j], histtype='step', lw=2, label=f'Family {fam}')
    ax.set_xlabel('Regions that differ between two random models (%)'); ax.set_ylabel('Number of model pairs')
    ax.spines[['top', 'right']].set_visible(False); ax.legend(frameon=False, fontsize=7.5)
    ax.set_title('(b) Random model pairs (n = 150)', fontsize=8.5, loc='left')
    save(fig, 'Fig_simulation')


if __name__ == '__main__':
    fig_distribution(); fig_merkle(); fig_key()
    a = fig_revisions('A'); b = fig_revisions('B'); z = fig_rev_zoom(); fig_sim()
    json.dump(dict(revA=a, revB=b, zoom=z), open(f'{OUT}/fig_regions_en.json', 'w'), indent=1)
    print(a); print(z)

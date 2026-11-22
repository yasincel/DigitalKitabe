"""Figures of the pattern encoding, generated from results/merkle_tree_rev*.json and results/e11_encoding.json:
Fig_encoding (DK-ENC-1.0 vs 1.1 and reading key), Fig_rev_A (Rev0-Rev4, DK-ENC-1.1), Fig_rev_B (Family B),
Fig_fixed_rule (rule and free variables) and Fig_proxies (computational proxies)."""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Wedge
import dkpattern as dp

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})
RES = os.path.join(HERE, 'results'); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
T = [dp.load_tree_json(os.path.join(RES, f'merkle_tree_rev{k}.json')) for k in range(5)]
E = json.load(open(os.path.join(RES, 'e11_encoding.json')))
base = T[0]; N = len(base['storeys']); S = dp.n_sectors(N)
TXT1, TXT2 = '#0b0b0b', '#52514e'


def save(fig, name):
    fig.savefig(f'{FIG}/{name}.png', dpi=600, bbox_inches='tight', facecolor='white'); plt.close(fig)


def reading_key(ax):
    ax.set_aspect('equal'); ax.axis('off'); ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.25, 1.25)
    ax.add_patch(Wedge((0, 0), 0.985, 0, 360, width=0.33, fc='#e3eefb', ec='#8a8984', lw=0.6))
    ax.add_patch(Wedge((0, 0), 0.635, 0, 360, width=0.30, fc='#fdebe2', ec='#8a8984', lw=0.6))
    ax.add_patch(Circle((0, 0), 0.318, fc='#fff3d6', ec='#8a8984', lw=0.6))
    for i in range(S):
        a0, a1 = dp.ang(i, S)
        ax.plot([0.335 * math.cos(a1), 0.985 * math.cos(a1)], [0.335 * math.sin(a1), 0.985 * math.sin(a1)], color='#b5b4ae', lw=0.4)
    for i, lab in [(0, 'Parking (lowest)'), (N - 1, 'highest story'), (6, 'L3')]:
        a0, a1 = dp.ang(i, S); am = (a0 + a1) / 2
        ax.text(1.1 * math.cos(am), 1.1 * math.sin(am), lab, fontsize=6.5, ha='center', va='center', color=TXT2)
    a0, a1 = dp.ang(N + 2, S); am = (a0 + a1) / 2
    ax.text(0.8 * math.cos(am), 0.8 * math.sin(am), 'reserved', fontsize=6.5, ha='center', va='center', color=TXT2)
    ax.text(0, 0.04, 'ROOT', ha='center', fontsize=9, weight='bold')
    ax.text(0, -0.1, '12-star + 24 petals', ha='center', fontsize=6.3, color=TXT2)
    ax.text(0, -0.49, 'STORIES', ha='center', fontsize=7.5, weight='bold')
    ax.text(0, -0.83, 'STORY × DISCIPLINE', ha='center', fontsize=7.5, weight='bold',
            bbox=dict(boxstyle='round,pad=0.15', fc='#e3eefb', ec='none'))
    for sx, sy in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        ax.add_patch(Circle((sx * 1.02, sy * 1.02), 0.11, fc='#eef2ee', ec='#8a8984', lw=0.6))
        ax.text(sx * 1.02, sy * 1.02, 'non-\nspatial', ha='center', va='center', fontsize=5.5)


def fig_encoding():
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.9))
    dp.draw(axs[0], dp.rosette_v10(base)); dp.draw(axs[1], dp.rosette(base)); reading_key(axs[2])
    e0, e1 = E['DK-ENC-1.0'], E['DK-ENC-1.1']
    axs[0].set_title(f"(a) DK-ENC-1.0 (first version)\n{e0['storey_sectors']} sectors; motifs of order "
                     + ', '.join(map(str, e0['storey_motif_orders'])), fontsize=8.5)
    axs[1].set_title(f"(b) DK-ENC-1.1 (current)\n{S} sectors ({S - N} reserved); motifs of order 6 and 12", fontsize=8.5)
    axs[2].set_title('(c) Reading key: regions ↔ Merkle levels\n', fontsize=8.5)
    save(fig, 'Fig_encoding')


def changed(Pa, Pb):
    sa, sb = dp.region_signature(Pa), dp.region_signature(Pb)
    return {k for k in sa if sa[k] != sb.get(k)}


def outline(ax, P, regions, color='#d01c1c'):
    for p in P:
        r = p['region']
        if r in regions and (r.startswith('disc') or r.startswith('storey')) and p['z'] == 1:
            ax.add_patch(Polygon(p['poly'], closed=True, fc='none', ec=color, lw=1.6, zorder=10))
        if r in regions and r == 'nonspatial' and p['z'] == 2:
            c = np.mean(np.array(p['poly']), 0)
            ax.add_patch(Circle(tuple(c), 0.17, fc='none', ec=color, lw=1.6, zorder=10))
        if r in regions and r == 'root' and p['z'] == 3:
            ax.add_patch(Circle((0, 0), 0.34, fc='none', ec=color, lw=1.6, zorder=10))


def fig_revisions(fam):
    gen = dp.rosette if fam == 'A' else dp.hexlattice
    Ps = [gen(t) for t in T]
    fig, axs = plt.subplots(1, 5, figsize=(13, 3.3) if fam == 'A' else (12, 4.6))
    for k, ax in enumerate(axs):
        dp.draw(ax, Ps[k])
        if k:
            ch = changed(Ps[k - 1], Ps[k])
            if fam == 'A': outline(ax, Ps[k], ch)
            if k == 1 and fam == 'A':   # cell with new digest but unchanged appearance
                for p in Ps[1]:
                    if p['region'] == 'disc:6:ACK' and p['z'] == 1:
                        ax.add_patch(Polygon(p['poly'], closed=True, fc='none', ec=TXT1, lw=1.4, ls=(0, (2, 1.5)), zorder=11))
        ax.set_title(('Rev0 (approved)' if k == 0 else f'Rev{k}') + f"\nroot {T[k]['root'].hex()[:8]}…", fontsize=8)
    save(fig, f'Fig_rev_{fam}')


def fig_fixed_rule():
    fig = plt.figure(figsize=(10.5, 3.6))
    ax = fig.add_axes([0.0, 0.05, 0.27, 0.8])
    P = [p for p in dp.rosette(base) if p['z'] <= 1]
    for p in P: ax.add_patch(Polygon(p['poly'], closed=True, fc=dp.PAPER if p['region'] != 'frame' else '#f4efe4', ec='#b8b2a4', lw=0.4))
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.2, 1.2); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('(a) Fixed rule: C12 skeleton,\n24 sectors, region layout', fontsize=8.5)
    ax = fig.add_axes([0.3, 0.05, 0.42, 0.8]); ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('(b) Free variables of one story region (5 bits)', fontsize=8.5)
    ax.text(0.2, 5.5, 'variant (2 bits)', fontsize=7.5, color=TXT2)
    motifs = [(dp.star, (0.75, 0.55 * 0.75, 6)), (dp.star, (0.75, 0.36 * 0.75, 6)), (None, None), (dp.star, (0.75, 0.72 * 0.75, 12))]
    names = ['6-star', 'sharp 6-star', 'hexagon', '12-star']
    for k, nm in enumerate(names):
        cx, cy = 1.0 + k * 2.4, 4.3; col = dp.PALETTE[k]
        if k == 2:
            ax.add_patch(Polygon(dp.ngon(cx, cy, 0.75, 6, math.pi / 2), fc=col, ec=dp.INK, lw=0.8))
            ax.add_patch(Polygon(dp.star(cx, cy, 0.6, 0.34, 6, math.pi / 2 + math.pi / 6), fc=dp.PAPER, ec=dp.INK, lw=0.5))
        else:
            ax.add_patch(Polygon(dp.star(cx, cy, *motifs[k][1], math.pi / 2), fc=col, ec=dp.INK, lw=0.8))
        ax.text(cx, 3.25, nm, ha='center', fontsize=7.5)
    ax.text(0.2, 2.6, 'color (2 bits)', fontsize=7.5, color=TXT2)
    for k, c in enumerate(dp.PALETTE):
        ax.add_patch(Polygon([(0.4 + k * 1.1, 0.8), (1.3 + k * 1.1, 0.8), (1.3 + k * 1.1, 1.9), (0.4 + k * 1.1, 1.9)], fc=c, ec=dp.INK, lw=0.8))
    ax.text(5.4, 2.6, 'rotation (1 bit): 0° / 15°', fontsize=7.5, color=TXT2)
    for k, r in enumerate([0, math.pi / 12]):
        ax.add_patch(Polygon(dp.star(6.3 + k * 2.0, 1.35, 0.65, 0.36, 6, math.pi / 2 + r), fc=dp.PALETTE[0], ec=dp.INK, lw=0.8))
    ax = fig.add_axes([0.74, 0.05, 0.26, 0.8]); dp.draw(ax, dp.rosette(base))
    ax.set_title('(c) Data in free variables;\nreserved sectors keep the rule', fontsize=8.5)
    save(fig, 'Fig_fixed_rule')


def fig_proxies():
    sc = E['single_change_DK-ENC-1.1']
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.2), gridspec_kw=dict(width_ratios=[1.15, 1]))
    ax = axs[0]; v = [sc['root'] * 100, sc['storey'] * 100, sc['cell'] * 100]; bits = [53, 5, 3]
    ax.bar(range(3), v, 0.55, color='#2a78d6')
    for x, (vi, b) in enumerate(zip(v, bits)):
        ax.text(x, vi + 1.5, f'{vi:.1f}', ha='center', fontsize=7.5)
        ax.plot([x - 0.35, x + 0.35], [100 * (1 - 2 ** -b)] * 2, ls=':', color=TXT1, lw=1)
    ax.set_xticks(range(3)); ax.set_xticklabels(['Root region\n(53 bits)', 'Story sector\n(5 bits)', 'Cell\n(3 bits)'], fontsize=7.5)
    ax.set_ylim(0, 112); ax.set_ylabel('Encoded appearance changed (%)'); ax.spines[['top', 'right']].set_visible(False)
    ax.set_title(f"(a) Single-element changes (n = {sc['trials']}); dotted: 1 − 2$^{{-b}}$", fontsize=8.5, loc='left')
    ax = axs[1]
    for k, ver in enumerate(['DK-ENC-1.0', 'DK-ENC-1.1']):
        e = E[ver]; m = e['insertion_unchanged_mean'] * 100
        ax.bar(k, m, 0.5, color=['#b5452c', '#2a9d9a'][k])
        ax.errorbar(k, m, yerr=[[m - e['insertion_unchanged_min'] * 100], [e['insertion_unchanged_max'] * 100 - m]], color=TXT1, capsize=4, lw=1)
        ax.text(k + 0.3, m, f'{m:.1f}', va='center', fontsize=7.5)
    ax.set_xticks([0, 1]); ax.set_xticklabels(['DK-ENC-1.0', 'DK-ENC-1.1']); ax.set_ylim(0, 105)
    ax.set_ylabel('Drawing unchanged in place (%)'); ax.spines[['top', 'right']].set_visible(False)
    ax.set_title(f"(b) One story inserted (mean, range; {E['DK-ENC-1.1']['insertion_positions']} positions)", fontsize=8.5, loc='left')
    save(fig, 'Fig_proxies')


if __name__ == '__main__':
    fig_encoding(); fig_revisions('A'); fig_revisions('B'); fig_fixed_rule(); fig_proxies()
    print(sorted(os.listdir(FIG)))

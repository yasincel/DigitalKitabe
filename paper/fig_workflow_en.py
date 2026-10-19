"""Fig. 1 (workflow) and graphical abstract, English."""
import sys, pickle
import os as _os; HERE = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, HERE)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image
import dkpattern as dp

FIG = _os.path.join(HERE, 'figures'); OUT = _os.path.join(HERE, 'out')
INK, SUB, EDGE, ACC = '#0b0b0b', '#52514e', '#9a998f', '#2a78d6'
plt.rcParams.update({'font.family': 'DejaVu Sans'})


def box(ax, x, y, w, h, t1, t2, hl=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12',
                                fc='#e3eefb' if hl else 'white', ec=ACC if hl else EDGE, lw=1.6 if hl else 1.0))
    ax.text(x + w / 2, y + h * 0.63, t1, ha='center', va='center', fontsize=10.5, weight='bold', color=INK)
    ax.text(x + w / 2, y + h * 0.3, t2, ha='center', va='center', fontsize=7.9, color=SUB)


def arrow(ax, p0, p1, dashed=False):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=11, color=EDGE, lw=1.1,
                                 linestyle=(0, (4, 3)) if dashed else '-'))


def workflow():
    fig, ax = plt.subplots(figsize=(10, 3.9)); ax.set_xlim(0, 10); ax.set_ylim(0, 3.9); ax.axis('off')
    w, h = 2.1, 0.95
    xs = [0.1, 2.6, 5.1, 7.6]
    top = [('IFC model', 'approved version'), ('Canonical form', 'kitabe objects excluded'),
           ('Merkle root', 'storey · discipline · element'), ('Ledger record', 'signatures + timestamp')]
    bot = [('Pattern generation', 'historical grammar'), ('IFC embedding', 'Pset + IfcAnnotation'),
           ('Handover', 'CDE, permit, delivery'), ('Verification', 're-compute the root')]
    for i, (a, b) in enumerate(top): box(ax, xs[i], 2.75, w, h, a, b)
    for i, (a, b) in enumerate(bot): box(ax, xs[i], 0.25, w, h, a, b, hl=(i == 3))
    for i in range(3):
        arrow(ax, (xs[i] + w + 0.03, 3.22), (xs[i + 1] - 0.03, 3.22))
        arrow(ax, (xs[i] + w + 0.03, 0.72), (xs[i + 1] - 0.03, 0.72))
    # root -> pattern
    ax.plot([xs[2] + w / 2, xs[2] + w / 2, xs[0] + w / 2], [2.75, 2.0, 2.0], color=EDGE, lw=1.1)
    arrow(ax, (xs[0] + w / 2, 2.0), (xs[0] + w / 2, 1.23))
    ax.text((xs[0] + xs[2] + w) / 2 + 0.2, 2.1, 'root and branch digests', ha='center', fontsize=8.6, color=SUB)
    arrow(ax, (xs[3] + w / 2, 1.23), (xs[3] + w / 2, 2.72), dashed=True)
    ax.text(xs[3] + w / 2 + 0.1, 1.98, 'compare', ha='left', fontsize=8.6, color=SUB)
    ax.text(0.1, 3.85, 'Cryptographic layer', fontsize=9, color=SUB, va='top', style='italic')
    ax.text(xs[1], 1.42, 'Visual layer and use', fontsize=9, color=SUB, va='top', style='italic')
    fig.savefig(f'{FIG}/Fig01_workflow.png', dpi=330, bbox_inches='tight', facecolor='white'); plt.close(fig)


def graphical_abstract():
    t0 = pickle.load(open(OUT + '/tree_rev0.pkl', 'rb'))
    t1 = pickle.load(open(OUT + '/tree_rev1.pkl', 'rb'))
    fig = plt.figure(figsize=(13.28, 5.31))  # 5:2 aspect
    ax0 = fig.add_axes([0.0, 0.08, 0.30, 0.84]); ax0.axis('off')
    im = Image.open(FIG + '/Fig02_model3d_nolegend.png'); ax0.imshow(im)
    ax0.set_title('IFC model (Snowdon Towers, 7,957 elements)', fontsize=11)
    axm = fig.add_axes([0.31, 0.08, 0.16, 0.84]); axm.axis('off'); axm.set_xlim(0, 1); axm.set_ylim(0, 1)
    for y, t in [(0.82, 'Canonical form\n(shifted quantisation)'), (0.55, 'Merkle root\nstorey · discipline · element'), (0.28, 'Signed ledger\nrevision chain')]:
        axm.add_patch(FancyBboxPatch((0.05, y - 0.08), 0.9, 0.16, boxstyle='round,pad=0.01,rounding_size=0.03', fc='white', ec=EDGE))
        axm.text(0.5, y, t, ha='center', va='center', fontsize=9.5)
    for y in (0.72, 0.45): axm.annotate('', (0.5, y - 0.07), (0.5, y + 0.01), arrowprops=dict(arrowstyle='-|>', color=EDGE))
    a1 = fig.add_axes([0.49, 0.08, 0.24, 0.84]); dp.draw(a1, dp.rosette(t0)); a1.set_title('Digital Kitabe, Rev0', fontsize=11)
    a2 = fig.add_axes([0.75, 0.08, 0.24, 0.84]); P1 = dp.rosette(t1); dp.draw(a2, P1); a2.set_title('Rev1: change visible on storey L3', fontsize=11)
    from figures_en import changed_regions, region_outline
    region_outline(a2, P1, changed_regions(dp.rosette(t0), P1))
    fig.savefig(f'{FIG}/Graphical_abstract.png', dpi=250, facecolor='white'); plt.close(fig)


if __name__ == '__main__':
    workflow()
    if 'ga' in sys.argv: graphical_abstract()

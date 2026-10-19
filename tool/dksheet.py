"""Digital Kitabe emblem ('kitabe sheet'): pattern + inscription bands + repair medallions.

The inscription bands carry human-readable project metadata, like the text of a historical
kitabe. They are informative only; the binding identity is the Merkle root encoded in the
pattern and stored in the record.
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
import dkpattern as dp

INK = '#141414'; PAPER = '#f6f1e6'; GOLD = '#b08a3e'


def _band(ax, x0, y0, w, h, lines, size=10):
    ax.add_patch(Rectangle((x0, y0), w, h, fc=PAPER, ec=INK, lw=1.4, zorder=1))
    ax.add_patch(Rectangle((x0 + 0.03, y0 + 0.03), w - 0.06, h - 0.06, fc='none', ec=GOLD, lw=0.8, zorder=2))
    n = len(lines)
    for i, (t, bold) in enumerate(lines):
        yy = y0 + h * (n - i) / (n + 1)
        ax.text(x0 + w / 2, yy, t, ha='center', va='center', fontsize=size, color=INK,
                weight='bold' if bold else 'normal', family='DejaVu Serif', zorder=3)


def draw_sheet(path, tree, meta, history_trees=(), dpi=300):
    """meta: dict(project, number, building, date, revision, root, c14n, enc, note)"""
    nh = len(history_trees)
    W = 6.4; H = 8.7 + (1.85 if nh else 0)
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    ax.add_patch(Rectangle((0.08, 0.08), W - 0.16, H - 0.16, fc='white', ec=INK, lw=2.0))
    top = H - 0.35
    _band(ax, 0.35, top - 1.15, W - 0.7, 1.0,
          [(meta.get('project', '').upper(), True), (meta.get('building', '') + ('  ·  ' + meta['number'] if meta.get('number') else ''), False)], size=12)
    # pattern
    pa = fig.add_axes([0.5 / W, (top - 1.35 - 5.2) / H, (W - 1.0) / W, 5.2 / H])
    dp.draw(pa, dp.rosette(tree))
    # lower band
    yb = top - 1.35 - 5.2 - 0.25 - 1.2
    _band(ax, 0.35, yb, W - 0.7, 1.2,
          [(f"Revision {meta.get('revision', 0)}  ·  approved {meta.get('date', '')}", True),
           (f"model root  {meta.get('root', '')[:16]}…", False),
           (f"{meta.get('c14n', '')}  ·  {meta.get('enc', '')}", False)], size=9.5)
    # repair medallions (revision history)
    if nh:
        ax.text(W / 2, yb - 0.22, 'earlier approvals (repair kitabe chain)', ha='center', va='center', fontsize=8.5, style='italic', color='#52514e', family='DejaVu Serif')
        size = min(0.95, (W - 0.9) / max(nh, 1) - 0.12)
        x = W / 2 - (nh * (size + 0.12) - 0.12) / 2
        for k, (lab, t) in enumerate(history_trees):
            ma = fig.add_axes([x / W, (yb - 0.35 - size) / H, size / W, size / H]); dp.draw(ma, dp.rosette(t))
            ax.text(x + size / 2, yb - 0.45 - size, lab, ha='center', va='top', fontsize=7.5, family='DejaVu Serif')
            x += size + 0.12
    fig.savefig(path, dpi=dpi, facecolor='white'); plt.close(fig)

"""Layered framework figure and design-science process figure (English)."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams.update({'font.family': 'DejaVu Sans'})
INK, SUB, EDGE = '#0b0b0b', '#52514e', '#9a998f'
FILL = ['#eef3fb', '#fbf1e8', '#eef7f1', '#f4f0fa']
import os as _os; HERE = _os.path.dirname(_os.path.abspath(__file__))
FIG = _os.path.join(HERE, 'figures'); OUT = _os.path.join(HERE, 'out')


def rbox(ax, x, y, w, h, fc, ec=EDGE, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.01,rounding_size=0.08', fc=fc, ec=ec, lw=lw))


def framework():
    fig, ax = plt.subplots(figsize=(10.4, 6.2)); ax.set_xlim(0, 10.3); ax.set_ylim(0, 6.2); ax.axis('off')
    layers = [
        ('L4  Process and\n      governance', 'who approves, signs, verifies',
         ['Approval roles\narchitect · client\nauthority', 'Revision chain\n(repair kitabe)', 'Verification at\npermit · inspection\nhandover']),
        ('L3  Visual layer', 'pattern grammar (DK-ENC)',
         ['Free variables\nas data\nchannels', 'Merkle level\n→ pattern\nregion', 'Pattern families\nA star rosette\nB lattice …']),
        ('L2  Cryptographic\n      layer', 'canonical commitment (DK-C14N)',
         ['Canonical form\n+ shifted\nquantisation', 'Merkle tree\nstorey · discipline\n· element', 'Signed ledger\nrecord (root,\nversions, time)']),
        ('L1  Information\n      layer', 'IFC model (ISO 16739)',
         ['Spatial structure\nand elements', 'Types, materials,\nproperty sets', 'Embedded identity\nPset_DigitalKitabe\n+ IfcAnnotation']),
    ]
    y = 4.75
    for k, (title, sub, comps) in enumerate(layers):
        rbox(ax, 0.05, y, 7.55, 1.3, FILL[k])
        ax.text(0.2, y + 0.95, title, fontsize=10.5, weight='bold', color=INK, va='center', linespacing=1.1)
        ax.text(0.2, y + 0.3, sub, fontsize=7.8, color=SUB, va='center', style='italic')
        for j, c in enumerate(comps):
            rbox(ax, 2.75 + j * 1.6, y + 0.12, 1.5, 1.06, 'white')
            ax.text(2.75 + j * 1.6 + 0.75, y + 0.65, c, fontsize=7.4, ha='center', va='center', color=INK, linespacing=1.15)
        y -= 1.5
    # requirements column
    rbox(ax, 7.85, 0.25, 2.35, 5.8, 'white')
    ax.text(9.02, 5.75, 'Requirements', fontsize=10.5, weight='bold', ha='center')
    reqs = [('R1', 'content-derived'), ('R2', 'stable across\nsoftware'), ('R3', 'self-consistent\nembedding'),
            ('R4', 'change\nlocalisation'), ('R5', 'human\nrecognisability'), ('R6', 'privacy and\nlongevity')]
    for i, (r, t) in enumerate(reqs):
        yy = 5.3 - i * 0.82
        ax.text(8.05, yy, r, fontsize=10, weight='bold', color=INK, va='center')
        ax.text(8.5, yy, t, fontsize=8.3, color=SUB, va='center', linespacing=1.1)
    # arrows between layers
    for yy in (4.75, 3.25, 1.75):
        ax.add_patch(FancyArrowPatch((1.2, yy - 0.18), (1.2, yy + 0.02), arrowstyle='-|>', mutation_scale=10, color=EDGE, lw=1))
    fig.savefig(f'{FIG}/Fig_framework.png', dpi=400, bbox_inches='tight', facecolor='white'); plt.close(fig)


if __name__ == '__main__':
    framework()

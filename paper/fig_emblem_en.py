"""Project emblem after Rev4 with Rev0-Rev3 medallions (Fig. 8, Fig_kitabe_sheet.png).
Requires out/tree_rev0..4.pkl (experiments.py). Project data as read from the IFC project and building entities."""
import sys, pickle, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import dksheet
OUT = os.path.join(HERE, 'out'); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
T = [pickle.load(open(f'{OUT}/tree_rev{k}.pkl', 'rb')) for k in range(5)]
meta = dict(project='Snowdon Towers 2.0', building='Snowdon Towers', number='7765328-33-A-2.0',
            date='2026-10-16', revision=4, root=T[4]['root'].hex(), c14n='DK-C14N-1.1', enc='DK-ENC-1.0')
dksheet.draw_sheet(f'{FIG}/Fig_kitabe_sheet.png', T[4], meta,
                   history_trees=[(f'Rev{k}', T[k]) for k in range(4)], dpi=400)
print('written', f'{FIG}/Fig_kitabe_sheet.png')

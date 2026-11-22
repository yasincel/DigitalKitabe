"""Project emblem after Rev4 with Rev0-Rev3 medallions (Fig. 8, Fig_kitabe_sheet.png).
Uses out/tree_rev0..4.pkl (experiments.py) or, if absent, results/merkle_tree_rev*.json. Project data as read from the IFC project and building entities."""
import sys, pickle, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import dksheet, dkpattern as dp
OUT = os.path.join(HERE, 'out'); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
T = [pickle.load(open(f'{OUT}/tree_rev{k}.pkl', 'rb')) if os.path.exists(f'{OUT}/tree_rev{k}.pkl')
     else dp.load_tree_json(os.path.join(HERE, 'results', f'merkle_tree_rev{k}.json')) for k in range(5)]
meta = dict(project='Snowdon Towers 2.0', building='Snowdon Towers', number='7765328-33-A-2.0',
            date='2026-10-16', revision=4, root=T[4]['root'].hex(), c14n='DK-C14N-1.1', enc=dp.ENC_VERSION)
dksheet.draw_sheet(f'{FIG}/Fig_kitabe_sheet.png', T[4], meta,
                   history_trees=[(f'Rev{k}', T[k]) for k in range(4)], dpi=400)
print('written', f'{FIG}/Fig_kitabe_sheet.png')

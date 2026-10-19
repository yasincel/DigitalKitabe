#!/bin/sh
set -e
cd "$(dirname "$0")"
python e1_stability.py
python experiments.py
python simulate.py out/tree_rev0.pkl out/sim.json
python geom_extract.py "${DK_IFC:-input/Snowdon_Towers_Sample_Architectural.ifc}" out/geom.pkl
python render3d.py en m3d rev
python figures_en.py
python fig_workflow_en.py ga
python fig_framework_en.py
python fig_emblem_en.py
echo "Done. Results in out/, figures in figures/."

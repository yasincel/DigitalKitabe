@echo off
cd /d "%~dp0"
python e1_stability.py || goto :err
python experiments.py || goto :err
python simulate.py out\tree_rev0.pkl out\sim.json || goto :err
if "%DK_IFC%"=="" set DK_IFC=input\Snowdon_Towers_Sample_Architectural.ifc
python geom_extract.py "%DK_IFC%" out\geom.pkl || goto :err
python render3d.py en m3d rev || goto :err
python figures_en.py || goto :err
python fig_workflow_en.py ga || goto :err
python fig_framework_en.py || goto :err
python fig_emblem_en.py || goto :err
echo Done. Results in out\, figures in figures\.
pause
exit /b
:err
echo An error occurred, see the message above.
pause

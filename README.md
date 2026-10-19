# Digital Kitabe

Code and data accompanying the article

> **Digital Kitabe: A content-derived, verifiable identity embedded in IFC models through historical geometric pattern grammars**
> Yasin Celik.

The Digital Kitabe is a model identity that is computed from the content of an IFC model (a canonical Merkle commitment), stored inside the model with standard IFC entities (`Pset_DigitalKitabe` and a non-physical `IfcAnnotation` emblem), sealed in a signed append-only record and rendered as a pattern generated from historical geometric pattern grammars. Pattern regions mirror the Merkle hierarchy (storeys, disciplines, types), so that a change can be located approximately by eye, while binding verification remains the recomputation of the root.

## Contents

```
DigitalKitabe/
├── paper/              code that produced the results and figures of the article
│   ├── dkcore.py         DK-C14N-1.1 canonicalisation, Merkle tree, revision root, branch comparison
│   ├── dkpattern.py      DK-ENC-1.0 pattern generator (Family A star rosette, Family B hexagonal lattice)
│   ├── dksheet.py        project emblem (pattern + inscription bands + repair medallions)
│   ├── e1_stability.py   E1  canonicalisation stability (T1, T2) and quantisation ablation   (Sec. 6.1)
│   ├── experiments.py    E2–E4  embedding/self-reference, controlled revisions, signed ledger (Sec. 6.2)
│   ├── simulate.py       E5  computational perceptual proxies                               (Sec. 6.3)
│   ├── geom_extract.py, render3d.py, figures_en.py, fig_workflow_en.py,
│   │   fig_framework_en.py, fig_emblem_en.py      figures of the article
│   ├── run_all.sh / run_all.bat                   runs the full pipeline
│   ├── input/            place the Snowdon Towers IFC file here (not included, see below)
│   └── results/          results reported in the article (see "Data")
└── tool/               stand-alone command-line tool for practitioners (stamp, verify, identify)
```

## Requirements

- Python 3.12 or 3.13 (the article used Python 3.13)
- IfcOpenShell 0.8.x (the article used **0.8.4**), numpy, matplotlib, scipy, Pillow, cryptography

```
pip install -r requirements.txt
```

Memory: the 204 MB test model needs about 6 GB of RAM per loaded model; the scripts load one model at a time. 8 GB or more is recommended.

## Reproducing the article

1. Obtain the **Snowdon Towers** sample architectural model distributed by Autodesk with Revit (Snowdon Towers sample project, exported to IFC2X3). The model is Autodesk's and is **not redistributed** here. Save it as
   `paper/input/Snowdon_Towers_Sample_Architectural.ifc`
   (or point the environment variable `DK_IFC` to another location).
2. Run the pipeline:

```
cd paper
./run_all.sh          # Linux / macOS
run_all.bat           # Windows
```

| Step | Script | Output in `paper/out/` or `paper/figures/` | Article |
|---|---|---|---|
| E1 | `e1_stability.py` | `e1_stability.json`, `ablation.json`, `tree_rev0.pkl` | Tables 6–7 |
| E2–E4 | `experiments.py` | `results.json`, `ledger.json`, `tree_rev1..4.pkl`, `digital_kitabe_rev*.svg`, `Snowdon_DK_rev0.ifc` | Sec. 6.2, Table 8 |
| E5 | `simulate.py out/tree_rev0.pkl out/sim.json` | `sim.json` | Sec. 6.3 |
| Figures | `geom_extract.py`, `render3d.py en m3d rev`, `figures_en.py`, `fig_workflow_en.py ga`, `fig_framework_en.py`, `fig_emblem_en.py` | `figures/*.png` | figures of the article, graphical abstract |

Expected values: model root `19de7e05791d31b846dd543a8891fae6b8baebc57d9221705c604bfe22b96464` for the source, T1 and T2, and the ablation counts 21 / 167 / 2 / 0. Timings depend on the machine. The Ed25519 keys of the test ledger are generated afresh on every run, so public keys and signatures differ from the archived ledger, whereas all model roots and revision roots are deterministic. The control root computed with the self-reference exclusion disabled (Section 6.2) also differs between runs, because the embedded emblem objects receive newly generated GlobalIds; only the fact that it differs from the model root is relevant. Change types in the branch comparison are printed with internal Turkish labels (eklendi = added, silindi = deleted, değişti = changed).

## Data (`paper/results/`)

| File | Content |
|---|---|
| `results.json` | all numbers reported in Section 6 (roots, timings, embedding check, revisions, ledger verification) |
| `e1_stability.json`, `ablation.json` | E1 stability and quantisation ablation |
| `ledger.json` | Ed25519-signed, append-only **local test ledger** (a simulation; not written to a public blockchain) |
| `sim.json` | E5 simulation results |
| `merkle_tree_rev0..4.json` | derived Merkle trees (digests only, hexadecimal) of the approved model and the four controlled revisions |
| `patterns/` | Digital Kitabe patterns (SVG) for Rev0–Rev4 and the project emblem after Rev4 |

The Merkle trees contain only GlobalIds and SHA-256 digests; they contain no geometry or design content of the model.

## The practitioner tool (`tool/`)

`tool/dkitabe.py` applies the same rules (DK-C14N-1.1, DK-ENC-1.0) to any IFC file:

```
python dkitabe.py stamp    Model.ifc --note "Design approval"              # identity, emblem, stamped IFC, record
python dkitabe.py verify   Received.ifc Model_kitabe/Model_rev0_kitabe_record.json
python dkitabe.py stamp    Model_rev1.ifc --previous ..._rev0_kitabe_record.json --note "Rev 1"
python dkitabe.py identify emblem.png records_folder/                      # experimental
```

Windows users can drag and drop files onto the `.bat` files. A step-by-step guide in Turkish is provided in `tool/KULLANIM.md` / `KULLANIM.html`; `tool/ornek/demo_metric.ifc` is a small IFC4 test model.

`identify` (recognition of a pattern image against stored records) is an **experimental** feature that is not part of the evaluation reported in the article. Binding verification is always `verify` on the IFC file.

## Notes

- Discipline codes inside the code are internal labels that are part of the hashed node labels (changing them changes the roots): YAP = STR, DUV = WAL, CEP = FAC, ACK = OPN, DOL = CIR, DON = FUR, MEK = SPC, DIG = OTH.
- The visual pattern supports recognition; it is not a security mechanism.
- The historical pattern grammars are simplified reconstructions; no ownership of historical patterns is claimed.

## Licence

Code: MIT licence (see `LICENSE`). Data in `paper/results/`: CC BY 4.0.

## Citation

Please cite the article and this archive (see `CITATION.cff`).

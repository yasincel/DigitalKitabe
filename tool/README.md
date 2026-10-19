# Digital Kitabe – command-line tool

Creates and verifies a Digital Kitabe (canonical Merkle root + historical-pattern identity) for IFC models.
Same canonicalisation (DK-C14N-1.1) and encoding (DK-ENC-1.0) as the accompanying article.

    pip install -r requirements.txt
    python dkitabe.py stamp  MODEL.ifc [--previous RECORD.json] [--note "..."]
    python dkitabe.py verify MODEL.ifc RECORD.json
    python dkitabe.py identify PATTERN.png RECORD_FOLDER

Outputs: pattern (PNG/SVG), stamped IFC (Pset_DigitalKitabe + IfcAnnotation), record JSON,
and comparison images for revisions or failed verifications. `verify` exits with code 0 when the
model matches the record and 2 otherwise. Turkish instructions: KULLANIM.md.
Example model for a first test: ornek/demo_metric.ifc

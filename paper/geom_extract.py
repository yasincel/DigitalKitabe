import sys, time, pickle
import os as _os; HERE = _os.path.dirname(_os.path.abspath(__file__)); sys.path.insert(0, HERE); import numpy as np, multiprocessing
import ifcopenshell, ifcopenshell.geom
import dkcore

f = ifcopenshell.open(sys.argv[1])
s = ifcopenshell.geom.settings()
s.set('use-world-coords', True)
skip = ('IfcOpeningElement', 'IfcSpace', 'IfcDistributionPort', 'IfcAnnotation', 'IfcGrid')
include = [p for p in f.by_type('IfcProduct') if p.Representation and not any(p.is_a(c) for c in skip)
           and not p.is_a('IfcSpatialStructureElement')]
print('to process', len(include), flush=True)
it = ifcopenshell.geom.iterator(s, f, multiprocessing.cpu_count(), include=include)
out = []
cache = {}
t = time.time()
if it.initialize():
    while True:
        sh = it.get()
        e = f.by_id(sh.id)
        v = np.array(sh.geometry.verts, dtype=np.float32).reshape(-1, 3)
        fa = np.array(sh.geometry.faces, dtype=np.int32).reshape(-1, 3)
        st = dkcore.storey_of(e, cache)
        out.append(dict(gid=e.GlobalId, cls=e.is_a(), disc=dkcore.discipline_of(e), storey=st.Name if st else None, v=v, f=fa))
        if len(out) % 1000 == 0: print(len(out), round(time.time() - t), flush=True)
        if not it.next(): break
print('done', len(out), round(time.time() - t), sum(len(o['f']) for o in out))
pickle.dump(out, open(sys.argv[2], 'wb'))

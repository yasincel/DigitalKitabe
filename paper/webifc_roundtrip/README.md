# web-ifc round trip (third software for E7)

`roundtrip.cpp` re-serialises an IFC file with web-ifc's own C++ STEP parser and writer
(IfcLoader::LoadFile / IfcLoader::SaveFile). Built natively against
https://github.com/ThatOpen/engine_web-ifc at commit d1962b4178c0fbfa87368e0b415c71ab97c0220d (web-ifc 0.0.81):

```
git clone https://github.com/ThatOpen/engine_web-ifc.git && cd engine_web-ifc/src/cpp
cp /path/to/roundtrip.cpp test/
cat >> CMakeLists.txt <<'X'
if(NOT EMSCRIPTEN)
	add_executable(dk-roundtrip ${web-ifc-source} "./test/roundtrip.cpp")
	param_setter(dk-roundtrip)
endif()
X
mkdir build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make dk-roundtrip
```

Usage: `dk-roundtrip in.ifc out.ifc`. Set the environment variable WEBIFC to the binary before running e7_generalisation.py.

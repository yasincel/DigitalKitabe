// Re-serialise an IFC file with web-ifc's own STEP parser and writer.
#include <iostream>
#include <fstream>
#include <sstream>
#include "../web-ifc/parsing/IfcLoader.h"
#include "../web-ifc/schema/IfcSchemaManager.h"
int main(int argc, char **argv) {
    if (argc < 3) { std::cerr << "usage: roundtrip in.ifc out.ifc\n"; return 1; }
    webifc::schema::IfcSchemaManager schemaManager;
    webifc::parsing::IfcLoader loader(67108864, 4294967295u, 10000, schemaManager);
    std::ifstream in(argv[1], std::ios::binary);
    loader.LoadFile(in);
    std::ofstream out(argv[2], std::ios::binary);
    loader.SaveFile(out, true);
    std::cout << "lines " << loader.GetMaxExpressId() << std::endl;
    return 0;
}

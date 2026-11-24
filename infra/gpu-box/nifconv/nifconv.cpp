// nifconv: Skyrim LE (2011, 20.2.0.7 user 12 stream 83) NIFs to Skyrim SE (stream 100), built on ousnius/nifly, the
// library Outfit Studio and Cathedral Assets Optimizer use for the same step: NifFile::OptimizeFor(SSE) turns every
// NiTriShape/NiTriStrips into a BSTriShape (vertex layout, tangents, skin partitions) and fixes the shader flags.
// Usage: nifconv --batch   stdin lines "info\t<in>" or "conv\t<in>\t<out>"; one answer line per request:
//   info -> "ok <stream> <nitrishape> <bstrishape> <skinned> <other>"  (stream 83 = LE, 100 = SE)
//   conv -> "ok <from-stream>" (already SE: copied unchanged) or "err <why>"
// Built by infra/gpu-box/nifconv/build.sh against the nifly commit infra/build-vm/toolchain.lock pins.
#include "NifFile.hpp"
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace nifly;

static std::vector<std::string> split(const std::string& s) {
	std::vector<std::string> o;
	std::stringstream ss(s);
	std::string t;
	while (std::getline(ss, t, '\t')) o.push_back(t);
	return o;
}

static std::string info(const std::string& in) {
	NifFile nif;
	if (nif.Load(std::filesystem::path(in)) != 0) return "err not a NIF nifly can read";
	int tri = 0, bst = 0, skin = 0, other = 0;
	for (NiShape* s : nif.GetShapes()) {
		if (s->HasType<BSTriShape>()) bst++;
		else if (s->HasType<NiTriShape>()) tri++;
		else other++;
		if (s->IsSkinned()) skin++;
	}
	return "ok " + std::to_string(nif.GetHeader().GetVersion().Stream()) + " " + std::to_string(tri) + " " +
		   std::to_string(bst) + " " + std::to_string(skin) + " " + std::to_string(other);
}

static std::string conv(const std::string& in, const std::string& out) {
	NifFile nif;
	if (nif.Load(std::filesystem::path(in)) != 0) return "err not a NIF nifly can read";
	NiVersion v = nif.GetHeader().GetVersion();
	std::filesystem::create_directories(std::filesystem::path(out).parent_path());
	if (v.IsSSE()) {
		std::filesystem::copy_file(in, out, std::filesystem::copy_options::overwrite_existing);
		return "ok 100";
	}
	if (!v.IsSK()) return "err not a Skyrim LE or SE NIF (stream " + std::to_string(v.Stream()) + ")";
	OptOptions o;
	o.targetVersion = NiVersion::getSSE();
	o.removeParallax = false;  // keep vertex colours and parallax as the author made them: only the format changes
	o.fixShaderFlags = false;
	o.calcBounds = true;
	OptResult r = nif.OptimizeFor(o);
	if (r.versionMismatch) return "err version mismatch";
	if (nif.Save(std::filesystem::path(out)) != 0) return "err save failed";
	return "ok 83";
}

int main(int argc, char** argv) {
	if (argc < 2 || std::string(argv[1]) != "--batch") { std::cerr << "usage: nifconv --batch\n"; return 2; }
	std::string line;
	while (std::getline(std::cin, line)) {
		auto f = split(line);
		std::string a;
		try {
			if (f.size() == 2 && f[0] == "info") a = info(f[1]);
			else if (f.size() == 3 && f[0] == "conv") a = conv(f[1], f[2]);
			else a = "err bad request";
		} catch (const std::exception& e) { a = std::string("err ") + e.what(); }
		std::cout << a << std::endl;
	}
	return 0;
}

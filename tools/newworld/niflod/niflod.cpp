// niflod: writes a static LOD model (<model>_lod_0.nif) laid out as Skyrim's own LOD models are (measured on
// Skyrim - Meshes, see docs/design/lod.md: a BSFadeNode root holding BSTriShape children, each with a
// BSLightingShaderProperty and its BSShaderTextureSet; no collision, no extra data, no further nodes).
// Built against ousnius/nifly (pinned in infra/build-vm/toolchain.lock) by build.sh. The geometry comes from
// tools/newworld/world/lodmodels.py, which reads the full model with nifdump and simplifies it.
//   niflod --info <in.nif>         one JSON line: the root, the block types, each shape's counts, shader and textures
//   niflod <shapes.bin> <out.nif>  the LOD model from the shapes file; one JSON line of what was written
// shapes.bin (little-endian): "NLOD", u32 shape count, then per shape: u32 vertices, u32 triangles, u32 flags
// (1 normals, 2 colours, 4 two-sided, 8 alpha test), u16 length + diffuse path, u16 length + normal-map path,
// f32 positions[3n], f32 uvs[2n], f32 normals[3n] (flag 1), f32 colours[4n] (flag 2), u16 indices[3t].
#include "NifFile.hpp"
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

using namespace nifly;

static std::string esc(const std::string& s) {
	std::string o;
	for (unsigned char c : s) {
		if (c == '"' || c == '\\') { o += '\\'; o += (char)c; }
		else if (c < 0x20 || c > 0x7e) { char b[8]; snprintf(b, sizeof b, "\\u%04x", c); o += b; }
		else o += (char)c;
	}
	return o;
}

static int info(const std::string& in) {
	NifFile nif;
	if (nif.Load(std::filesystem::path(in)) != 0) { std::cerr << "not a NIF nifly can read\n"; return 1; }
	std::ostringstream js;
	NiNode* root = nif.GetRootNode();
	js << "{\"root\":\"" << (root ? root->GetBlockName() : "") << "\",\"blocks\":[";
	std::vector<NiObject*> tree;
	nif.GetTree(tree);
	for (size_t i = 0; i < tree.size(); i++) js << (i ? "," : "") << "\"" << tree[i]->GetBlockName() << "\"";
	js << "],\"shapes\":[";
	bool first = true;
	for (NiShape* s : nif.GetShapes()) {
		std::vector<Triangle> t;
		s->GetTriangles(t);
		NiShader* sh = nif.GetShader(s);
		uint32_t f1 = 0, f2 = 0, type = 0;
		if (auto* b = dynamic_cast<BSShaderProperty*>(sh)) { f1 = b->shaderFlags1; f2 = b->shaderFlags2; }
		if (sh) type = sh->bslspShaderType;
		NiAlphaProperty* al = nif.GetAlphaProperty(s);
		if (!first) js << ",";
		first = false;
		js << "{\"name\":\"" << esc(s->name.get()) << "\",\"block\":\"" << s->GetBlockName() << "\",\"verts\":" << s->GetNumVertices()
		   << ",\"tris\":" << t.size() << ",\"shader\":\"" << (sh ? sh->GetBlockName() : "") << "\",\"flags1\":" << f1
		   << ",\"flags2\":" << f2 << ",\"shader_type\":" << type << ",\"normals\":" << (s->HasNormals() ? "true" : "false")
		   << ",\"tangents\":" << (s->HasTangents() ? "true" : "false") << ",\"colors\":" << (s->HasVertexColors() ? "true" : "false")
		   << ",\"parent\":\"" << (nif.GetParentNode(s) ? nif.GetParentNode(s)->GetBlockName() : "") << "\",\"tex\":[";
		for (int i = 0; i < 9; i++) { std::string x; nif.GetTextureSlot(s, x, i); js << (i ? "," : "") << "\"" << esc(x) << "\""; }
		js << "]";
		if (al) js << ",\"alpha\":{\"flags\":" << al->flags << ",\"threshold\":" << (int)al->threshold << "}";
		js << "}";
	}
	js << "]}";
	std::cout << js.str() << std::endl;
	return 0;
}

template <class T> static bool rd(std::istream& f, T* p, size_t n) { return (bool)f.read((char*)p, sizeof(T) * n); }

static int make(const std::string& in, const std::string& out) {
	std::ifstream f(in, std::ios::binary);
	char magic[4];
	uint32_t count = 0;
	if (!rd(f, magic, 4) || memcmp(magic, "NLOD", 4) != 0 || !rd(f, &count, 1) || !count) { std::cerr << "not a shapes file\n"; return 1; }
	NifFile dst;
	dst.Create(NiVersion::getSSE());
	{  // Skyrim's statics and their LOD models hang from a BSFadeNode (nifly's Create starts with a NiNode)
		auto root = std::make_unique<BSFadeNode>();
		root->name.get() = "Scene Root";
		dst.GetHeader().ReplaceBlock(0, std::move(root));
	}
	size_t wrote = 0;
	for (uint32_t k = 0; k < count; k++) {
		uint32_t nv, nt, flags;
		std::string tex[2];
		if (!rd(f, &nv, 1) || !rd(f, &nt, 1) || !rd(f, &flags, 1)) { std::cerr << "short shapes file\n"; return 1; }
		for (auto& t : tex) { uint16_t n; if (!rd(f, &n, 1)) return 1; t.resize(n); if (n && !rd(f, t.data(), n)) return 1; }
		if (!nv || !nt || nv > 65535) { std::cerr << "a shape with " << nv << " vertices, " << nt << " triangles\n"; return 1; }
		std::vector<Vector3> v(nv), nr;
		std::vector<Vector2> uv(nv);
		std::vector<Color4> col;
		std::vector<uint16_t> idx(nt * 3);
		bool ok = rd(f, &v[0], nv) && rd(f, &uv[0], nv);
		if (ok && (flags & 1)) { nr.resize(nv); ok = rd(f, &nr[0], nv); }
		if (ok && (flags & 2)) { col.resize(nv); ok = rd(f, &col[0], nv); }
		ok = ok && rd(f, &idx[0], nt * 3);
		if (!ok) { std::cerr << "short shapes file\n"; return 1; }
		std::vector<Triangle> tris;
		for (uint32_t i = 0; i < nt; i++) {
			if (idx[i * 3] >= nv || idx[i * 3 + 1] >= nv || idx[i * 3 + 2] >= nv) { std::cerr << "an index past the vertices\n"; return 1; }
			tris.emplace_back(idx[i * 3], idx[i * 3 + 1], idx[i * 3 + 2]);
		}
		NiShape* s = dst.CreateShapeFromData("LOD" + std::to_string(k), &v, &tris, &uv, nr.empty() ? nullptr : &nr);
		if (!s) { std::cerr << "nifly made no shape\n"; return 1; }
		if (nr.empty()) dst.CalcNormalsForShape(s, true);
		dst.CalcTangentsForShape(s);
		if (!col.empty()) { s->SetVertexColors(true); dst.SetColorsForShape(s, col); }
		dst.SetTextureSlot(s, tex[0], 0);
		if (!tex[1].empty()) dst.SetTextureSlot(s, tex[1], 1);
		auto* sh = dynamic_cast<BSLightingShaderProperty*>(dst.GetShader(s));
		if (!sh) { std::cerr << "nifly made no lighting shader\n"; return 1; }
		// a plain lit, shadowed, depth-tested surface, the flags Skyrim's own LOD models carry; of the full model
		// only what a far shape needs: two-sided, vertex colours
		sh->bslspShaderType = 0;
		sh->shaderFlags1 = 0x80400300;  // receive and cast shadows, own emit, z-buffer test: the commonest of Skyrim's own
		sh->shaderFlags2 = 0x8001 | ((flags & 4) ? SLSF2_DOUBLE_SIDED : 0) | (col.empty() ? 0 : SLSF2_VERTEX_COLORS);  // z-buffer write, env-map light fade
		if (flags & 8) {  // alpha test only: LOD has no blending and tests at 128 (dyndolod.info Mod-Authors)
			auto al = std::make_unique<NiAlphaProperty>();
			al->flags = 4844;
			al->threshold = 128;
			dst.AssignAlphaProperty(s, std::move(al));
		}
		wrote += nt;
	}
	if (dst.Save(std::filesystem::path(out)) != 0) { std::cerr << "cannot write " << out << "\n"; return 1; }
	std::cout << "{\"shapes\":" << count << ",\"tris\":" << wrote << "}" << std::endl;
	return 0;
}

int main(int argc, char** argv) {
	try {
		if (argc == 3 && std::string(argv[1]) == "--info") return info(argv[2]);
		if (argc == 3) return make(argv[1], argv[2]);
	} catch (const std::exception& x) { std::cerr << "exception: " << x.what() << "\n"; return 1; }
	std::cerr << "usage: niflod --info <in.nif> | niflod <shapes.bin> <out.nif>\n";
	return 2;
}

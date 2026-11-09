// nifdump: a NIF's drawable shapes as one flat binary the Python side turns into a GLB (tools/places/assets/nifglb.py).
// Built against ousnius/nifly (pinned in infra/build-vm/toolchain.lock) by tools/places/assets/nifdump/build.sh.
// Usage: nifdump <in.nif> <out.bin>, or nifdump --batch (stdin lines "in\tout"; one "ok" or "err <why>" per line).
// out.bin: u32 header length, the JSON header, then the arrays the header's offsets name (little-endian).
#include "NifFile.hpp"
#include <cstdio>
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

static std::string dump(const std::string& in, const std::string& out) {
	NifFile nif;
	if (nif.Load(std::filesystem::path(in)) != 0) return "not a NIF nifly can read";
	std::ostringstream js;
	std::string blob;
	auto put = [&](const void* p, size_t n) { size_t at = blob.size(); blob.append((const char*)p, n); return at; };
	js << "{\"shapes\":[";
	bool first = true;
	for (NiShape* s : nif.GetShapes()) {
		std::vector<Vector3> v;
		std::vector<Triangle> t;
		if (!nif.GetVertsForShape(s, v) || v.empty()) continue;
		s->GetTriangles(t);
		if (t.empty()) continue;
		// the shape's transform to the root: its own, then every parent node's
		MatTransform x = s->GetTransformToParent();
		bool hidden = s->flags & 1;
		for (NiNode* p = nif.GetParentNode(s); p; p = nif.GetParentNode(p)) {
			x = p->GetTransformToParent().ComposeTransforms(x);
			if (p->flags & 1) hidden = true;
		}
		float m[12];
		for (int c = 0; c < 3; c++) {
			Vector3 e(c == 0, c == 1, c == 2);
			Vector3 col = x.rotation * e * x.scale;
			m[c] = col.x; m[4 + c] = col.y; m[8 + c] = col.z;
		}
		m[3] = x.translation.x; m[7] = x.translation.y; m[11] = x.translation.z;
		std::vector<float> pos; for (auto& p : v) { pos.push_back(p.x); pos.push_back(p.y); pos.push_back(p.z); }
		std::vector<uint32_t> idx; for (auto& tr : t) { idx.push_back(tr.p1); idx.push_back(tr.p2); idx.push_back(tr.p3); }
		size_t opos = put(pos.data(), pos.size() * 4), oidx = put(idx.data(), idx.size() * 4);
		long onrm = -1, ouv = -1, ocol = -1;
		const auto* n = nif.GetNormalsForShape(s);
		if (n && n->size() == v.size()) { std::vector<float> a; for (auto& q : *n) { a.push_back(q.x); a.push_back(q.y); a.push_back(q.z); } onrm = put(a.data(), a.size() * 4); }
		const auto* uv = nif.GetUvsForShape(s);
		if (uv && uv->size() == v.size()) { std::vector<float> a; for (auto& q : *uv) { a.push_back(q.u); a.push_back(q.v); } ouv = put(a.data(), a.size() * 4); }
		const auto* cl = nif.GetColorsForShape(s);
		if (cl && cl->size() == v.size()) { std::vector<float> a; for (auto& q : *cl) { a.push_back(q.r); a.push_back(q.g); a.push_back(q.b); a.push_back(q.a); } ocol = put(a.data(), a.size() * 4); }
		NiShader* sh = nif.GetShader(s);
		std::string tex[2];
		nif.GetTextureSlot(s, tex[0], 0);
		nif.GetTextureSlot(s, tex[1], 1);
		NiAlphaProperty* al = nif.GetAlphaProperty(s);
		if (!first) js << ",";
		first = false;
		js << "{\"name\":\"" << esc(s->name.get()) << "\",\"block\":\"" << s->GetBlockName() << "\",\"verts\":" << v.size()
		   << ",\"tris\":" << t.size() << ",\"hidden\":" << (hidden ? "true" : "false")
		   << ",\"skinned\":" << (s->IsSkinned() ? "true" : "false") << ",\"m\":[";
		for (int i = 0; i < 12; i++) js << (i ? "," : "") << m[i];
		js << "],\"pos\":" << opos << ",\"idx\":" << oidx << ",\"nrm\":" << onrm << ",\"uv\":" << ouv << ",\"col\":" << ocol
		   << ",\"tex\":[\"" << esc(tex[0]) << "\",\"" << esc(tex[1]) << "\"]";
		if (sh) {
			Vector2 uo = sh->GetUVOffset(), us = sh->GetUVScale();
			js << ",\"shader\":{\"type\":\"" << sh->GetBlockName() << "\",\"two_sided\":" << (sh->IsDoubleSided() ? "true" : "false")
			   << ",\"vertex_colors\":" << (sh->HasVertexColors() ? "true" : "false")
			   << ",\"vertex_alpha\":" << (sh->HasVertexAlpha() ? "true" : "false")
			   << ",\"flags2\":" << (dynamic_cast<BSShaderProperty*>(sh) ? dynamic_cast<BSShaderProperty*>(sh)->shaderFlags2 : 0)
			   << ",\"uv_offset\":[" << uo.u << "," << uo.v << "],\"uv_scale\":[" << us.u << "," << us.v << "]}";
		}
		if (al) js << ",\"alpha\":{\"flags\":" << al->flags << ",\"threshold\":" << (int)al->threshold << "}";
		js << "}";
	}
	js << "]}";
	std::string h = js.str();
	std::ofstream f(out, std::ios::binary);
	uint32_t hl = (uint32_t)h.size();
	f.write((const char*)&hl, 4);
	f.write(h.data(), h.size());
	f.write(blob.data(), blob.size());
	return f ? "" : "cannot write " + out;
}

int main(int argc, char** argv) {
	if (argc == 3) {
		std::string e;
		try { e = dump(argv[1], argv[2]); } catch (const std::exception& x) { e = std::string("exception: ") + x.what(); }
		if (!e.empty()) { std::cerr << e << "\n"; return 1; }
		return 0;
	}
	if (argc == 2 && std::string(argv[1]) == "--batch") {
		std::string line;
		while (std::getline(std::cin, line)) {
			auto tab = line.find('\t');
			std::string e = "bad line";
			if (tab != std::string::npos) {
				try { e = dump(line.substr(0, tab), line.substr(tab + 1)); } catch (const std::exception& x) { e = std::string("exception: ") + x.what(); } catch (...) { e = "exception"; }
			}
			std::cout << (e.empty() ? "ok" : "err " + e) << std::endl;
		}
		return 0;
	}
	std::cerr << "usage: nifdump <in.nif> <out.bin> | nifdump --batch\n";
	return 2;
}

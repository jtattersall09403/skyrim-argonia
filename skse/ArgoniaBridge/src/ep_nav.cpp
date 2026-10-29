// nav and booth (0.3 §a).
//   nav <x y z | player> <x y z>   a navmesh path over the loaded cells (protocol/nav.h), or the failure and why
//   booth place <base form id>     place one copy of a base record ahead of the player (or at the booth's centre),
//                                  answer its centre and bounding radius
//   booth view <0..5>              free camera framing the placed copy: front, right, back, left, top, three-quarter
//   booth clear                    camera back, the copy deleted
// tools/bridge.py's booth() runs place, the six views with a still each, and clear.
#include "bridge.h"
#include "nav.h"

namespace argonia::bridge {
namespace {

nav::Mesh copy_mesh(RE::NavMesh* m) {
  nav::Mesh out;
  out.id = m->GetFormID();
  out.vertices.reserve(m->vertices.size());
  for (auto& v : m->vertices) out.vertices.push_back({v.location.x, v.location.y, v.location.z});
  using F = RE::BSNavmeshTriangle::TriangleFlag;
  const F link_flags[3] = {F::kEdge0_Link, F::kEdge1_Link, F::kEdge2_Link};
  for (auto& t : m->triangles) {
    nav::Triangle tri;
    for (int e = 0; e < 3; ++e) {
      tri.v[e] = t.vertices[e];
      tri.next[e] = t.triangles[e];
      tri.link[e] = t.triangleFlags.any(link_flags[e]);
    }
    tri.deleted = t.triangleFlags.any(F::kDeleted);
    out.triangles.push_back(tri);
  }
  for (auto& x : m->extraEdgeInfo)
    out.portals.push_back({x.portal.otherMeshID, x.portal.triangle});
  return out;
}

std::vector<nav::Mesh> loaded_meshes() {
  std::vector<nav::Mesh> meshes;
  auto add_cell = [&](RE::TESObjectCELL* cell) {
    if (!cell || !cell->IsAttached()) return;
    auto* arr = cell->GetRuntimeData().navMeshes;
    if (!arr) return;
    for (auto& m : arr->navMeshes)
      if (m) meshes.push_back(copy_mesh(m.get()));
  };
  if (auto* tes = RE::TES::GetSingleton()) {
    if (tes->interiorCell) add_cell(tes->interiorCell);
    else tes->ForEachCell(add_cell);
  }
  return meshes;
}

std::optional<nav::Vec3> point(const Request& req, std::size_t& i) {
  if (i < req.args.size() && req.args[i] == "player") {
    ++i;
    auto* p = player_in_world();
    if (!p) return std::nullopt;
    auto pos = p->GetPosition();
    return nav::Vec3{pos.x, pos.y, pos.z};
  }
  if (i + 3 > req.args.size()) return std::nullopt;
  auto x = to_number(req.args[i]), y = to_number(req.args[i + 1]), z = to_number(req.args[i + 2]);
  i += 3;
  if (!x || !y || !z) return std::nullopt;
  return nav::Vec3{float(*x), float(*y), float(*z)};
}

std::string nav_ep(const Request& req) {
  return on_main_thread("nav", [req] {
    if (!player_in_world()) return reply_error("nav", "no player in a world (main menu or loading)");
    std::size_t i = 0;
    auto a = point(req, i), b = point(req, i);
    if (!a || !b || i != req.args.size()) return reply_error("nav", "usage: nav <x y z | player> <x y z>");
    auto meshes = loaded_meshes();
    if (meshes.empty()) return reply_error("nav", "no navmesh in the loaded cells");
    auto r = nav::find_path(meshes, *a, *b);
    if (!r.found)
      return reply_error("nav", r.reason + " (" + std::to_string(meshes.size()) + " meshes, " +
                                    std::to_string(r.triangles_searched) + " triangles searched)");
    std::string pts = "[";
    for (auto& w : r.waypoints) pts += (pts.size() > 1 ? "," : "") + ("[" + json_number(w.x) + "," + json_number(w.y) + "," + json_number(w.z) + "]");
    return reply_ok("nav", JsonObject()
                               .num("length", r.length)
                               .integer("meshes", static_cast<long long>(meshes.size()))
                               .integer("triangles_searched", static_cast<long long>(r.triangles_searched))
                               .raw("waypoints", pts + "]")
                               .done());
  }, 10s);
}

// --- booth --------------------------------------------------------------------------------------------------
RE::ObjectRefHandle g_booth;
RE::NiPoint3 g_centre;
float g_radius = 0;
bool g_free_asked = false;

std::string booth(const Request& req) {
  const std::string usage = "usage: booth place <base form id> | view <0..5> | clear";
  if (req.args.empty()) return reply_error("booth", usage);
  auto what = req.args[0];
  if (what == "place") {
    if (req.args.size() != 2) return reply_error("booth", usage);
    auto id = to_form_id(req.args[1]);
    if (!id) return reply_error("booth", "a base form id in hex");
    return on_main_thread("booth", [id = *id] {
      auto* p = player_in_world();
      if (!p) return reply_error("booth", "no player in a world (main menu or loading)");
      auto* f = RE::TESForm::LookupByID(id);
      auto* base = f && f->IsBoundObject() ? static_cast<RE::TESBoundObject*>(f) : nullptr;
      if (!base) return reply_error("booth", "no base object with a model at " + JsonObject().hex("id", id).done());
      if (auto old = g_booth.get()) {
        old->Disable();
        old->SetDelete(true);
      }
      auto ref = p->PlaceObjectAtMe(base, false);
      if (!ref) return reply_error("booth", "the game would not place it");
      float yaw = p->GetAngleZ();
      auto at = p->GetPosition() + RE::NiPoint3{std::sin(yaw) * 400.0f, std::cos(yaw) * 400.0f, 0.0f};
      ref->SetPosition(at);
      auto lo = ref->GetBoundMin(), hi = ref->GetBoundMax();
      g_centre = at + RE::NiPoint3{(lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2};
      g_radius = (std::max)(32.0f, (hi - lo).Length() / 2);  // parenthesised: <Windows.h> max
      g_booth = ref->CreateRefHandle();
      return reply_ok("booth", JsonObject()
                                   .hex("ref", ref->GetFormID())
                                   .hex("base", id)
                                   .str("name", base->GetName())
                                   .raw("centre", JsonObject().num("x", g_centre.x).num("y", g_centre.y).num("z", g_centre.z).done())
                                   .num("radius", g_radius)
                                   .done());
    });
  }
  if (what == "view") {
    auto v = req.args.size() == 2 ? to_number(req.args[1]) : std::nullopt;
    if (!v || *v < 0 || *v > 5 || *v != std::floor(*v)) return reply_error("booth", "view 0..5");
    int view = int(*v);
    return on_main_thread("booth", [view] {
      if (!g_booth.get()) return reply_error("booth", "nothing placed: booth place <id> first");
      auto* cam = RE::PlayerCamera::GetSingleton();
      if (!cam) return reply_error("booth", "no camera");
      // The switch may land a frame later, so it is asked for once and the client asks for the view again.
      if (!cam->IsInFreeCameraMode()) {
        if (!g_free_asked) cam->ToggleFreeCameraMode(false);
        g_free_asked = true;
        return reply_error("booth", "the free camera is starting; ask for the view again");
      }
      // Frame where the object is now: a placed weapon or clutter falls under physics after `place`, so its 3D's
      // world bound replaces the centre taken at placement (the first live booth aimed above the fallen sword).
      if (auto ref = g_booth.get()) {
        if (auto* obj = ref->Get3D(); obj && obj->worldBound.radius > 0) {
          g_centre = obj->worldBound.center;
          g_radius = (std::max)(32.0f, obj->worldBound.radius);
        }
      }
      auto* fc = static_cast<RE::FreeCameraState*>(cam->currentState.get());
      if (!fc) return reply_error("booth", "no free camera state");
      // yaw around the object (0 front = looking north from the south), and pitch; top looks straight down.
      constexpr float pi = 3.14159265f;
      const float yaws[6] = {0, -pi / 2, pi, pi / 2, 0, pi / 4};
      // A little above the object (a placed object lies on the floor) and never nearer than 160 units: the first
      // live views at 0.1 rad and 2.6 radii sat in the grass beside the sword.
      const float pitches[6] = {0.3f, 0.3f, 0.3f, 0.3f, pi / 2 - 0.05f, 0.6f};
      float d = (std::max)(160.0f, g_radius * 3.0f), yaw = yaws[view], pitch = pitches[view];
      RE::NiPoint3 eye = g_centre + RE::NiPoint3{-std::sin(yaw) * std::cos(pitch) * d, -std::cos(yaw) * std::cos(pitch) * d,
                                                 std::sin(pitch) * d};
      fc->translation = eye;
      fc->rotation.x = pitch;  // pitch down is positive
      fc->rotation.y = yaw;
      return reply_ok("booth", JsonObject().integer("view", view).raw("eye", JsonObject().num("x", eye.x).num("y", eye.y).num("z", eye.z).done()).done());
    });
  }
  if (what == "clear") {
    return on_main_thread("booth", [] {
      auto* cam = RE::PlayerCamera::GetSingleton();
      if (cam && cam->IsInFreeCameraMode()) cam->ToggleFreeCameraMode(false);
      bool had = false;
      if (auto ref = g_booth.get()) {
        ref->Disable();
        ref->SetDelete(true);
        had = true;
      }
      g_booth = {};
      g_free_asked = false;
      return reply_ok("booth", JsonObject().boolean("cleared", had).done());
    });
  }
  return reply_error("booth", usage);
}

const Register r_nav{"nav", &nav_ep};
const Register r_booth{"booth", &booth};

}  // namespace
}  // namespace argonia::bridge

// L2: the `nav` search finds a path across a shared edge and a portal, and every failure names its cause.
#include "check.h"
#include "nav.h"

using namespace argonia::bridge::nav;

namespace {
// Two unit squares (2 triangles each) side by side in x; square B is its own mesh joined by a portal.
std::vector<Mesh> two_meshes(bool joined) {
  Mesh a{0x100, {{0, 0, 0}, {100, 0, 0}, {100, 100, 0}, {0, 100, 0}}, {}, {}};
  // t0: 0-1-2 (edge 1-2 is x=100: the portal); t1: 0-2-3. Shared edge 0-2: t0 edge 2 (2-0), t1 edge 0 (0-2).
  a.triangles.push_back(Triangle{{0, 1, 2}, {kNone, joined ? std::uint16_t(0) : kNone, 1}, {false, joined, false}});
  a.triangles.push_back(Triangle{{0, 2, 3}, {0, kNone, kNone}, {}});
  a.portals.push_back(Portal{0x200, 1});
  Mesh b{0x200, {{100, 0, 0}, {200, 0, 0}, {200, 100, 0}, {100, 100, 0}}, {}, {}};
  b.triangles.push_back(Triangle{{0, 1, 2}, {kNone, kNone, 1}, {}});
  b.triangles.push_back(Triangle{{0, 2, 3}, {0, kNone, joined ? std::uint16_t(0) : kNone}, {false, false, joined}});
  b.portals.push_back(Portal{0x100, 0});
  return {a, b};
}

void locates_the_triangle_under_a_point() {
  auto m = two_meshes(true);
  auto s = locate(m, {80, 10, 5});
  CHECK(s && s->mesh == 0 && s->triangle == 0);
  CHECK(!locate(m, {80, 10, 400}));   // too far above
  CHECK(!locate(m, {-5, 10, 0}));     // outside
}

void finds_a_path_across_the_portal() {
  auto r = find_path(two_meshes(true), {10, 50, 0}, {190, 20, 0});
  CHECK(r.found);
  CHECK(r.waypoints.size() >= 3);
  CHECK(r.length >= 180.0 && r.length < 260.0);
}

void same_triangle_is_a_straight_line() {
  auto r = find_path(two_meshes(true), {60, 10, 0}, {90, 20, 0});
  CHECK(r.found && r.waypoints.size() == 2);
}

void failures_name_their_cause() {
  auto cut = find_path(two_meshes(false), {10, 50, 0}, {190, 20, 0});
  CHECK(!cut.found && cut.reason.find("no navmesh connection") != std::string::npos);
  auto off = find_path(two_meshes(true), {-50, 50, 0}, {190, 20, 0});
  CHECK(!off.found && off.reason.find("start") != std::string::npos);
  auto off2 = find_path(two_meshes(true), {10, 50, 0}, {500, 20, 0});
  CHECK(!off2.found && off2.reason.find("end") != std::string::npos);
  auto unloaded = two_meshes(true);
  unloaded.pop_back();  // the far mesh's cell is not loaded
  CHECK(!find_path(unloaded, {10, 50, 0}, {150, 20, 0}).found);
}
}  // namespace

void nav_tests() {
  locates_the_triangle_under_a_point();
  finds_a_path_across_the_portal();
  same_triangle_is_a_straight_line();
  failures_name_their_cause();
}

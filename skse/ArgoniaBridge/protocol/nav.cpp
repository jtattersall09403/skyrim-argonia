#include "nav.h"

#include <cmath>
#include <queue>
#include <unordered_map>

namespace argonia::bridge::nav {
namespace {

double dist(Vec3 a, Vec3 b) {
  double dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
  return std::sqrt(dx * dx + dy * dy + dz * dz);
}

Vec3 mid(Vec3 a, Vec3 b) { return {(a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2}; }

// Barycentric test in x, y; returns the plane's z at p when inside (edges included).
std::optional<float> z_in(Vec3 a, Vec3 b, Vec3 c, Vec3 p) {
  double d = (b.y - c.y) * (a.x - c.x) + (c.x - b.x) * (a.y - c.y);
  if (std::fabs(d) < 1e-9) return std::nullopt;
  double l1 = ((b.y - c.y) * (p.x - c.x) + (c.x - b.x) * (p.y - c.y)) / d;
  double l2 = ((c.y - a.y) * (p.x - c.x) + (a.x - c.x) * (p.y - c.y)) / d;
  double l3 = 1 - l1 - l2;
  constexpr double eps = -1e-6;
  if (l1 < eps || l2 < eps || l3 < eps) return std::nullopt;
  return static_cast<float>(l1 * a.z + l2 * b.z + l3 * c.z);
}

std::uint64_t key(std::size_t mesh, std::uint16_t tri) { return (std::uint64_t(mesh) << 16) | tri; }

}  // namespace

std::optional<Spot> locate(const std::vector<Mesh>& meshes, Vec3 p, float max_dz) {
  std::optional<Spot> best;
  float best_dz = max_dz;
  for (std::size_t m = 0; m < meshes.size(); ++m) {
    const auto& mesh = meshes[m];
    for (std::size_t t = 0; t < mesh.triangles.size(); ++t) {
      const auto& tri = mesh.triangles[t];
      if (tri.deleted || tri.v[0] >= mesh.vertices.size() || tri.v[1] >= mesh.vertices.size() ||
          tri.v[2] >= mesh.vertices.size())
        continue;
      auto z = z_in(mesh.vertices[tri.v[0]], mesh.vertices[tri.v[1]], mesh.vertices[tri.v[2]], p);
      if (!z) continue;
      float dz = std::fabs(*z - p.z);
      if (dz <= best_dz) {
        best_dz = dz;
        best = Spot{m, static_cast<std::uint16_t>(t)};
      }
    }
  }
  return best;
}

Result find_path(const std::vector<Mesh>& meshes, Vec3 a, Vec3 b, std::size_t max_expanded) {
  Result r;
  auto sa = locate(meshes, a), sb = locate(meshes, b);
  if (!sa) {
    r.reason = "the start is not on a loaded navmesh";
    return r;
  }
  if (!sb) {
    r.reason = "the end is not on a loaded navmesh";
    return r;
  }
  std::unordered_map<std::uint32_t, std::size_t> by_id;
  for (std::size_t m = 0; m < meshes.size(); ++m) by_id[meshes[m].id] = m;

  struct Node {
    double g;
    Vec3 at;           // where the path enters this triangle (an edge midpoint, or the start)
    std::uint64_t from;  // the previous node's key, or ~0
  };
  std::unordered_map<std::uint64_t, Node> seen;
  using Item = std::pair<double, std::uint64_t>;
  std::priority_queue<Item, std::vector<Item>, std::greater<>> open;
  auto start = key(sa->mesh, sa->triangle), goal = key(sb->mesh, sb->triangle);
  seen[start] = Node{0, a, ~0ull};
  open.push({dist(a, b), start});
  while (!open.empty()) {
    auto [f, k] = open.top();
    open.pop();
    const Node cur = seen[k];
    if (f > cur.g + dist(cur.at, b) + 1e-6) continue;  // a stale entry
    if (k == goal) {
      std::vector<Vec3> rev{b};
      for (auto at = k; at != ~0ull; at = seen[at].from) rev.push_back(seen[at].at);
      r.waypoints.assign(rev.rbegin(), rev.rend());
      for (std::size_t i = 1; i < r.waypoints.size(); ++i) r.length += dist(r.waypoints[i - 1], r.waypoints[i]);
      r.found = true;
      return r;
    }
    if (++r.triangles_searched > max_expanded) {
      r.reason = "search stopped after " + std::to_string(max_expanded) + " triangles";
      return r;
    }
    std::size_t m = k >> 16;
    const auto& mesh = meshes[m];
    const auto& tri = mesh.triangles[k & 0xFFFF];
    for (int e = 0; e < 3; ++e) {
      if (tri.next[e] == kNone) continue;
      std::size_t nm = m;
      std::uint16_t nt = tri.next[e];
      if (tri.link[e]) {
        if (tri.next[e] >= mesh.portals.size()) continue;
        auto& p = mesh.portals[tri.next[e]];
        auto it = by_id.find(p.other_mesh);
        if (it == by_id.end()) continue;  // a mesh in a cell that is not loaded
        nm = it->second;
        nt = p.triangle;
      }
      if (nt >= meshes[nm].triangles.size() || meshes[nm].triangles[nt].deleted) continue;
      Vec3 edge = mid(mesh.vertices[tri.v[e]], mesh.vertices[tri.v[(e + 1) % 3]]);
      double g = cur.g + dist(cur.at, edge);
      auto nk = key(nm, nt);
      auto it = seen.find(nk);
      if (it != seen.end() && it->second.g <= g) continue;
      seen[nk] = Node{g, edge, k};
      open.push({g + dist(edge, b), nk});
    }
  }
  r.reason = "no navmesh connection between the two points among the loaded cells";
  return r;
}

}  // namespace argonia::bridge::nav

// The bridge's `nav` search (DEV ONLY, 0.3 §a), pure so it is unit-tested on the build VM: A* over the loaded
// navmesh triangles, within a mesh by shared edges and across meshes by edge portals, from the triangle under one
// point to the triangle under another. Our own build over the game's navmesh data (the plugin copies the loaded
// cells' meshes into these structs on the main thread), not the game's path planner: it answers "is there a
// navmesh path, and how long", or why not.
#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace argonia::bridge::nav {

struct Vec3 {
  float x = 0, y = 0, z = 0;
};

inline constexpr std::uint16_t kNone = 0xFFFF;

struct Triangle {
  std::uint16_t v[3]{};
  // Per edge (v0-v1, v1-v2, v2-v0): a triangle of this mesh, or kNone; when `link[e]` the value is an index into
  // Mesh::portals instead (the game's kEdgeN_Link flags).
  std::uint16_t next[3]{kNone, kNone, kNone};
  bool link[3]{};
  bool deleted = false;
};

struct Portal {
  std::uint32_t other_mesh = 0;  // form id
  std::uint16_t triangle = kNone;
};

struct Mesh {
  std::uint32_t id = 0;  // the NavMesh form id
  std::vector<Vec3> vertices;
  std::vector<Triangle> triangles;
  std::vector<Portal> portals;
};

struct Spot {
  std::size_t mesh = 0;  // index into the meshes vector
  std::uint16_t triangle = 0;
};

struct Result {
  bool found = false;
  std::string reason;          // why not, when !found
  std::vector<Vec3> waypoints;  // start, the edge midpoints crossed, end
  double length = 0;            // along the waypoints, game units
  std::size_t triangles_searched = 0;
};

// The triangle whose 2D (x, y) footprint holds p and whose plane is nearest p in z, within max_dz; else none.
std::optional<Spot> locate(const std::vector<Mesh>& meshes, Vec3 p, float max_dz = 256.0f);

// A* from a to b; every failure names its cause: a point off the navmesh, or no connection among loaded meshes.
Result find_path(const std::vector<Mesh>& meshes, Vec3 a, Vec3 b, std::size_t max_expanded = 200000);

}  // namespace argonia::bridge::nav

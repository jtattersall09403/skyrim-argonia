#include <cstdio>

#include "backstab.h"
#include "ini.h"

using namespace argonia::backstab;

static int failed = 0;
#define CHECK(c) do { if (!(c)) { std::fprintf(stderr, "FAIL %s:%d %s\n", __FILE__, __LINE__, #c); ++failed; } } while (0)

static double rad(double d) { return d * kPi / 180.0; }

int main() {
  const Rule r{};
  const Pose target{0, 0, 0, 0};  // faces north (+y); its back is -y
  // straight behind, 150 units, facing north: ok
  CHECK(check({0, -150, 0, 0}, target, r) == Why::Ok);
  // in front, facing it: not behind
  CHECK(check({0, 150, 0, rad(180)}, target, r) == Why::NotBehind);
  // beside (90 degrees off the back): not behind; 55 degrees off: behind; 65 off: not
  CHECK(check({150, 0, 0, 0}, target, r) == Why::NotBehind);
  CHECK(check({150 * std::sin(rad(55)), -150 * std::cos(rad(55)), 0, 0}, target, r) == Why::Ok);
  CHECK(check({150 * std::sin(rad(65)), -150 * std::cos(rad(65)), 0, 0}, target, r) == Why::NotBehind);
  // behind but facing away: not facing; 40 degrees turned is fine, 50 is not
  CHECK(check({0, -150, 0, rad(180)}, target, r) == Why::NotFacing);
  CHECK(check({0, -150, 0, rad(40)}, target, r) == Why::Ok);
  CHECK(check({0, -150, 0, rad(-50)}, target, r) == Why::NotFacing);
  // headings wrap: 350 against 10 degrees is 20 apart
  CHECK(std::fabs(heading_diff_deg(rad(350), rad(10)) - 20.0) < 1e-9);
  CHECK(check({0, -150, 0, rad(350)}, Pose{0, 0, 0, rad(10)}, r) == Why::Ok);
  // too far, too high
  CHECK(check({0, -250, 0, 0}, target, r) == Why::TooFar);
  CHECK(check({0, -150, 150, 0}, target, r) == Why::TooHighOrLow);
  // a target facing east (+x): behind is -x
  CHECK(check({-150, 0, 0, rad(90)}, Pose{0, 0, 0, rad(90)}, r) == Why::Ok);
  CHECK(check({150, 0, 0, rad(90)}, Pose{0, 0, 0, rad(90)}, r) == Why::NotBehind);
  // the ini keys
  argonia::dodgebuffer::Settings s;
  auto unknown = argonia::dodgebuffer::parse_ini(
      "bBackstab=0\nbBackstabExecute=0\nfBackstabReach=180\nfBackstabHeight=90\nfBackstabBehindDegrees=50\n"
      "fBackstabFacingDegrees=40\n",
      s);
  CHECK(unknown.empty());
  CHECK(!s.backstab && !s.backstab_execute && s.backstab_reach == 180 && s.backstab_height == 90);
  CHECK(s.backstab_behind_deg == 50 && s.backstab_facing_deg == 40);
  if (failed) return 1;
  std::puts("backstab: all checks passed");
  return 0;
}

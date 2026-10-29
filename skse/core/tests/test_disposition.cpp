// L2: disposition (76 §125, native map G18.3): the base, the bands at their edges, changes clamped, S18c's 20 and 80,
// and the `dispositions` family payload.
#include "check.h"
#include "argonia/core/disposition.h"

using namespace argonia::core::disposition;

int main() {
  CHECK(base({50}, {50}) == 50);
  CHECK(base({50}, {70}) == 60);                                  // +0.5 x (Per - 50)
  CHECK(base({50}, {30}) == 40);
  CHECK(base({40}, {50, 10, 5, -3, 2}) == 54);                    // the priors add
  CHECK(base({90}, {100, 30}) == 100);                            // clamped
  CHECK(base({0}, {0, -50}) == 0);
  CHECK(band(0) == DispositionBand::low && band(29) == DispositionBand::low);
  CHECK(band(30) == DispositionBand::mid && band(69) == DispositionBand::mid);
  CHECK(band(70) == DispositionBand::high && band(100) == DispositionBand::high);
  CHECK(band(20) != band(80));                                    // S18c's two variants
  CHECK(apply(95, {10}) == 100 && apply(5, {-10}) == 0 && apply(50, {-20}) == 30);
  CHECK(clamp(49.5) == 50);

  Table t{{0x0100ABCD, 20}, {0x0100ABCE, 80}};
  auto back = decode(encode(t));
  CHECK(back && *back == t);
  CHECK(decode(encode({}))->empty());
  auto bad = encode({{1, 50}});
  bad[8] = 200;  // 200 is outside 0-100
  CHECK(!decode(bad));
  auto dup = encode(t);
  for (int i = 0; i < 4; ++i) dup[12 + i] = dup[4 + i];  // the same person twice
  CHECK(!decode(dup));
  auto trunc = encode(t);
  trunc.pop_back();
  CHECK(!decode(trunc));
  return TEST_MAIN_RESULT("core.disposition");
}

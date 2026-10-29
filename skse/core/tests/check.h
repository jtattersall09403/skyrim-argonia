// The smallest test harness: CHECK counts failures with file:line, main returns the count. No dependency, so
// the gate needs only a C++ compiler (and CMake when present).
#pragma once
#include <cstdio>

namespace argonia::test {
inline int failures = 0;
}

#define CHECK(cond)                                                              \
  do {                                                                           \
    if (!(cond)) {                                                               \
      std::fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__, #cond); \
      ++::argonia::test::failures;                                               \
    }                                                                            \
  } while (0)

#define TEST_MAIN_RESULT(name)                                                            \
  (std::printf("%s: %s (%d failed)\n", name, ::argonia::test::failures ? "FAIL" : "ok", \
               ::argonia::test::failures),                                                \
   ::argonia::test::failures ? 1 : 0)

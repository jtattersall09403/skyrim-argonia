#include "argonia/core/roundtrip.h"

#include <algorithm>
#include <cmath>

namespace argonia::core::roundtrip {

Item u8(std::string name, double lo, double hi) { return {Kind::u8, std::move(name), lo, hi, 0, false, {}}; }
Item u32(std::string name, double lo, double hi) { return {Kind::u32, std::move(name), lo, hi, 0, false, {}}; }
Item u64(std::string name, double lo, double hi) { return {Kind::u64, std::move(name), lo, hi, 0, false, {}}; }
Item i32(std::string name, double lo, double hi) { return {Kind::i32, std::move(name), lo, hi, 0, false, {}}; }
Item f64(std::string name, double lo, double hi) { return {Kind::f64, std::move(name), lo, hi, 0, false, {}}; }
Item str(std::string name) { return {Kind::str, std::move(name), 0, 0, 0, false, {}}; }
Item repeat(std::string name, std::size_t count, Layout of) {
  return {Kind::repeat, std::move(name), 0, 0, std::uint32_t(count), false, std::move(of)};
}
Item list(std::string name, std::size_t max_count, Layout of, bool keyed) {
  return {Kind::list, std::move(name), 0, 0, std::uint32_t(max_count), keyed, std::move(of)};
}
Item flag(std::string name, Layout of) { return {Kind::flag, std::move(name), 0, 0, 0, false, std::move(of)}; }

namespace {

// splitmix64: small, seedable, the same on every compiler.
struct Rng {
  std::uint64_t s;
  std::uint64_t next() {
    std::uint64_t z = (s += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
  }
  double unit() { return double(next() >> 11) / 9007199254740992.0; }
  // An integer in [lo, hi]; the ends are drawn often, since they are where layouts break.
  double whole(double lo, double hi) {
    const std::uint64_t pick = next() % 8;
    if (pick == 0) return lo;
    if (pick == 1) return hi;
    return std::min(hi, lo + std::floor(unit() * (hi - lo + 1)));
  }
};

bool is_int(Kind k) { return k == Kind::u8 || k == Kind::u32 || k == Kind::u64 || k == Kind::i32; }

void put_number(cosave::Writer& w, Kind k, double v) {
  switch (k) {
    case Kind::u8: w.u8(std::uint8_t(v)); break;
    case Kind::u32: w.u32(std::uint32_t(v)); break;
    case Kind::u64: w.u64(std::uint64_t(v)); break;
    case Kind::i32: w.i32(std::int32_t(v)); break;
    case Kind::f64: w.f64(v); break;
    default: break;
  }
}

void sample_into(cosave::Writer& w, const Layout& layout, Rng& rng, const double* key);

void sample_item(cosave::Writer& w, const Item& it, Rng& rng) {
  switch (it.kind) {
    case Kind::u8: case Kind::u32: case Kind::u64: case Kind::i32:
      put_number(w, it.kind, rng.whole(it.lo, it.hi));
      break;
    case Kind::f64: {
      const double pick = double(rng.next() % 8);
      put_number(w, it.kind, pick == 0 ? it.lo : pick == 1 ? it.hi : it.lo + rng.unit() * (it.hi - it.lo));
      break;
    }
    case Kind::str: {
      std::string s(rng.next() % 13, 'a');
      for (auto& c : s) c = char('a' + rng.next() % 26);
      w.str(s);
      break;
    }
    case Kind::repeat:
      for (std::uint32_t i = 0; i < it.count; ++i) sample_into(w, it.of, rng, nullptr);
      break;
    case Kind::list: {
      const std::uint32_t n = std::uint32_t(rng.next() % (std::min<std::uint32_t>(it.count, 4) + 1));
      w.u32(n);
      const Item& k = it.of.front();
      double key = k.lo;
      for (std::uint32_t i = 0; i < n; ++i) {
        if (it.keyed) {
          // Keys rise from lo in steps of 1..1000, which fits any key range wider than a few thousand.
          key = (i == 0 ? k.lo : key + 1) + double(rng.next() % 1000);
          key = std::min(key, k.hi - double(n - 1 - i));
        }
        sample_into(w, it.of, rng, it.keyed ? &key : nullptr);
      }
      break;
    }
    case Kind::flag: {
      const bool on = (rng.next() % 2) != 0;
      w.u8(on ? 1 : 0);
      if (on) sample_into(w, it.of, rng, nullptr);
      break;
    }
  }
}

void sample_into(cosave::Writer& w, const Layout& layout, Rng& rng, const double* key) {
  for (std::size_t i = 0; i < layout.size(); ++i) {
    if (i == 0 && key) put_number(w, layout[0].kind, *key);
    else sample_item(w, layout[i], rng);
  }
}

struct Walker {
  cosave::Reader r;
  std::string err;

  bool fail(const std::string& path, const std::string& why) { err = path + ": " + why; return false; }

  bool number(const Item& it, const std::string& path, double& out) {
    std::optional<double> v;
    switch (it.kind) {
      case Kind::u8: if (auto x = r.u8()) v = double(*x); break;
      case Kind::u32: if (auto x = r.u32()) v = double(*x); break;
      case Kind::u64: if (auto x = r.u64()) v = double(*x); break;
      case Kind::i32: if (auto x = r.i32()) v = double(*x); break;
      case Kind::f64: if (auto x = r.f64()) v = *x; break;
      default: break;
    }
    if (!v) return fail(path, "ends early");
    if (!(*v >= it.lo && *v <= it.hi)) return fail(path, "outside its range");
    out = *v;
    return true;
  }

  bool items(const Layout& layout, const std::string& path, double* first) {
    for (std::size_t i = 0; i < layout.size(); ++i) {
      const Item& it = layout[i];
      const std::string p = path + "." + it.name;
      if (is_int(it.kind) || it.kind == Kind::f64) {
        double v = 0;
        if (!number(it, p, v)) return false;
        if (i == 0 && first) *first = v;
      } else if (it.kind == Kind::str) {
        if (!r.str()) return fail(p, "ends early");
      } else if (it.kind == Kind::repeat) {
        for (std::uint32_t k = 0; k < it.count; ++k)
          if (!items(it.of, p + "[" + std::to_string(k) + "]", nullptr)) return false;
      } else if (it.kind == Kind::list) {
        auto n = r.u32();
        if (!n) return fail(p, "ends early");
        if (*n > it.count) return fail(p, "holds more than " + std::to_string(it.count));
        double prev = 0;
        for (std::uint32_t k = 0; k < *n; ++k) {
          double key = 0;
          if (!items(it.of, p + "[" + std::to_string(k) + "]", &key)) return false;
          if (it.keyed && k > 0 && !(key > prev)) return fail(p, "keys do not rise");
          prev = key;
        }
      } else if (it.kind == Kind::flag) {
        auto f = r.u8();
        if (!f || *f > 1) return fail(p, "flag is not 0 or 1");
        if (*f && !items(it.of, p, nullptr)) return false;
      }
    }
    return true;
  }
};

std::string hex4(std::uint32_t id) { return families::fourcc_name(id); }

}  // namespace

Bytes sample(const Layout& layout, std::uint64_t seed) {
  Rng rng{seed};
  cosave::Writer w;
  sample_into(w, layout, rng, nullptr);
  return w.take();
}

std::optional<std::string> conforms(const Layout& layout, std::span<const std::uint8_t> bytes) {
  Walker w{cosave::Reader(bytes), {}};
  if (!w.items(layout, "payload", nullptr)) return w.err;
  if (!w.r.done()) return std::string("payload: bytes left after the last field");
  return std::nullopt;
}

std::vector<std::string> check(families::Registry& reg, const FamilySchema& schema, int samples) {
  std::vector<std::string> out;
  const std::string name = "family " + hex4(schema.id);
  auto bad = [&](const std::string& why) { out.push_back(name + ": " + why); };
  const families::Family* f = reg.find(schema.id);
  if (!f) { bad("has a schema but is not registered"); return out; }
  if (schema.versions.empty()) { bad("its schema has no version"); return out; }
  if (f->version != schema.current())
    bad("writes version " + std::to_string(f->version) + ", its schema's newest is " + std::to_string(schema.current()));
  const Layout& now = schema.versions.back().layout;

  for (int s = 0; s < samples; ++s) {
    const Bytes p = sample(now, std::uint64_t(s) + 1);
    const std::string at = " (sample " + std::to_string(s) + ")";
    if (auto why = conforms(now, p)) { bad("the sampler broke its own layout: " + *why + at); return out; }
    families::Report r = reg.load(schema.id, f->version, p);
    if (!r.ok()) { bad("a payload of its layout was refused: " + r.message + at); continue; }
    const Bytes q = f->save();
    if (q != p) {
      std::size_t k = 0;
      while (k < p.size() && k < q.size() && p[k] == q[k]) ++k;
      bad("save -> load -> compare differs at byte " + std::to_string(k) + at);
    }
    if (!p.empty()) {
      Bytes cut(p.begin(), p.end() - 1);
      if (reg.load(schema.id, f->version, cut).ok()) bad("a truncated payload was accepted" + at);
    }
    Bytes padded = p;
    padded.push_back(0);
    if (reg.load(schema.id, f->version, padded).ok()) bad("a payload with a trailing byte was accepted" + at);
  }

  f->reset();
  const Bytes z = f->save();
  if (auto why = conforms(now, z)) bad("the reset state does not fit its layout: " + *why);
  else if (!reg.load(schema.id, f->version, z).ok() || f->save() != z) bad("the reset state does not round-trip");

  for (std::size_t i = 0; i + 1 < schema.versions.size(); ++i) {
    const VersionSchema& old = schema.versions[i];
    const std::string v = std::to_string(old.version);
    for (int s = 0; s < samples; ++s) {
      const Bytes p = sample(old.layout, std::uint64_t(s) + 1000);
      families::Report r = reg.load(schema.id, old.version, p);
      if (old.migrates) {
        if (r.status != families::Status::migrated) { bad("version " + v + " did not migrate: " + r.message); break; }
        if (auto why = conforms(now, f->save())) { bad("version " + v + " migrated to a payload off the layout: " + *why); break; }
      } else {
        const std::string want = "no migration from version " + v;
        if (r.status != families::Status::refused_no_migration || r.message.find(want) == std::string::npos) {
          bad("version " + v + " has no migration but was not refused with '" + want + "': " + r.message);
          break;
        }
        if (f->save() != z) { bad("version " + v + " was refused but the family was not reset"); break; }
      }
    }
  }
  return out;
}

}  // namespace argonia::core::roundtrip

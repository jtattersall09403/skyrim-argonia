// PrismaUI's modder interface as ArgoniaCore calls it: our own declaration of the ABI that PrismaUI 1.5.1 publishes
// (PrismaUI-SKSE/framework, tag 1.5.1, src/PrismaUI_API.h; data/dependencies.json row prismaui). PrismaUI is the
// player's own download, depended on unmodified (decision 0015); we call it only through this published interface.
// The virtual order below is the ABI: it must match the published header slot for slot. A PrismaUI update that
// changes it is a dependency re-pin (stack.py's sha256 stops a silent change), and the probe re-runs.
#pragma once
#include <cstdint>

namespace argonia::prisma {

using View = std::uint64_t;
using DomReady = void (*)(View view);
using JsResult = void (*)(const char* result);
using JsListener = void (*)(const char* argument);
enum class ConsoleLevel : std::uint8_t { log = 0, warning, error, debug, info };
using ConsoleSink = void (*)(View view, ConsoleLevel level, const char* message);
enum class Version : std::uint8_t { v1, v2 };

class Api1 {
 protected:
  ~Api1() = default;

 public:
  virtual View CreateView(const char* html_path, DomReady on_dom_ready = nullptr) noexcept = 0;
  virtual void Invoke(View view, const char* script, JsResult callback = nullptr) noexcept = 0;
  virtual void InteropCall(View view, const char* function, const char* argument) noexcept = 0;
  virtual void RegisterJSListener(View view, const char* function, JsListener callback) noexcept = 0;
  virtual bool HasFocus(View view) noexcept = 0;
  virtual bool Focus(View view, bool pause_game = false, bool disable_focus_menu = false) noexcept = 0;
  virtual void Unfocus(View view) noexcept = 0;
  virtual void Show(View view) noexcept = 0;
  virtual void Hide(View view) noexcept = 0;
  virtual bool IsHidden(View view) noexcept = 0;
  virtual int GetScrollingPixelSize(View view) noexcept = 0;
  virtual void SetScrollingPixelSize(View view, int pixels) noexcept = 0;
  virtual bool IsValid(View view) noexcept = 0;
  virtual void Destroy(View view) noexcept = 0;
  virtual void SetOrder(View view, int order) noexcept = 0;
  virtual int GetOrder(View view) noexcept = 0;
  virtual void CreateInspectorView(View view) noexcept = 0;
  virtual void SetInspectorVisibility(View view, bool visible) noexcept = 0;
  virtual bool IsInspectorVisible(View view) noexcept = 0;
  virtual void SetInspectorBounds(View view, float x, float y, unsigned width, unsigned height) noexcept = 0;
  virtual bool HasAnyActiveFocus() noexcept = 0;
};

class Api2 : public Api1 {
 protected:
  ~Api2() = default;

 public:
  virtual void RegisterConsoleCallback(View view, ConsoleSink callback) noexcept = 0;
};

// PrismaUI.dll's exported entry; null when the DLL is absent (the views stay off and the vanilla menus pass).
using RequestApi = void* (*)(Version version);
inline constexpr const char* kDll = "PrismaUI.dll";
inline constexpr const char* kEntry = "RequestPluginAPI";

}  // namespace argonia::prisma

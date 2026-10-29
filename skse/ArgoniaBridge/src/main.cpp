// ArgoniaBridge skeleton (DEV ONLY, 0.3 §a): a named pipe \\.\pipe\argonia-bridge, local clients only, one
// request line and one JSON reply line at a time (protocol/bridge_protocol.h). Every handler runs on the game's
// main thread through SKSE's task queue and must answer within kMainThreadTimeout, or the reply says it did not.
// The only endpoint is `ping`; 0.3 §a adds input, frametime, nav, booth and the ArgoniaCore reads behind it.
#if !defined(ARGONIA_DEV_ONLY) || defined(ARGONIA_RELEASE)
#  error "ArgoniaBridge is dev-only (skse/dev-only.txt) and is never built into a release"
#endif

#include "argonia/core/version.h"
#include "bridge_protocol.h"

namespace bridge = argonia::bridge;

namespace {

constexpr auto kPipeName = LR"(\\.\pipe\argonia-bridge)";
constexpr auto kMainThreadTimeout = 3s;

std::string g_token;
std::atomic<std::uint64_t> g_tasks_run{0};

// Runs fn on the main thread and waits for its JSON result; an error reply if the game does not get to it.
std::string on_main_thread(const std::string& cmd, std::function<std::string()> fn) {
  auto done = std::make_shared<std::promise<std::string>>();
  auto result = done->get_future();
  SKSE::GetTaskInterface()->AddTask([done, fn = std::move(fn)] {
    ++g_tasks_run;
    try {
      done->set_value(fn());
    } catch (const std::exception& e) {
      done->set_value(bridge::reply_error("task", e.what()));
    }
  });
  if (result.wait_for(kMainThreadTimeout) != std::future_status::ready)
    return bridge::reply_error(cmd, "main thread did not run the task within 3 s");
  return result.get();
}

std::string handle(const bridge::Request& req) {
  if (req.command == "ping") {
    return on_main_thread(req.command, [] {
      return bridge::reply_ok("ping", "{\"pong\":true,\"main_thread\":true,\"bridge\":\""s +
                                          argonia::core::kVersionString + "\",\"tasks_run\":" +
                                          std::to_string(g_tasks_run.load()) + "}");
    });
  }
  return bridge::reply_error(req.command, "unknown command");
}

std::string answer(std::string_view line) {
  auto parsed = bridge::parse(line, g_token);
  if (auto* refusal = std::get_if<bridge::Refusal>(&parsed)) return bridge::reply_error("", refusal->error);
  return handle(std::get<bridge::Request>(parsed));
}

void serve_client(HANDLE pipe) {
  std::string buffer;
  char chunk[512];
  DWORD got = 0;
  while (ReadFile(pipe, chunk, sizeof chunk, &got, nullptr) && got > 0) {
    buffer.append(chunk, got);
    if (buffer.size() > bridge::kMaxLine + 2 && buffer.find('\n') == std::string::npos) {
      auto reply = bridge::reply_error("", "request longer than 4096 bytes");
      WriteFile(pipe, reply.data(), static_cast<DWORD>(reply.size()), &got, nullptr);
      return;
    }
    for (std::size_t nl; (nl = buffer.find('\n')) != std::string::npos;) {
      auto reply = answer(std::string_view(buffer).substr(0, nl + 1));
      buffer.erase(0, nl + 1);
      DWORD wrote = 0;
      if (!WriteFile(pipe, reply.data(), static_cast<DWORD>(reply.size()), &wrote, nullptr)) return;
    }
  }
}

void serve() {
  for (;;) {
    HANDLE pipe = CreateNamedPipeW(kPipeName, PIPE_ACCESS_DUPLEX,
                                   PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS, 1,
                                   64 * 1024, 64 * 1024, 0, nullptr);
    if (pipe == INVALID_HANDLE_VALUE) {
      SKSE::log::critical("bridge: CreateNamedPipe failed ({}); bridge stopped", GetLastError());
      return;
    }
    if (ConnectNamedPipe(pipe, nullptr) || GetLastError() == ERROR_PIPE_CONNECTED) serve_client(pipe);
    FlushFileBuffers(pipe);
    DisconnectNamedPipe(pipe);
    CloseHandle(pipe);
  }
}

// A fresh 128-bit token per game launch, written beside the SKSE log for the client to read over SSH.
bool write_token() {
  std::random_device rd;
  static constexpr char hex[] = "0123456789abcdef";
  g_token.clear();
  for (std::size_t i = 0; i < bridge::kTokenHexChars; ++i) g_token += hex[rd() & 0xF];
  auto dir = SKSE::log::log_directory();
  if (!dir) return false;
  std::ofstream f(*dir / "ArgoniaBridge.token", std::ios::trunc);
  f << g_token;
  return static_cast<bool>(f);
}

}  // namespace

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* skse) {
  SKSE::Init(skse);
  if (!write_token()) {
    SKSE::log::critical("bridge: token not written; bridge not started");
    return true;  // a dev tool never stops the game from loading
  }
  // Tasks need the game loop; serving starts once the data is loaded.
  SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* m) {
    if (m->type == SKSE::MessagingInterface::kDataLoaded) {
      std::thread(serve).detach();
      SKSE::log::info("bridge: serving {} (DEV ONLY)", "\\\\.\\pipe\\argonia-bridge");
    }
  });
  SKSE::log::info("ArgoniaBridge {} loaded (DEV ONLY)", argonia::core::kVersionString);
  return true;
}

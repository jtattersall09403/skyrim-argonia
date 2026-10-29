// ArgoniaBridge (DEV ONLY, 0.3 §a): the agent's hands in the running game, by SkyLink AI's method (SkyLink itself
// does not load on 1.7.104). Requests come over a named pipe \\.\pipe\argonia-bridge and over TCP 127.0.0.1:47615
// (local clients only; the build VM reaches the port through an SSH tunnel), one line in and one JSON line out
// (protocol/bridge_protocol.h), one request at a time. Every game read or write runs on the main thread through
// SKSE's task queue. The endpoints live in ep_*.cpp; tools/bridge.py is the one client.
#if !defined(ARGONIA_DEV_ONLY) || defined(ARGONIA_RELEASE)
#  error "ArgoniaBridge is dev-only (skse/dev-only.txt) and is never built into a release"
#endif

#include "argonia/core/version.h"
#include "bridge.h"
#include "server.h"

namespace argonia::bridge {

std::map<std::string, Handler>& handlers() {
  static std::map<std::string, Handler> h;
  return h;
}

GameSignals& signals() {
  static GameSignals s;
  return s;
}

std::filesystem::path my_games() {
  auto dir = SKSE::log::log_directory();
  return dir ? dir->parent_path() : std::filesystem::path{};
}

RE::PlayerCharacter* player_in_world() {
  auto* p = RE::PlayerCharacter::GetSingleton();
  if (!p || !p->GetParentCell() || !p->Get3D()) return nullptr;
  if (auto* ui = RE::UI::GetSingleton(); ui && (ui->IsMenuOpen(RE::MainMenu::MENU_NAME) || ui->IsMenuOpen(RE::LoadingMenu::MENU_NAME)))
    return nullptr;
  return p;
}

namespace {
std::atomic<std::uint64_t> g_tasks_run{0};
std::string g_token;
std::mutex g_one_request;  // the pipe and the socket share the handlers: one request at a time
}  // namespace

std::string on_main_thread(const std::string& cmd, std::function<std::string()> fn, std::chrono::milliseconds timeout) {
  auto done = std::make_shared<std::promise<std::string>>();
  auto result = done->get_future();
  SKSE::GetTaskInterface()->AddTask([done, fn = std::move(fn)] {
    ++g_tasks_run;
    try {
      done->set_value(fn());
    } catch (const std::exception& e) {
      done->set_value(reply_error("task", e.what()));
    }
  });
  if (result.wait_for(timeout) != std::future_status::ready)
    return reply_error(cmd, "main thread did not run the task within " + std::to_string(timeout.count()) + " ms");
  return result.get();
}

namespace {

std::string ping(const Request& req) {
  return on_main_thread(req.command, [] {
    return reply_ok("ping", JsonObject()
                                .boolean("pong", true)
                                .boolean("main_thread", true)
                                .str("bridge", argonia::core::kVersionString)
                                .integer("tasks_run", static_cast<long long>(g_tasks_run.load()))
                                .integer("pid", static_cast<long long>(GetCurrentProcessId()))
                                .done());
  });
}

std::string list(const Request&) {
  std::string names = "[";
  for (auto& [n, h] : handlers()) names += (names.size() > 1 ? "," : "") + json_string(n);
  return reply_ok("commands", JsonObject().raw("commands", names + "]").done());
}

const Register r_ping{"ping", &ping};
const Register r_list{"commands", &list};

std::string answer(std::string_view line) {
  auto parsed = parse(line, g_token);
  if (auto* refusal = std::get_if<Refusal>(&parsed)) return reply_error("", refusal->error);
  auto& req = std::get<Request>(parsed);
  auto it = handlers().find(req.command);
  if (it == handlers().end()) return reply_error(req.command, "unknown command (try `commands`)");
  std::scoped_lock lock(g_one_request);
  try {
    return it->second(req);
  } catch (const std::exception& e) {
    return reply_error(req.command, e.what());
  }
}

}  // namespace

// One client: read lines, answer each.
void serve_lines(const RecvFn& recv, const SendFn& send) {
  std::string buffer;
  char chunk[512];
  for (int got; (got = recv(chunk, static_cast<int>(sizeof chunk))) > 0;) {
    buffer.append(chunk, static_cast<std::size_t>(got));
    if (buffer.size() > kMaxLine + 2 && buffer.find('\n') == std::string::npos) {
      send(reply_error("", "request longer than 4096 bytes"));
      return;
    }
    for (std::size_t nl; (nl = buffer.find('\n')) != std::string::npos;) {
      auto reply = answer(std::string_view(buffer).substr(0, nl + 1));
      buffer.erase(0, nl + 1);
      if (!send(reply)) return;
    }
  }
}

namespace {

void serve_pipe() {
  for (;;) {
    HANDLE pipe = CreateNamedPipeW(LR"(\\.\pipe\argonia-bridge)", PIPE_ACCESS_DUPLEX,
                                   PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS, 1,
                                   64 * 1024, 64 * 1024, 0, nullptr);
    if (pipe == INVALID_HANDLE_VALUE) {
      SKSE::log::critical("bridge: CreateNamedPipe failed ({}); pipe stopped", GetLastError());
      return;
    }
    if (ConnectNamedPipe(pipe, nullptr) || GetLastError() == ERROR_PIPE_CONNECTED) {
      serve_lines(
          [pipe](char* b, int n) {
            DWORD got = 0;
            return ReadFile(pipe, b, static_cast<DWORD>(n), &got, nullptr) ? static_cast<int>(got) : -1;
          },
          [pipe](const std::string& s) {
            DWORD wrote = 0;
            return WriteFile(pipe, s.data(), static_cast<DWORD>(s.size()), &wrote, nullptr) != 0;
          });
    }
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
  for (std::size_t i = 0; i < kTokenHexChars; ++i) g_token += hex[rd() & 0xF];
  auto dir = SKSE::log::log_directory();
  if (!dir) return false;
  std::ofstream f(*dir / "ArgoniaBridge.token", std::ios::trunc);
  f << g_token;
  return static_cast<bool>(f);
}

void on_message(SKSE::MessagingInterface::Message* m) {
  auto& s = signals();
  switch (m->type) {
    case SKSE::MessagingInterface::kDataLoaded:
      events_install();
      std::thread(serve_pipe).detach();
      std::thread([] { serve_tcp(kTcpPort, [](const std::string& e) { SKSE::log::critical("bridge: {}", e); }); }).detach();
      SKSE::log::info("bridge: serving \\\\.\\pipe\\argonia-bridge and 127.0.0.1:{} (DEV ONLY)", kTcpPort);
      return;
    case SKSE::MessagingInterface::kPostLoadGame: {
      std::scoped_lock l(s.m);
      ++s.loads;
      // SKSE passes the load's success as the pointer value itself ((void*)success), not a pointer to a bool:
      // dereferencing it read address 0x1 and crashed the first live load (2026-10-29).
      s.last_load_ok = reinterpret_cast<std::uintptr_t>(m->data) != 0;
      events_on_game_loaded();
      break;
    }
    case SKSE::MessagingInterface::kSaveGame: {
      std::scoped_lock l(s.m);
      ++s.saves;
      s.last_save = m->data ? static_cast<const char*>(m->data) : "";
      break;
    }
    case SKSE::MessagingInterface::kNewGame: {
      std::scoped_lock l(s.m);
      ++s.new_games;
      events_on_game_loaded();
      break;
    }
    default:
      return;
  }
  s.cv.notify_all();
}

}  // namespace
}  // namespace argonia::bridge

SKSE_PLUGIN_LOAD(const SKSE::LoadInterface* skse) {
  SKSE::Init(skse);
  if (!argonia::bridge::write_token()) {
    SKSE::log::critical("bridge: token not written; bridge not started");
    return true;  // a dev tool never stops the game from loading
  }
  argonia::bridge::input_install();
  SKSE::GetMessagingInterface()->RegisterListener(argonia::bridge::on_message);
  SKSE::log::info("ArgoniaBridge {} loaded (DEV ONLY), {} commands", argonia::core::kVersionString,
                  argonia::bridge::handlers().size());
  return true;
}

// ArgoniaBridge's localhost socket (DEV ONLY): built without the PCH (see server.h). Loopback only; the build VM
// reaches it through `ssh -L`, so nothing listens on the machine's network.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <winsock2.h>

#include <cstddef>
#include <string>

#include "server.h"

namespace argonia::bridge {

void serve_tcp(std::uint16_t port, const std::function<void(const std::string&)>& log_error) {
  WSADATA wsa;
  if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return log_error("WSAStartup failed; socket not served");
  SOCKET ls = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
  sockaddr_in addr{};
  addr.sin_family = AF_INET;
  addr.sin_port = htons(port);
  addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  if (ls == INVALID_SOCKET || bind(ls, reinterpret_cast<sockaddr*>(&addr), sizeof addr) != 0 || listen(ls, 4) != 0)
    return log_error("127.0.0.1:" + std::to_string(port) + " not bound (" + std::to_string(WSAGetLastError()) + ")");
  for (;;) {
    SOCKET c = accept(ls, nullptr, nullptr);
    if (c == INVALID_SOCKET) continue;
    serve_lines([c](char* b, int n) { return ::recv(c, b, n, 0); },
                [c](const std::string& s) {
                  for (std::size_t off = 0; off < s.size();) {
                    int k = ::send(c, s.data() + off, static_cast<int>(s.size() - off), 0);
                    if (k <= 0) return false;
                    off += static_cast<std::size_t>(k);
                  }
                  return true;
                });
    closesocket(c);
  }
}

}  // namespace argonia::bridge

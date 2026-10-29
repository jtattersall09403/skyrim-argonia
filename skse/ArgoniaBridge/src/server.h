// The transport seam (no Skyrim or Windows types), so the socket file can include Winsock without the PCH:
// CommonLib's headers pull in <Windows.h> with the old winsock.h, which clashes with <winsock2.h>.
#pragma once
#include <cstdint>
#include <functional>
#include <string>

namespace argonia::bridge {
using RecvFn = std::function<int(char*, int)>;            // bytes read; <= 0 ends the client
using SendFn = std::function<bool(const std::string&)>;  // false ends the client
// Reads request lines from one client and sends one reply line for each (main.cpp).
void serve_lines(const RecvFn& recv, const SendFn& send);
// Serves 127.0.0.1:port forever, one client at a time; logs and returns if the port cannot be bound (tcp.cpp).
void serve_tcp(std::uint16_t port, const std::function<void(const std::string&)>& log_error);
}  // namespace argonia::bridge

// The reads 1.7's first-place journey and soak need (DEV ONLY, 0.3 §a):
//   core <Native> [arg]   a whitelisted ArgoniaCore native (argonia/core/bridge_call.h: the reads of ArgoniaCore.psc and
//                         the two view intents), as {"native":..,"value":..}; any other name is refused here, before a
//                         message is sent, and again by ArgoniaCore
//   papyrus-queue         the Papyrus VM's stacks (running + suspended), the soak's "queue length", read on the main
//                         thread under the VM's own locks
#include "bridge.h"
#include "argonia/core/bridge_call.h"

namespace argonia::bridge {
namespace {

std::string core(const Request& req) {
  namespace bc = argonia::core::bridge_call;
  auto call = core_call(req);
  if (!call) return reply_error("core", "usage: core <Native> [arg] (e.g. core GetVastei, core KnowsTopic topic.x)");
  if (auto why = bc::refuse(call->native, call->arg.has_value())) return reply_error("core", *why);
  if (call->native.size() >= sizeof(bc::BridgeCore::native) || (call->arg && call->arg->size() >= sizeof(bc::BridgeCore::arg)))
    return reply_error("core", "the native's name or argument is too long");
  return on_main_thread(req.command, [c = *call] {
    auto m = std::make_unique<bc::BridgeCore>();
    c.native.copy(m->native, sizeof(m->native) - 1);
    if (c.arg) {
      c.arg->copy(m->arg, sizeof(m->arg) - 1);
      m->has_arg = true;
    }
    const bool sent = SKSE::GetMessagingInterface()->Dispatch(bc::kBridgeCoreMessage, m.get(), sizeof(*m), "ArgoniaCore");
    if (!sent) return reply_error("core", "ArgoniaCore is not loaded (the message had no receiver)");
    if (!m->ok) return reply_error("core", m->error[0] ? m->error : "ArgoniaCore did not answer (an older DLL?)");
    return reply_ok("core", m->json);
  });
}

std::string papyrus_queue(const Request& req) {
  return on_main_thread(req.command, [] {
    auto* vm = RE::BSScript::Internal::VirtualMachine::GetSingleton();
    if (!vm) return reply_error("papyrus-queue", "no Papyrus VM yet");
    PapyrusQueue q;
    {
      RE::BSSpinLockGuard g(vm->runningStacksLock);
      q.running = static_cast<long long>(vm->allRunningStacks.size());
      q.waiting_latent = static_cast<long long>(vm->waitingLatentReturns.size());
    }
    {
      RE::BSSpinLockGuard g(vm->suspendQueueLock);
      q.suspended = static_cast<long long>(vm->suspendQueue1.numEntries) + vm->suspendQueue2.numEntries +
                    vm->overflowSuspendArray1.size() + vm->overflowSuspendArray2.size();
    }
    q.waiting_functions = vm->uiWaitingFunctionMessages;
    q.overstressed = vm->overstressed;
    return reply_ok("papyrus-queue", papyrus_queue_json(q));
  });
}

const Register r_core{"core", &core};
const Register r_papyrus_queue{"papyrus-queue", &papyrus_queue};

}  // namespace
}  // namespace argonia::bridge

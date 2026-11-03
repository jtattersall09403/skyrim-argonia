"""A small AVM1 (ActionScript 2 bytecode) assembler: enough to drive a menu movie from an injected DoAction (call a
method by path, set a member, build arrays and objects, define a function with a for..in loop). Used by flash_still
to put a Scaleform menu into a state off-game; the bytecode is ours, the movie is the player's (0014).

    a = Asm(); a.call("_root.Menu_mc", "startPage"); a.set("_root.Menu_mc", "x", 3); tag_body = a.bytes()
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

STOP, POP, ADD2, EQUALS2, NOT = 0x07, 0x17, 0x47, 0x49, 0x12
GET_VARIABLE, SET_VARIABLE, DEFINE_LOCAL = 0x1C, 0x1D, 0x3C
GET_MEMBER, SET_MEMBER, CALL_METHOD, CALL_FUNCTION = 0x4E, 0x4F, 0x52, 0x3D
INIT_ARRAY, INIT_OBJECT, TYPEOF, INSTANCEOF, ENUMERATE2 = 0x42, 0x43, 0x44, 0x54, 0x55
PUSH, JUMP, IF, STORE_REGISTER, DEFINE_FUNCTION = 0x96, 0x99, 0x9D, 0x87, 0x9B


@dataclass(frozen=True)
class Ref:
    """A value read by path at run time ("_root.a.b"), or register n when reg is set."""
    path: str = ""
    reg: int | None = None


class Asm:
    def __init__(self) -> None:
        self.out: list = []  # bytes, or ("jump"/"if", label), or ("label", name)

    # --- raw ----------------------------------------------------------------------------------------------------
    def op(self, code: int, payload: bytes = b"") -> "Asm":
        self.out.append(bytes([code]) + (struct.pack("<H", len(payload)) + payload if code >= 0x80 else b""))
        return self

    def push(self, *values) -> "Asm":
        body = b""
        for v in values:
            if v is None:
                body += b"\x02"
            elif isinstance(v, bool):
                body += b"\x05" + bytes([v])
            elif isinstance(v, int) and -2**31 <= v < 2**31:
                body += b"\x07" + struct.pack("<i", v)
            elif isinstance(v, (int, float)):
                d = struct.pack("<d", float(v))
                body += b"\x06" + d[4:] + d[:4]  # AVM1 doubles are stored high word first
            elif isinstance(v, str):
                body += b"\x00" + v.encode("utf-8") + b"\0"
            else:
                raise TypeError(v)
        return self.op(PUSH, body)

    def label(self, name: str) -> "Asm":
        self.out.append(("label", name))
        return self

    def jump(self, name: str, cond: bool = False) -> "Asm":
        self.out.append(("if" if cond else "jump", name))
        return self

    # --- values -------------------------------------------------------------------------------------------------
    def path(self, path: str) -> "Asm":
        head, *rest = path.split(".")
        self.push(head).op(GET_VARIABLE)
        for m in rest:
            self.push(m).op(GET_MEMBER)
        return self

    def value(self, v) -> "Asm":
        if isinstance(v, Ref):
            return self.push_reg(v.reg) if v.reg is not None else self.path(v.path)
        if isinstance(v, (list, tuple)):
            for x in reversed(v):
                self.value(x)
            return self.push(len(v)).op(INIT_ARRAY)
        if isinstance(v, dict):
            for k, x in v.items():
                self.push(k)
                self.value(x)
            return self.push(len(v)).op(INIT_OBJECT)
        return self.push(v)

    def push_reg(self, n: int) -> "Asm":
        return self.op(PUSH, b"\x04" + bytes([n]))

    # --- statements ---------------------------------------------------------------------------------------------
    def call(self, obj: str | Ref, method: str, *args, keep: bool = False) -> "Asm":
        for a in reversed(args):
            self.value(a)
        self.push(len(args))
        self.value(obj if isinstance(obj, Ref) else Ref(obj))
        self.push(method).op(CALL_METHOD)
        return self if keep else self.op(POP)

    def callf(self, name: str, *args) -> "Asm":
        for a in reversed(args):
            self.value(a)
        self.push(len(args), name).op(CALL_FUNCTION)
        return self.op(POP)

    def set(self, obj: str | Ref, member: str, v) -> "Asm":
        self.value(obj if isinstance(obj, Ref) else Ref(obj))
        self.push(member)
        self.value(v)
        return self.op(SET_MEMBER)

    def var(self, name: str, v) -> "Asm":
        self.push(name)
        self.value(v)
        return self.op(SET_VARIABLE)

    def function(self, name: str, params: list[str], body: "Asm") -> "Asm":
        code = body.bytes(end=False)
        payload = name.encode() + b"\0" + struct.pack("<H", len(params))
        payload += b"".join(p.encode() + b"\0" for p in params) + struct.pack("<H", len(code))
        self.op(DEFINE_FUNCTION, payload)
        self.out.append(code)
        return self

    # --- output -------------------------------------------------------------------------------------------------
    def bytes(self, end: bool = True) -> bytes:
        size = lambda x: 5 if isinstance(x, tuple) and x[0] != "label" else (0 if isinstance(x, tuple) else len(x))
        at, pos = {}, 0
        for x in self.out:
            if isinstance(x, tuple) and x[0] == "label":
                at[x[1]] = pos
            pos += size(x)
        blob, pos = b"", 0
        for x in self.out:
            pos += size(x)
            if isinstance(x, tuple):
                if x[0] != "label":
                    blob += bytes([IF if x[0] == "if" else JUMP]) + struct.pack("<Hh", 2, at[x[1]] - pos)
            else:
                blob += x
        return blob + (b"\0" if end else b"")


def text_walker(name: str, on_text: "Asm") -> Asm:
    """`function name(mc) { for (k in mc) { c = mc[k]; if (c instanceof TextField) { on_text } else if
    (typeof c == "movieclip" && c._parent == mc) name(c); } }` as a DefineFunction; on_text reads the local c."""
    b = Asm()
    b.push("mc").op(GET_VARIABLE).op(ENUMERATE2)
    b.label("loop").op(STORE_REGISTER, b"\0").push(None).op(EQUALS2).jump("end", cond=True)
    b.push("c").push("mc").op(GET_VARIABLE).push_reg(0).op(GET_MEMBER).op(DEFINE_LOCAL)
    b.push("c").op(GET_VARIABLE).push("TextField").op(GET_VARIABLE).op(INSTANCEOF).op(NOT).jump("notext", cond=True)
    b.out += on_text.out
    b.jump("loop")
    b.label("notext")
    b.push("c").op(GET_VARIABLE).op(TYPEOF).push("movieclip").op(EQUALS2).op(NOT).jump("loop", cond=True)
    b.push("c").op(GET_VARIABLE).push("_parent").op(GET_MEMBER).push("mc").op(GET_VARIABLE).op(EQUALS2)
    b.op(NOT).jump("loop", cond=True)
    b.push("c").op(GET_VARIABLE).push(1, name).op(CALL_FUNCTION).op(POP).jump("loop")
    b.label("end")
    return Asm().function(name, ["mc"], b)


def hide_text_function() -> Asm:
    """__hideText(mc): every text field under mc hidden."""
    return text_walker("__hideText", Asm().set(Ref("c"), "_visible", False))


def translate_function(table: dict[str, str]) -> Asm:
    """__translate(mc): every text field under mc whose text is a "$KEY" in the table shows the translation, as
    Scaleform does when a script sets "$KEY" text (Ruffle shows it raw)."""
    a = Asm().var("__tr", table)
    t = Asm()
    t.push("t").path("__tr").path("c.text").op(GET_MEMBER).op(DEFINE_LOCAL)
    t.path("t").op(TYPEOF).push("string").op(EQUALS2).op(NOT).jump("skip", cond=True)
    t.set(Ref("c"), "text", Ref("t")).label("skip")
    a.out += text_walker("__translate", t).out
    return a

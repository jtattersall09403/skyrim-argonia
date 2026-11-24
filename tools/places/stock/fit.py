"""Does a worn piece fit an Argonian? Read from the plugins: an ARMO's armatures (ARMA, its `MODL` rows) each name the
race they dress (`RNAM`) and the races added to it (`MODL` rows), and the piece fits an Argonian when one of its
armatures dresses ArgonianRace, or DefaultRace with ArgonianRace among the added races (a race's armature wins over the
default one in the game, so an ArgonianRace armature is the better fit).

    from tools.places.stock import fit
    f = fit.Fit.load(["Skyrim.esm", ..., "King of the Murkmire.esp"])
    f.argonian("King of the Murkmire.esp:086686")  -> (True, "ArgonianRace armature") or (False, why)
"""
from __future__ import annotations

import struct

from tools.argonia_world import esm
from tools.places.stock.records import place_key

ARGONIAN = {"ArgonianRace", "ArgonianRaceVampire"}


class Fit:
    def __init__(self):
        self.armo: dict[str, esm.Record] = {}
        self.arma: dict[str, esm.Record] = {}
        self.race: dict[str, str] = {}

    @classmethod
    def load(cls, plugins: list[str]) -> "Fit":
        from tools.places.extract import find_plugin, search_dirs
        dirs = search_dirs()
        self = cls()
        for name in plugins:
            p = esm.Plugin.read(find_plugin(name, dirs), {"ARMO", "ARMA", "RACE"})
            for r in p.records():
                k = place_key(r.key)
                if r.sig == "ARMO":
                    self.armo[k] = r
                elif r.sig == "ARMA":
                    self.arma[k] = r
                elif r.sig == "RACE":
                    self.race[k] = r.edid or k
        return self

    def _refs(self, rec: esm.Record, sig: str) -> list[str]:
        return [place_key(rec.plugin.form_key(struct.unpack_from("<I", d)[0]))
                for d in rec.all(sig) if len(d) >= 4 and struct.unpack_from("<I", d)[0]]

    def armatures(self, key: str) -> list[tuple[str, list[str]]]:
        """[(its race, [added races])] of each armature of the piece, by race editor ids."""
        rec = self.armo.get(key)
        out = []
        for a in self._refs(rec, "MODL") if rec else []:
            ar = self.arma.get(a)
            if ar is None:
                continue
            main = (self._refs(ar, "RNAM") or [None])[0]
            out.append((self.race.get(main, main), [self.race.get(x, x) for x in self._refs(ar, "MODL")]))
        return out

    def argonian(self, key: str) -> tuple[bool, str]:
        arms = self.armatures(key)
        if not arms:
            return False, "no armature in the plugins read"
        for race, extra in arms:
            if race in ARGONIAN:
                return True, "an ArgonianRace armature"
        for race, extra in arms:
            if race == "DefaultRace" and ARGONIAN & set(extra):
                return True, "a DefaultRace armature that adds ArgonianRace"
        return False, "its armatures dress " + ", ".join(sorted({r or "?" for r, _ in arms}))

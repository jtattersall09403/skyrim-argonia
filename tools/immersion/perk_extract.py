#!/usr/bin/env python3
"""The reachable skill-tree perks (1.12 §4; decision 0012): every PERK on a skill tree of the official plugins (the AVIF
perk-tree nodes, then each node's NNAM rank chain), with its vanilla name and description, written to the ignored
out/perk-text/vanilla.json (game text: never committed, decision 0003). tests/test_perk_text.py compares our wording
in the perk_text table with it when it is present.

    python3 tools/immersion/perk_extract.py     (game data: $ARGONIA_GAME_ROOT/Data or ~/games/skyrimse/Data;
                                                 strings: out/strings-cache, the official STRINGS tables)
"""
import json
import os
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.navmesh.esm import records, subrecords, masters
D = (Path(os.environ['ARGONIA_GAME_ROOT']) / 'Data') if os.environ.get('ARGONIA_GAME_ROOT') else Path.home() / 'games/skyrimse/Data'
S = REPO / 'out' / 'strings-cache'
def load(p, kind):
    b=p.read_bytes(); n,_=struct.unpack_from('<II',b,0); out={}
    base=8+n*8
    for i in range(n):
        sid,off=struct.unpack_from('<II',b,8+i*8); o=base+off
        if kind!='S':
            l=struct.unpack_from('<I',b,o)[0]; o+=4; s=b[o:o+l-1]
        else:
            e=b.index(b'\0',o); s=b[o:e]
        out[sid]=s.decode('utf-8','replace')
    return out
plugins=['Skyrim.esm','Update.esm','Dawnguard.esm','HearthFires.esm','Dragonborn.esm']
strs={}
for pl in plugins:
    st=pl[:-4]; strs[pl]={}
    for k,ext in (('S','STRINGS'),('D','DLSTRINGS'),('I','ILSTRINGS')):
        f=S/f'{st}_English.{ext}'
        if f.exists(): strs[pl].update(load(f,k))
def fk(fid, pl, ms):
    idx=fid>>24; name=(ms+[pl])[min(idx,len(ms))]
    return f'{fid&0xFFFFFF:06X}:{name}'
perks={}; trees=[]
for pl in plugins:
    ms=masters(D/pl)
    for r in records(D/pl,{b'PERK',b'AVIF'}):
        subs=list(subrecords(r.data))
        key=fk(r.fid,pl,ms)
        if r.sig==b'AVIF':
            nodes=[fk(struct.unpack('<I',p)[0],pl,ms) for s,p in subs if s==b'PNAM']
            ed=next((p[:-1].decode() for s,p in subs if s==b'EDID'),'')
            if nodes: trees.append((key,ed,nodes))
        else:
            d={'edid':'','name':None,'desc':None,'next':None}
            for s,p in subs:
                if s==b'EDID': d['edid']=p[:-1].decode()
                elif s==b'FULL': d['name']=strs[pl].get(struct.unpack('<I',p)[0]) if len(p)==4 else p[:-1].decode()
                elif s==b'DESC': d['desc']=strs[pl].get(struct.unpack('<I',p)[0]) if len(p)==4 else p[:-1].decode()
                elif s==b'NNAM': d['next']=fk(struct.unpack('<I',p)[0],pl,ms)
            perks[key]=d
reach={}
for k,ed,nodes in trees:
    for n in nodes:
        while n and n not in reach and n in perks:
            reach[n]=ed; n=perks[n]['next'] if perks[n]['next']!='000000:Skyrim.esm' else None
print(len(trees),[t[1] for t in trees])
(REPO / 'out/perk-text').mkdir(parents=True, exist_ok=True)
rows=[dict(formkey=k,tree=reach[k],**{x:perks[k][x] for x in('edid','name','desc')}) for k in reach]
json.dump(rows,open(REPO / 'out/perk-text/vanilla.json','w'),indent=0)
print(len(rows), sum(1 for r in rows if not r['name']), sum(1 for r in rows if not r['desc']))

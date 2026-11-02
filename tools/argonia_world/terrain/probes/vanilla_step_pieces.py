"""Probe (0034, lane 1.15-r4-water): how Skyrim.esm lays its rapids and falls pieces on a water step at a cell edge:
for each FX piece within 3,000 units of a stepped Tamriel edge (4-adjacent explicit levels differing by > 64 u),
its z against the upper and lower water and the ground, and its yaw against the drop (upper cell -> lower cell);
then the drops of the dressed steps and the skirt scales. Feeds water/steps.py.
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_step_pieces [Skyrim.esm]  (reads only; prints numbers)"""
import collections
import math
import struct
import sys

import numpy as np
from pathlib import Path
from tools.argonia_world.terrain.esm import records
from tools.argonia_world.terrain.probes.vanilla_lake_cells import TAMRIEL, vhgt
blob=Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/games/skyrimse/Data/Skyrim.esm").read_bytes()
FX={"FXrapidsFallsLine01","FxRapidsRingHeavy","FXWaterfallBodySlope","FXWaterfallSkirtSlope","FXWaterfallBodyTall","FXWaterfallMistBlast"}
base={};water={};land={};refs=[];wrld=None;cell=None
for r in records(blob):
    if r.sig in("ACTI","STAT","MSTT"):
        e=(r.first("EDID") or b"").rstrip(b"\0").decode()
        if e in FX: base[r.formid]=e
    elif r.sig=="WRLD": wrld=r.formid
    elif r.sig=="CELL":
        xc=r.first("XCLC"); cell=struct.unpack_from("<ii",xc) if (xc and wrld==TAMRIEL) else None
        if cell:
            wl=r.first("XCLW"); d=r.first("DATA")
            if wl and d and d[0]&2:
                h=struct.unpack_from("<f",wl)[0]
                if -1e6<h<1e6: water[cell]=h
    elif r.sig=="LAND" and cell: land[cell]=vhgt(r.first("VHGT")) if r.first("VHGT") else None
    elif r.sig=="REFR" and wrld==TAMRIEL:
        n=struct.unpack("<I",r.first("NAME"))[0]
        if n in base: refs.append((n,struct.unpack_from("<6f",r.first("DATA")),r.first("XSCL")))
print("fx bases",sorted(base.values()),"refs",len(refs))
steps=[]
for (x,y),h in water.items():
    for o in((x+1,y),(x,y+1)):
        if o in water and abs(water[o]-h)>64:
            hi,lo=((x,y),o) if h>water[o] else (o,(x,y)); steps.append((hi,lo))
def gz(px,py):
    cx,cy=math.floor(px/4096),math.floor(py/4096); a=land.get((cx,cy))
    if a is None: return None
    i=min(32,round((py-cy*4096)/128)); j=min(32,round((px-cx*4096)/128)); return float(a[i,j])
out=collections.defaultdict(list)
for n,(px,py,pz,rx,ry,rz),sc in refs:
    best=None
    for hi,lo in steps:
        # shared edge midpoint
        ex=(max(hi[0],lo[0]))*4096 if hi[0]!=lo[0] else hi[0]*4096+2048
        ey=(max(hi[1],lo[1]))*4096 if hi[1]!=lo[1] else hi[1]*4096+2048
        d=math.hypot(px-ex,py-ey)
        if d<3000 and (best is None or d<best[0]): best=(d,hi,lo)
    if not best: continue
    d,hi,lo=best
    down=math.degrees(math.atan2(lo[0]-hi[0],lo[1]-hi[1]))%360   # clockwise from north toward lower cell
    yaw=math.degrees(rz)%360; rel=(yaw-down+180)%360-180
    g=gz(px,py)
    out[base[n]].append((pz-water[hi],pz-water[lo],None if g is None else pz-g,rel,abs(rx)+abs(ry)>0.05))
for k,v in out.items():
    a=np.array([[t[0],t[1],t[2] if t[2] is not None else np.nan,t[3]] for t in v])
    rel=collections.Counter(int(round(t[3]/45))*45 for t in v)
    print(k,len(v),"z-upper med",np.nanmedian(a[:,0]).round(0),"z-lower med",np.nanmedian(a[:,1]).round(0),"z-ground p10/50/90",np.nanpercentile(a[:,2],[10,50,90]).round(0),"yaw-vs-down",dict(rel.most_common(4)),"tilted",sum(t[4] for t in v))
dd=collections.defaultdict(set)
for n,(px,py,pz,rx,ry,rz),sc in refs:
    for hi,lo in steps:
        ex=(max(hi[0],lo[0]))*4096 if hi[0]!=lo[0] else hi[0]*4096+2048
        ey=(max(hi[1],lo[1]))*4096 if hi[1]!=lo[1] else hi[1]*4096+2048
        if math.hypot(px-ex,py-ey)<3000: dd[(hi,lo)].add(base[n])
dr=sorted((water[h]-water[l])/70.03 for (h,l) in dd)
print("vanilla steps with fx",len(dr),"drop m",[round(x,1) for x in dr])
sk=[struct.unpack("<f",s)[0] if s else 1.0 for n,_,s in refs if base[n]=="FXWaterfallSkirtSlope"]
print("skirt scales",np.percentile(sk,[10,50,90]).round(2))

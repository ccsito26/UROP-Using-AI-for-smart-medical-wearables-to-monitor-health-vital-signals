"""Minimal DXF R12 writer: flat patterns / templates (mm, 1:1)."""
import numpy as np, os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from params import *
from geom import rrect, circle
D = os.path.join(os.path.dirname(__file__), 'out'); lay = json.load(open(os.path.join(D, 'layout.json')))
E = []
COL = {'CUT': 1, 'DRILL': 5, 'REF': 8, 'TRACE': 30, 'TEXT': 7, 'SNAP': 4}
def line(p, q, L): E.append(f"0\nLINE\n8\n{L}\n62\n{COL[L]}\n10\n{p[0]:.3f}\n20\n{p[1]:.3f}\n30\n0\n11\n{q[0]:.3f}\n21\n{q[1]:.3f}\n31\n0\n")
def pl(pts, L, closed=True):
    pts = list(pts) + ([pts[0]] if closed else [])
    for p, q in zip(pts[:-1], pts[1:]): line(p, q, L)
def circ(c, r, L): E.append(f"0\nCIRCLE\n8\n{L}\n62\n{COL[L]}\n10\n{c[0]:.3f}\n20\n{c[1]:.3f}\n30\n0\n40\n{r:.3f}\n")
def text(p, s, h=3.0, L='TEXT'): E.append(f"0\nTEXT\n8\n{L}\n62\n{COL[L]}\n10\n{p[0]:.3f}\n20\n{p[1]:.3f}\n30\n0\n40\n{h}\n1\n{s}\n")
snaps = [(-30, 39), (30, 39), (-30, -39), (30, -39)]
# 1 dock panel template (origin at its centre)
o = np.array([0, 0])
pl(rrect(DOCK["w"], DOCK["h"], DOCK["r"], 12) + o, 'CUT'); circ(o, PATCH["window_d"]/2, 'CUT')
for (x, y), pin in zip(snaps, ["3V3", "GND", "SDA", "SCL"]):
    circ(o + (x, y), 1.6, 'DRILL'); circ(o + (x, y), PATCH["snap_d"]/2, 'SNAP'); text(o + (x - 5, y + 8), pin, 2.5)
pl(rrect(PATCH["w"], PATCH["h"], PATCH["r"], 12) + o, 'REF')
text(o + (-55, -75), 'M1 DOCK PANEL - TPU laminate 0.6 - cut 1 per shirt', 3)
# 2 patch carrier outline
o = np.array([150, 0])
pl(rrect(PATCH["w"], PATCH["h"], PATCH["r"], 12) + o, 'CUT'); circ(o, PATCH["boss_d"]/2 + 0.2, 'CUT'); circ(o, 20, 'REF')
for x, y in snaps: circ(o + (x, y), 6.1, 'DRILL')
text(o + (-42, -68), 'M1 PATCH CARRIER - TPU 95A - boss D46.4, magnet pockets D12.2', 3)
text(o + (-42, -73), 'REF circle D40 = re-digitised labyrinth RTD + sweat electrodes', 2.5)
# 3 ECG electrodes x2
for k, x in enumerate((250, 300)):
    o = np.array([x, 0]); pl(rrect(ECG["w"], ECG["h"], ECG["r"], 10) + o, 'CUT'); circ(o + (0, ECG["h"]/2 - 8), 2.0, 'DRILL')
    text(o + (-20, -48), f'M3 ECG {"R" if k == 0 else "L"} - Ag knit', 3)
# 4 pod footprint & pogo
o = np.array([150, -120])
pl(rrect(POD["w"], POD["h"], POD["r"], 10) + o, 'CUT')
for i, px in enumerate((np.arange(6) - 2.5)*4): circ(o + (px, -6), 1.1, 'DRILL'); text(o + (px - 1, -13), str(i + 1), 2)
for mx in (-22, 22): circ(o + (mx, 4), 4, 'SNAP')
pl(rrect(POD["w"] + 6, POD["h"] + 4, POD["r"] + 2, 10) + o, 'REF')
text(o + (-35, -28), 'M2 POD / POGO DOCK PLATE - pins 1-6: 3V3 GND SDA SCL ECG_R ECG_L', 3)
# 5 back trace-routing template (surface coordinates: x = arc length from CB, y = height above hem, shifted)
o = np.array([700, -760])
for k, pts in lay["trace_paths"].items():
    P = np.array(pts, float) + o; pl(P, 'TRACE', closed=False); text(P[-1] + (2, 2), k, 2.5, 'TRACE')
PLC = lay["placement"]; MODS = PLC["modules"]
outl = {"m1": (DOCK["w"], DOCK["h"], DOCK["r"]), "temp": (76, 66, 12), "imu": (56, 42, 10), "sweat": (66, 56, 12), "hub": (POD["w"], POD["h"], POD["r"]), "ecgR": (ECG["w"], ECG["h"], ECG["r"]), "ecgL": (ECG["w"], ECG["h"], ECG["r"])}
for k in (["m1"] if PLC["bundleM1"] else ["temp", "imu", "sweat"]) + ["hub", "ecgR", "ecgL"]:
    p = MODS[k]; w, h, r = outl[k]; pl(rrect(w, h, r, 12) + o + (p["s"], p["z"]), 'REF'); text(o + (p["s"] - w/2, p["z"] + h/2 + 2), k.upper(), 3)
line(o + (-300, BNP_Z), o + (300, BNP_Z), 'REF'); text(o + (-300, BNP_Z + 3), 'BNP (back neck point)', 3)
line(o + (0, 300), o + (0, BNP_Z + 20), 'REF'); text(o + (2, 302), 'CB', 3)
text(o + (-300, 280), 'TRACE ROUTING TEMPLATE (unrolled back/side surface, size M; ECG traces continue round side seams to front)', 3.5)
hdr = "0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n6\n" + ''.join(
    f"0\nLAYER\n2\n{n}\n70\n0\n62\n{c}\n6\nCONTINUOUS\n" for n, c in COL.items()) + "0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n"
open(os.path.join(D, 'RSAF_HeatStrain_Shirt_Flat_Patterns.dxf'), 'w').write(hdr + ''.join(E) + "0\nENDSEC\n0\nEOF\n")
print(len(E), 'entities')

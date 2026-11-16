"""Printable parts as watertight 2.5-D heightfield solids (STL, mm)."""
import numpy as np, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from params import *
from geom import heightfield, rrect_mask, write_stl
OUT = os.path.join(os.path.dirname(__file__), 'out', 'printable'); os.makedirs(OUT, exist_ok=True)

def dist_to_edge(X, Y, w, h, r):
    # signed-ish inward distance for rounded rectangle
    qx, qy = np.abs(X) - (w/2 - r), np.abs(Y) - (h/2 - r)
    outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0)
    return r - outside

# ---- M2 hub pod base tray (PETG/ABS), opening up, pogo holes through floor ----
W, H, R = POD["w"], POD["h"], POD["r"]
WALL, FLOOR, TRAY_H = 1.8, 1.6, 9.0
pogo_x = (np.arange(6) - 2.5) * 4.0
def base_h(X, Y):
    d = dist_to_edge(X, Y, W, H, R)
    Z = np.where(d < WALL, TRAY_H, FLOOR)
    for px in pogo_x:
        Z = np.where(np.hypot(X - px, Y + 6) < 1.1, 0.0, Z)          # pogo pin holes D2.2
        Z = np.where((np.hypot(X - px, Y + 6) >= 1.1) & (np.hypot(X - px, Y + 6) < 2.2), np.maximum(Z, 3.0), Z)  # pin bosses
    for sx in (-W/2 + 6, W/2 - 6):                                    # M2 screw bosses
        rr = np.hypot(X - sx, Y)
        Z = np.where((rr < 3.0) & (rr >= 1.0), np.maximum(Z, TRAY_H - 1.0), Z)
        Z = np.where(rr < 1.0, FLOOR, Z)
    return Z
v, f = heightfield(rrect_mask(W, H, R), base_h, W, H, 0.25)
write_stl(os.path.join(OUT, 'M2_hub_pod_base_tray.stl'), v, f, 'M2 hub pod base tray')

# ---- M2 hub pod lid (prints flat side down), lip fits inside tray ----
LID_T, LIP_H, CLR = 2.0, 2.0, 0.25
def lid_h(X, Y):
    d = dist_to_edge(X, Y, W, H, R)
    Z = np.full_like(X, LID_T)
    Z = np.where((d >= WALL + CLR) & (d < WALL + CLR + 1.2), LID_T + LIP_H, Z)   # locating lip
    Z = np.where(np.hypot(X - (W/2 - 9), Y) < 1.6, 0.0, Z)                          # LED light-pipe hole D3.2
    Z = np.where(np.hypot(X - (-W/2 + 10), Y) < 3.8, 0.0, Z)                        # button hole D7.6
    for sx in (-W/2 + 6, W/2 - 6):
        Z = np.where(np.hypot(X - sx, Y) < 1.1, 0.0, Z)                             # screw clearance D2.2
    return Z
v, f = heightfield(rrect_mask(W, H, R), lid_h, W, H, 0.25)
write_stl(os.path.join(OUT, 'M2_hub_pod_lid.stl'), v, f, 'M2 hub pod lid')

# ---- M1 back patch carrier (TPU 95A), modelled shirt-side UP: print upside-down as modelled ----
PW, PH, PR = PATCH["w"], PATCH["h"], PATCH["r"]
BASE = 3.0
def carrier_h(X, Y):
    d = dist_to_edge(X, Y, PW, PH, PR)
    Z = np.full_like(X, BASE)
    Z = np.where(d < 1.6, BASE + 1.0, Z)                                             # perimeter sealing lip
    rr = np.hypot(X, Y)
    Z = np.where(rr < PATCH["boss_d"]/2 + 0.2, 0.0, Z)                               # boss aperture D46.4 (through)
    Z = np.where((rr >= PATCH["boss_d"]/2 + 0.2) & (rr < PATCH["boss_d"]/2 + 2.2), 1.5, Z)  # 2 mm ledge for boss flange
    for sx in (-PATCH["snap_pitch_x"]/2, PATCH["snap_pitch_x"]/2):
        for sy in (-PATCH["snap_pitch_y"]/2, PATCH["snap_pitch_y"]/2):
            Z = np.where(np.hypot(X - sx, Y - sy) < 6.1, 0.6, Z)                    # magnet pocket D12.2 x 2.4 deep
    # cable channels from pockets to the boss (1.2 mm wide, 1.0 deep)
    for sx in (-PATCH["snap_pitch_x"]/2, PATCH["snap_pitch_x"]/2):
        for sy in (-PATCH["snap_pitch_y"]/2, PATCH["snap_pitch_y"]/2):
            t = np.clip(((X*sx + Y*sy)) / (sx*sx + sy*sy), 0, 1)
            dd = np.hypot(X - t*sx, Y - t*sy)
            Z = np.where((dd < 0.6) & (Z > 1.9), 2.0, Z)
    return Z
v, f = heightfield(rrect_mask(PW, PH, PR), carrier_h, PW, PH, 0.25)
write_stl(os.path.join(OUT, 'M1_back_patch_carrier_TPU95A.stl'), v, f, 'M1 back patch carrier')

# ---- M1 sensing boss insert (PETG): cup, 1.0 mm skin-contact floor, TMP117 bonded inside, foam fills cup ----
BD = PATCH["boss_d"]
def boss_h(X, Y):
    rr = np.hypot(X, Y)
    Z = np.where(rr < BD/2, 1.0 + PATCH["foam_t"] + 1.6, 0.0)     # wall height 5.6
    Z = np.where(rr < BD/2 - 1.5, 1.0, Z)                          # 1.0 mm skin-contact floor
    Z = np.where((np.abs(X) < 4.5) & (np.abs(Y - 12) < 1.0), 2.0, Z)   # FPC tail locating rib
    return Z
v, f = heightfield(lambda X, Y: np.hypot(X, Y) < BD/2, boss_h, BD + 1, BD + 1, 0.25)
write_stl(os.path.join(OUT, 'M1_sensing_boss_cup.stl'), v, f, 'M1 sensing boss cup')
print(sorted(os.listdir(OUT)))

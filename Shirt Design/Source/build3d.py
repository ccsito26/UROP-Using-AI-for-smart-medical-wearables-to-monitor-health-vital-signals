import numpy as np, sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from params import *
from geom import *

OUT = os.path.join(os.path.dirname(__file__), 'out'); os.makedirs(OUT, exist_ok=True)
C = COLORS
meshes = []

# ---------- shirt torso ----------
zs = np.linspace(0, BNP_Z, 71); ths = np.linspace(-np.pi/2, 3*np.pi/2, 160, endpoint=False)
P = np.array([[torso_point(z, th) for z in zs] for th in ths])
v, f = grid_surface(P, len(ths), len(zs), closed_u=True)
meshes.append(Mesh(v, f, "Shirt_body", C["shirt"], rough=0.9, group="Shirt"))
# collar band
neck = [torso_point(BNP_Z, th) for th in np.linspace(-np.pi/2, 3*np.pi/2, 81)]
v, f = tube(neck, 7, 12); meshes.append(Mesh(v, f, "Collar_band", C["collar"], rough=0.9, group="Shirt"))
# hem band
hem = [torso_point(0, th) for th in np.linspace(-np.pi/2, 3*np.pi/2, 81)]
v, f = tube(hem, 4, 10); meshes.append(Mesh(v, f, "Hem_band", C["collar"], rough=0.9, group="Shirt"))
# sleeves
sl = SLEEVE; d = np.radians(sl["droop_deg"])
sleeve_frames = {}
for side in (+1, -1):
    root = np.array([side*sl["root_x"], 0, sl["root_z"]]); ax = np.array([side*np.cos(d), 0, -np.sin(d)])
    up = np.array([side*np.sin(d), 0, np.cos(d)]); fw = np.array([0, 1.0, 0])
    ts = np.linspace(0, 1, 20); angs = np.linspace(0, 2*np.pi, 48, endpoint=False)
    Ps = np.array([[root - ax*25 + ax*(t*(sl["length"]+25)) + (sl["r0"] + (sl["r1"]-sl["r0"])*t)*(np.cos(a)*up + np.sin(a)*fw) for t in ts] for a in angs])
    v, f = grid_surface(Ps, len(angs), len(ts), closed_u=True)
    meshes.append(Mesh(v, f, f"Sleeve_{'R' if side > 0 else 'L'}", C["shirt"], rough=0.9, group="Shirt"))
    cuff = [root - ax*25 + ax*(sl["length"]+25) + sl["r1"]*(np.cos(a)*up + np.sin(a)*fw) for a in np.linspace(0, 2*np.pi, 49)]
    v, f = tube(cuff, 4, 10); meshes.append(Mesh(v, f, f"Cuff_{'R' if side > 0 else 'L'}", C["collar"], rough=0.9, group="Shirt"))
    sleeve_frames[side] = (root, ax, up, fw)

# ---------- helpers to place 2D (local x = s, local y = z) shapes on the back surface ----------
def placer(s0, z0):
    def place(pts2d, off):
        pts2d = np.atleast_2d(pts2d)
        return np.array([surf(s0 + p[0], z0 + p[1], off) for p in pts2d])
    return place

import placement as PL
P = PL.load(); MOD = P["modules"]; BUNDLE = P["bundleM1"]
snap_xy = [(-PATCH["snap_pitch_x"]/2, PATCH["snap_pitch_y"]/2), (PATCH["snap_pitch_x"]/2, PATCH["snap_pitch_y"]/2),
           (-PATCH["snap_pitch_x"]/2, -PATCH["snap_pitch_y"]/2), (PATCH["snap_pitch_x"]/2, -PATCH["snap_pitch_y"]/2)]
def outward(s0, z0, mag):
    o, ts_, tz_, n = surf_frame(s0, z0); return tuple((n*mag).tolist())

def dock_and_patch(s0, z0, w, h, r, t, label, color, boss_d=None, n_snaps=4, pitch=None, group=None):
    place = placer(s0, z0); grp = group or label
    dw, dh = w + 26, h + 16
    v, f = slab_from_poly(rrect(dw, dh, min(r + 2, dw/2 - 1), 8), place, FABRIC_T*0.5, FABRIC_T*0.5 + DOCK["t"], fillet=0.3, rings=1)
    meshes.append(Mesh(v, f, f"Dock_{label}", C["dock"], rough=0.6, group="Dock (on shirt)"))
    base_off = FABRIC_T*0.5 + DOCK["t"] + 1.3; ex = outward(s0, z0, 90)
    v, f = slab_from_poly(rrect(w, h, r, 10), place, base_off, base_off + t, fillet=min(2.5, t/2.5), rings=5)
    meshes.append(Mesh(v, f, f"{label}_housing", color, rough=0.55, explode=ex, group=grp))
    if boss_d:
        v, f = slab_from_poly(circle(boss_d/2 + 2, 40), place, FABRIC_T*0.5 + DOCK["t"] + 0.05, FABRIC_T*0.5 + DOCK["t"] + 0.25, fillet=0.1, rings=1)
        meshes.append(Mesh(v, f, f"Mesh_window_{label}", C["window"], rough=1.0, group="Dock (on shirt)"))
        v, f = slab_from_poly(circle(boss_d/2, 40), place, -PATCH["boss_proj"] - FABRIC_T*0.5, base_off, fillet=1.0, rings=3)
        meshes.append(Mesh(v, f, f"{label}_sensing_boss", C["boss"], rough=0.4, explode=ex, group=grp))
    px, py = pitch or (w - 24, h - 26)
    sn = []
    for sx, sy in [(-px/2, py/2), (px/2, py/2), (-px/2, -py/2), (px/2, -py/2)][:n_snaps]:
        o, ts_, tz_, n = surf_frame(s0 + sx, z0 + sy)
        sn.append(cylinder(o + n*(FABRIC_T*0.5 + DOCK["t"]), n, min(6, w/6), 1.2))
    meshes.append(merge([Mesh(v, f, "", C["snap"]) for v, f in sn], f"Snaps_{label}", C["snap"], metallic=0.9, rough=0.3, group="Dock (on shirt)"))

if BUNDLE:
    m1 = MOD["m1"]
    dock_and_patch(m1["s"], m1["z"], PATCH["w"], PATCH["h"], PATCH["r"], PATCH["t"], "M1_Back_patch", C["patch"], boss_d=PATCH["boss_d"],
                   pitch=(PATCH["snap_pitch_x"], PATCH["snap_pitch_y"]), group="M1 Back thermal-gait patch")
else:
    specs = {"temp": (50, 50, 10, 6.6, (0.15, 0.39, 0.92, 1.0), 30), "imu": (30, 26, 8, 8.0, (0.76, 0.25, 0.05, 1.0), None), "sweat": (40, 40, 10, 3.0, (0.03, 0.57, 0.70, 1.0), 28)}
    names = {"temp": "Skin-temperature pod", "imu": "Gait IMU pod", "sweat": "Sweat sensor pod"}
    for k, (w, h, r, t, col, boss) in specs.items():
        p = MOD[k]
        dock_and_patch(p["s"], p["z"], w, h, r, t, names[k].replace(' ', '_').replace('-', '_'), col, boss_d=boss, n_snaps=4, group=names[k])

# hub pod
hp = MOD["hub"]; podz = hp["z"]
o, ts_, tz_, n = surf_frame(hp["s"], podz)
def rigid(pts2d, off, o=o, ts_=ts_, tz_=tz_, n=n):
    pts2d = np.atleast_2d(pts2d); return o + pts2d[:, :1]*ts_ + pts2d[:, 1:2]*tz_ + off*n
EXP_POD = tuple((n*70 + np.array([0, 0, 40])).tolist())
v, f = slab_from_poly(rrect(POD["w"] + 6, POD["h"] + 4, POD["r"] + 2, 8), rigid, FABRIC_T*0.5, FABRIC_T*0.5 + 0.8, fillet=0.3, rings=1)
meshes.append(Mesh(v, f, "Pogo_dock_plate", C["dock"], rough=0.6, group="Dock (on shirt)"))
v, f = slab_from_poly(rrect(POD["w"], POD["h"], POD["r"], 10), rigid, FABRIC_T*0.5 + 1.0, FABRIC_T*0.5 + 1.0 + POD["t"], fillet=3.0, rings=6)
meshes.append(Mesh(v, f, "M2_Hub_pod", C["pod"], rough=0.45, explode=EXP_POD, group="M2 Collar hub pod"))
v, f = cylinder(rigid(np.array([[POD["w"]/2 - 9, 0]]), FABRIC_T*0.5 + POD["t"] + 0.6)[0], n, 1.8, 0.8)
meshes.append(Mesh(v, f, "M2_LED_lightpipe", C["pod_led"], explode=EXP_POD, group="M2 Collar hub pod"))
v, f = cylinder(rigid(np.array([[-POD["w"]/2 + 10, 0]]), FABRIC_T*0.5 + POD["t"] + 0.6)[0], n, 3.5, 0.9)
meshes.append(Mesh(v, f, "M2_Button", C["snap"], metallic=0.6, rough=0.4, explode=EXP_POD, group="M2 Collar hub pod"))

# ECG electrodes (inside face)
for key, label in (("ecgR", "R"), ("ecgL", "L")):
    p = MOD[key]; pl = placer(p["s"], p["z"])
    v, f = slab_from_poly(rrect(ECG["w"], ECG["h"], ECG["r"], 8), pl, -FABRIC_T*0.5 - 0.8, -FABRIC_T*0.5 - 0.1, fillet=0.2, rings=1)
    meshes.append(Mesh(v, f, f"M3_ECG_electrode_{label}", C["ecg"], metallic=0.7, rough=0.35, group="M3 Textile ECG electrodes"))

# traces: Manhattan routes along the surface (horizontal at the sensor height, then vertical to the hub)
TR = 1.2; trace_paths = {}
def surf_path(pts, off):
    out = []
    for (s0, z0), (s1, z1) in zip(pts[:-1], pts[1:]):
        L = np.hypot(s1 - s0, z1 - z0); k = max(2, int(L / 6))
        for t in np.linspace(0, 1, k, endpoint=False): out.append(surf(s0 + (s1 - s0)*t, z0 + (z1 - z0)*t, off))
    out.append(surf(pts[-1][0], pts[-1][1], off)); return np.array(out)
wired = (["m1"] if BUNDLE else ["temp", "imu", "sweat"]) + ["ecgR", "ecgL"]
for k in wired:
    p = MOD[k]
    if k in ("m1",):
        for i, sig in enumerate(["3V3", "GND", "SDA", "SCL"]):
            off = (i - 1.5)*5.0
            a = {"s": p["s"] + off, "z": p["z"] + PATCH["h"]/2 + 2}; b = {"s": hp["s"] + off, "z": podz - POD["h"]/2}
            trace_paths[sig] = PL.manhattan(a, b)
    else:
        b = {"s": hp["s"] + (8 if k == "ecgR" else -8 if k == "ecgL" else 0), "z": podz - POD["h"]/2}
        lane = hp["s"] + (70 if k == "ecgR" else -70) if k.startswith("ecg") else None
        trace_paths[k] = PL.manhattan(p, b, lane)
tr = []
for k, pts in trace_paths.items():
    pts = [q for i, q in enumerate(pts) if i == 0 or np.hypot(q[0] - pts[i-1][0], q[1] - pts[i-1][1]) > 0.5]
    v, f = tube(surf_path(pts, FABRIC_T*0.5 + 0.9), TR, 8); tr.append(Mesh(v, f, "", C["trace"]))
meshes.append(merge(tr, "Conductive_thread_traces_TPU_taped", C["trace"], metallic=0.6, rough=0.4, group="Traces (in shirt)"))

# optional arm pod on the chosen sleeve
hr = MOD["hr"]; side = 1 if hr["side"] == "R" else -1
root, ax, up, fw = sleeve_frames[side]
cen = root - ax*25 + ax*(hr["t"]*(SLEEVE["length"]+25)); rad = SLEEVE["r0"] + (SLEEVE["r1"]-SLEEVE["r0"])*hr["t"]
ang = np.radians(hr["ang_deg"]); nrm = np.cos(ang)*up + np.sin(ang)*fw; o2 = cen + nrm*rad; tzv = np.cross(nrm, ax)
def rigid2(pts2d, off):
    pts2d = np.atleast_2d(pts2d); return o2 + pts2d[:, :1]*ax + pts2d[:, 1:2]*tzv + off*nrm
v, f = slab_from_poly(rrect(ARMPOD["w"], ARMPOD["h"], ARMPOD["r"], 8), rigid2, 0.5, 0.5 + ARMPOD["t"], fillet=2.5, rings=5)
meshes.append(Mesh(v, f, "M4_Optional_arm_optical_HR_pod", C["armpod"], rough=0.45, explode=tuple((nrm*50).tolist()), group="M4 Optional arm HR pod"))
pz = MOD["m1"]["z"]
write_glb(os.path.join(OUT, 'RSAF_HeatStrain_Shirt_Assembly.glb'), meshes)
# also STL of the full assembly (single body, for viewing)
allm = merge(meshes, "all", (1, 1, 1, 1))
write_stl(os.path.join(OUT, 'RSAF_HeatStrain_Shirt_Assembly_view_only.stl'), allm.v, allm.f, "assembly")
# save geometry for drawings / renders
np.savez_compressed(os.path.join(OUT, 'meshes.npz'), **{f"{i}_v": m.v for i, m in enumerate(meshes)}, **{f"{i}_f": m.f for i, m in enumerate(meshes)})
json.dump([{"name": m.name, "color": m.color, "group": m.group, "explode": m.explode} for m in meshes], open(os.path.join(OUT, 'meshes.json'), 'w'))
json.dump({"placement": P, "pz": pz, "podz": podz, "Cz_ecg": circumference(385), "C_chest": circumference(430), "C_waist": circumference(120), "C_hem": circumference(0),
           "trace_paths": trace_paths}, open(os.path.join(OUT, 'layout.json'), 'w'), default=float)
print("meshes", len(meshes), "tris", sum(len(m.f) for m in meshes))

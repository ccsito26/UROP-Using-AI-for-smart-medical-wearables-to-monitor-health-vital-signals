import numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from params import *
from geom import circumference, rrect, circle
from drawlib import *
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
import matplotlib.image as mpimg

D = os.path.join(os.path.dirname(__file__), 'out'); DW = os.path.join(D, 'drawings'); os.makedirs(DW, exist_ok=True)
lay = json.load(open(os.path.join(D, 'layout.json')))
N = 5
pz = BNP_Z - PATCH["centre_below_bnp"]; podz = BNP_Z - POD["centre_below_bnp"]
sheets = []

# ============ SHEET 1: GENERAL ARRANGEMENT (garment flats 1:5), driven by placement.json ============
import placement as PL
PLC = lay["placement"]; MODS = PLC["modules"]; BUNDLE = PLC["bundleM1"]
fig, ax = sheet('GENERAL ARRANGEMENT – SENSOR PLACEMENT, SIZE M', 'UROP-HSS-001', 1, N, '1:5')
S = 0.2
def flat_outline(front=True):
    hw = lambda z: circumference(z)/4
    d = np.radians(SLEEVE["droop_deg"]); dirv = np.array([np.cos(d), -np.sin(d)])
    A = np.array([hw(530), 530.0]); Sh = np.array([218.0, 652.0])
    right = [np.array([hw(0), 0.0]), np.array([hw(120), 120]), np.array([hw(260), 260]), np.array([hw(400), 400]), A, A + dirv*120, Sh + dirv*205, Sh, np.array([82.0, 700.0])]
    nc = 615.0 if front else 690.0
    curve = [np.array([82*np.cos(t*np.pi/2), 700 - (700 - nc)*np.sin(t*np.pi/2)]) for t in np.linspace(0, 1, 12)]
    pts = right + curve[1:]
    return np.array(pts + [np.array([-p[0], p[1]]) for p in pts[::-1]][1:-1])
def flat_xy(sv, z):
    w = PL.where(sv, z)
    return (False, sv, z) if w["back"] else (True, -np.sign(sv)*w["dcf"], z)
OX = {True: 110, False: 300}; OY = 120
def T(front, x, z): return np.array([OX[front] + x*S, OY + z*S])
for front, title in ((True, 'FRONT FLAT (outside view)'), (False, 'BACK FLAT (outside view)')):
    poly(ax, np.array([T(front, *p) for p in flat_outline(front)]), lw=THICK)
    cl(ax, T(front, 0, -15), T(front, 0, 730))
    view_title(ax, OX[front], OY + 162, title, 'compression-fit 80/20 polyester–elastane knit; positions from placement.json')
    ax.plot([T(front, -190, BNP_Z)[0], T(front, 190, BNP_Z)[0]], [T(front, 0, BNP_Z)[1]]*2, lw=0.2, color=INK, ls=(0, (3, 2)))
    ax.text(*(T(front, 0, -10) + [1.5, -1]), 'CF' if front else 'CB', fontsize=5, color=INK, va='top')
bnp = T(False, 0, BNP_Z); ax.plot(*bnp, 'o', ms=2, color=ACC); ax.text(bnp[0] + 2, bnp[1] + 3, 'BNP (≈C7)', fontsize=5, color=ACC)
# traces
for k, pts in lay["trace_paths"].items():
    dense = []
    for (s0, z0), (s1, z1) in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 40): dense.append(flat_xy(s0 + (s1 - s0)*t, z0 + (z1 - z0)*t))
    seg = []
    for q in dense + [None]:
        if q is None or (seg and seg[-1][0] != q[0]):
            if len(seg) > 1: ax.plot(*np.array([T(p[0], p[1], p[2]) for p in seg]).T, lw=0.6, color=ACC, zorder=1)
            seg = []
        if q is not None: seg.append(q)
# modules
SIZES = {"m1": (PATCH["w"], PATCH["h"], '#2a2c2e', 'M1'), "temp": (50, 50, '#2563eb', 'T'), "imu": (30, 26, '#c2410c', 'IMU'), "sweat": (40, 40, '#0891b2', 'SW'),
         "hub": (POD["w"], POD["h"], '#111111', 'M2'), "ecgR": (ECG["w"], ECG["h"], None, 'M3-R'), "ecgL": (ECG["w"], ECG["h"], None, 'M3-L')}
keys = (["m1"] if BUNDLE else ["temp", "imu", "sweat"]) + ["hub", "ecgR", "ecgL"]
dim_slot = {True: 0, False: 0}
for k in keys:
    p = MODS[k]; front, x, z = flat_xy(p["s"], p["z"]); w, h, col, tag = SIZES[k]; c = T(front, x, z)
    if col: rr(ax, *c, w, h, min(w, h)*0.2, s=S, lw=MED, ec=INK, fc=col, alpha=0.9)
    else: rr(ax, *c, w, h, 8, s=S, lw=MED, ec=BLUE, ls=(0, (3, 1.5)))
    ax.text(*c, tag, fontsize=4.2, ha='center', va='center', color='white' if col else BLUE, zorder=6)
    # vertical dim from BNP level, horizontal from CB/CF (staggered lanes per flat)
    side = 1 if x >= 0 else -1; i = dim_slot[front]; dim_slot[front] += 1
    xl = T(front, side*(205 + 22*i), 0)[0]
    dimv(ax, c[1], T(front, 0, BNP_Z)[1], c[0], c[0], xl, s=S, fs=4.3)
    yl = c[1] - (h/2*S + 3 + 0*i)
    if abs(x) > 3: dimh(ax, T(front, 0, 0)[0], c[0], c[1], c[1], yl - 2.5, s=S, fs=4.3)
leg = 'Positions are the centre of each item, measured along the garment surface. Orange = conductive-thread traces. Dashed = inside face.'
ax.text(14, OY - 8, leg, fontsize=4.6, color='#555')
# evidence table
rows = [('Item', 'Vertical (below BNP)', 'Lateral', 'Region', 'Evidence', 'Basis')]
items = (["m1"] if BUNDLE else []) + ["temp", "imu", "sweat", "hub", "ecgR", "ecgL", "hr"]
NM = {"m1": "M1 patch (holds T, IMU, SW)", "temp": "  Skin-temperature sensor" if BUNDLE else "Skin-temperature pod", "imu": "  Gait IMU" if BUNDLE else "Gait IMU pod",
      "sweat": "  Sweat sensor" if BUNDLE else "Sweat sensor pod", "hub": "M2 hub pod", "ecgR": "M3 ECG electrode R", "ecgL": "M3 ECG electrode L", "hr": "M4 arm HR pod (option)"}
for k in items:
    p = PL.effective(PLC, k) if k != "m1" else MODS["m1"]
    if p["kind"] == "sleeve":
        vert, lat = f'{p["side"]} sleeve', f'{int(p["t"]*100)}% along'
    else:
        w = PL.where(p["s"], p["z"]); vert = f'{BNP_Z - p["z"]:.0f}'
        lat = (f'{w["dcb"]:.0f} {"R" if p["s"] >= 0 else "L"} of CB' if w["back"] else f'{w["dcf"]:.0f} {"R" if p["s"] >= 0 else "L"} of CF')
    if k == "m1":
        e = {"region": PL.region(p["s"], p["z"])["name"], "score": None, "cite": "see rows below"}
        rows.append((NM[k], vert, lat, e["region"], '', 'see rows below')); continue
    e = PL.score(k, p); cite = e["cite"] if len(e["cite"]) < 58 else e["cite"][:55] + '…'
    rows.append((NM[k], vert, lat, e["region"], f'{PL.label(e["score"])} {e["score"]:.2f}', cite))
table(ax, 14, 100, [44, 24, 24, 50, 20, 70], rows, fs=4.3, row_h=4.2)
notes(ax, 260, 100, 'NOTES', [
    'Generated from Source/placement.json (exported by the\nSensor Placement Configurator). Re-run build_all.py after edits.',
    'Evidence scores (0–1) are the team\'s reading of the consolidated\nliterature review, not published values; see placement_rules.json.',
    'Grade ±10 mm per size step (S/L) along the same landmarks.',
    'Rucksack zones flagged in the configurator: shoulder straps,\nback panel and hip belt (to confirm with RSAF).'], fs=4.5, lh=3.0)
sheets.append(fig)

# ============ SHEET 2: M1 BACK PATCH (1:1 and section 3:1) ============
fig, ax = sheet('M1 BACK THERMAL-GAIT PATCH – DETAIL', 'UROP-HSS-002', 2, N, '1:1 (section 2.5:1)')
W, H, R = PATCH["w"], PATCH["h"], PATCH["r"]
# outer face view
cx, cy = 62, 205
view_title(ax, cx, 281, 'OUTER FACE (away from body)', 'scale 1:1')
rr(ax, cx, cy, W, H, R, lw=THICK, fc='#e9e9e7')
rr(ax, cx, cy, W - 5, H - 5, R - 2.5, lw=THIN, ls='--')
circ(ax, cx + W/2 - 14, cy - H/2 + 12, 4, lw=THIN, fc='#4caf50'); label(ax, cx + W/2 - 11, cy - H/2 + 4.5, 'status LED', fs=4.2)
for sx, sy in [(-30, 39), (30, 39), (-30, -39), (30, -39)]:
    circ(ax, cx + sx, cy + sy, 12, lw=THIN, ls=(0, (2, 1)))
cl(ax, (cx - W/2 - 6, cy), (cx + W/2 + 6, cy)); cl(ax, (cx, cy - H/2 - 6), (cx, cy + H/2 + 6))
dimh(ax, cx - W/2, cx + W/2, cy + H/2, cy + H/2, cy + H/2 + 7); dimv(ax, cy - H/2, cy + H/2, cx - W/2, cx - W/2, cx - W/2 - 8)
ax.text(cx + W/2 - 2, cy + H/2 - 9, f'R{R}', fontsize=5, color=INK, ha='right')
ax.plot([cx - W/2 - 10, cx + W/2 + 10], [cy - 2, cy - 2], lw=0.4, color=ACC); label(ax, cx + W/2 + 11, cy - 2, 'A', fs=7, color=ACC, va='center'); label(ax, cx - W/2 - 14, cy - 2, 'A', fs=7, color=ACC, va='center')
label(ax, cx, cy + 10, 'TPU 95A housing\n(matte, olive/black)', fs=4.6, ha='center')
# skin face view
cx2 = 158
view_title(ax, cx2, 281, 'SKIN / SHIRT FACE', 'scale 1:1')
rr(ax, cx2, cy, W, H, R, lw=THICK, fc='#f6f6f4')
circ(ax, cx2, cy, PATCH["boss_d"], lw=MED, fc='#dcdcd8')
circ(ax, cx2, cy, 40, lw=THIN, ls='--'); circ(ax, cx2, cy, 6, lw=THIN, fc='#999')
# interdigitated sweat electrodes on annulus (schematic arcs)
for k in range(10):
    a0 = k*36 + 4
    ax.add_patch(Arc((cx2, cy), 43, 43, theta1=a0, theta2=a0 + 26, lw=0.5, color=BLUE))
for sx, sy in [(-30, 39), (30, 39), (-30, -39), (30, -39)]:
    circ(ax, cx2 + sx, cy + sy, 12, lw=MED, fc='#bfc3c7'); circ(ax, cx2 + sx, cy + sy, 7, lw=THIN)
for (sx, sy), pin in zip([(-30, 39), (30, 39), (-30, -39), (30, -39)], ['S1 3V3', 'S2 GND', 'S3 SDA', 'S4 SCL']):
    label(ax, cx2 + sx, cy + sy + (8.5 if sy > 0 else -10), pin, fs=4.4, ha='center')
cl(ax, (cx2 - W/2 - 6, cy), (cx2 + W/2 + 6, cy)); cl(ax, (cx2, cy - H/2 - 6), (cx2, cy + H/2 + 6))
dimh(ax, cx2 - 30, cx2 + 30, cy + 39, cy + 39, cy + H/2 + 7); dimv(ax, cy - 39, cy + 39, cx2 + 30, cx2 + 30, cx2 + W/2 + 8)
dimd(ax, cx2, cy, PATCH["boss_d"], ang=-35, out=26); dimd(ax, cx2 + 30, cy - 39, 12, ang=-50, out=6)
leader(ax, (cx2, cy), (cx2 + 50, cy + 30), 'TMP117 ±0.1 °C in 1.0 mm\nPETG floor (skin contact)', fs=4.6)
leader(ax, (cx2 - 19, cy + 8), (cx2 + 47, cy + 8), 'Embroidered labyrinth RTD\n(re-digitised to Ø40 dashed)', fs=4.6)
leader(ax, (cx2 + 18, cy - 12), (cx2 + 50, cy - 24), 'Interdigitated Ag-thread\nsweat/wetness electrodes', fs=4.6, color=BLUE)
# section A-A at 3:1 (true scale both axes), half section from centreline to edge
k = 2.5; X0, Y0 = 262, 205      # X0 = centreline, Y0 = shirt outer surface (z = 0)
view_title(ax, X0 + 63, 281, 'SECTION A–A (half)', 'scale 2.5:1 · snap rotated into section plane')
def lay(x0, x1, z0, z1, fc, hatch=None, lw=THIN):
    hatch_poly(ax, [(X0 + x0*k, Y0 + z0*k), (X0 + x1*k, Y0 + z0*k), (X0 + x1*k, Y0 + z1*k), (X0 + x0*k, Y0 + z1*k)], fc=fc, hatch=hatch, lw=lw)
L = [('Shirt fabric 0.8', (27, 42, -0.8, 0.0), '#a3ab93', None),
     ('Elastic window binding', (25, 27, -1.2, 0.6), '#333', None),
     ('Dock TPU 0.6', (27, 42, 0.0, 0.6), '#d4d6d0', None),
     ('Female snap (riveted)', (24, 36, 0.0, 0.6), '#9aa0a6', 'xxxx'),
     ('Magnet N52 Ø12 × 2', (24, 36, 0.6, 2.6), '#c7cbd1', '\\\\\\'),
     ('TPU 95A carrier', (23, 42, 2.6, 5.6), '#4a4d50', '////'),
     ('TPU cover 1.0', (0, 42, 5.6, 6.6), '#4a4d50', '////'),
     ('Boss cup PETG wall', (21.5, 23, -3.3, 5.6), '#ece9e1', '....'),
     ('Boss floor 1.0 (skin)', (0, 23, -3.3, -2.3), '#ece9e1', '....'),
     ('Closed-cell PE foam 3.0', (0, 21.5, -2.3, 0.7), '#9cc0ea', None),
     ('Flex PCB 0.2 + IMU/ADC', (0, 21.5, 0.7, 0.9), '#2e7d4f', None),
     ('TMP117 on floor', (0, 1.6, -2.3, -1.5), '#111', None)]
for name, (x0, x1, z0, z1), c, h in L:
    lay(x0, x1, z0, z1, c, h)
lay(23, 24, 0.6, 2.6, '#4a4d50', '////')
lay(5, 9, 0.9, 1.9, '#111'); lay(12, 16, 0.9, 1.8, '#111')
ax.plot([X0 + 36*k, X0 + 42*k], [Y0 + 2.6*k, Y0 + 2.6*k], lw=THIN, color=INK)
cl(ax, (X0, Y0 - 16), (X0, Y0 + 26)); label(ax, X0 - 1, Y0 + 27, 'CL', fs=5, ha='center')
ax.plot([X0 - 6, X0 + 42*k + 4], [Y0 - 3.3*k, Y0 - 3.3*k], lw=0.5, color=ACC, ls=':')
label(ax, X0 - 7, Y0 - 3.3*k, 'SKIN', fs=5.5, ha='right', va='center', color=ACC)
label(ax, X0 - 7, Y0, 'shirt\nsurface', fs=4.6, ha='right', va='center', color='#555')
for i, (name, (x0, x1, z0, z1), c, h) in enumerate(L):
    p = (X0 + (x0 + x1)/2*k, Y0 + (z0 + z1)/2*k)
    q = (X0 + 42*k + 12, Y0 + 30 - i*5.4)
    ax.plot([p[0], q[0] - 1], [p[1], q[1]], lw=0.18, color='#666'); ax.add_patch(Circle(p, 0.35, color='#666'))
    label(ax, q[0], q[1], name, fs=4.5, va='center')
dimv(ax, Y0 - 3.3*k, Y0 + 6.6*k, X0 + 42*k, X0 + 42*k, X0 + 42*k + 5, s=k, text='9.9')
dimv(ax, Y0, Y0 + 6.6*k, X0 + 23*k, X0 + 23*k, X0 + 23*k - 1, s=k, text='6.6')
dimv(ax, Y0 - 3.3*k, Y0, X0 + 12*k, X0 + 12*k, X0 + 19*k, s=k, text='3.3 to skin')
dimh(ax, X0, X0 + 23*k, Y0 - 3.3*k, Y0 - 3.3*k, Y0 - 3.3*k - 7, s=k, text='R23 (Ø46 boss)')
dimh(ax, X0, X0 + 42*k, Y0 + 6.6*k, Y0 + 6.6*k, Y0 + 6.6*k + 14, s=k, text='42 (½ width)')
# BOM
rows = [('Item', 'Part', 'Spec / suggested part', 'Qty'), ('1', 'Carrier/housing', 'TPU 95A, FDM or cast silicone Shore 60A; file M1_back_patch_carrier_TPU95A.stl', '1'),
        ('2', 'Sensing boss cup', 'PETG, 1.0 mm floor; file M1_sensing_boss_cup.stl', '1'),
        ('3', 'Skin temperature', 'TMP117 (±0.1 °C) bonded with thermal epoxy to floor', '1'),
        ('4', 'Insulation', 'Closed-cell PE foam, 3 mm, Ø43 (after Richmond et al., 2015)', '1'),
        ('5', 'IMU', 'LSM6DSO / BMI270, 6-axis, ≥104 Hz (128 Hz as Buller et al., 2022)', '1'),
        ('6', 'ADC for textile sensors', 'ADS1115 16-bit: RTD bridge, sweat electrodes, contact', '1'),
        ('7', 'Flex PCB', '0.2 mm polyimide, I²C bus, 0603 status LED', '1'),
        ('8', 'Magnetic snaps', 'Ø12 × 2 N52, Ni-plated, conductive (3V3/GND/SDA/SCL)', '4'),
        ('9', 'Textile RTD + sweat', 'Ag-coated thread, embroidered on boss annulus', '1 set')]
table(ax, 14, 140, [9, 34, 120, 10], rows, fs=4.6)
notes(ax, 200, 140, 'NOTES', [
    'Mass target ≤ 30 g; profile 6.6 mm so a rucksack back panel presses it on, not off.',
    'Boss passes through the Ø50 elastic-bound mesh window to touch skin;\nfoam above the sensor approximates an insulated skin site.',
    'I²C at 100 kHz over 4 snaps + ~80 mm couched-thread traces (≤ 10 Ω each).',
    'Prototype 1 labyrinth (65.0 × 73.6 mm) must be re-digitised to ≤ Ø40\nto fit the boss, or kept as a research-only textile RTD.',
    'Seal: 1 mm perimeter lip; IP54 target; wipe with 70% alcohol.',
], fs=4.6, lh=3.0)
sheets.append(fig)

# ============ SHEET 3: M2 HUB POD (2:1) ============
fig, ax = sheet('M2 COLLAR HUB POD – DETAIL', 'UROP-HSS-003', 3, N, '2:1')
k = 2.0; W, H, T, R = POD["w"], POD["h"], POD["t"], POD["r"]
cx, cy = 95, 205
view_title(ax, cx, 272, 'TOP VIEW (lid removed, internals dashed)', 'scale 2:1')
rr(ax, cx, cy, W, H, R, s=k, lw=THICK)
rr(ax, cx, cy, W - 3.6, H - 3.6, R - 1.8, s=k, lw=THIN)
def box(x, y, w, h, txt, c='#e5e7eb', ls='--'):
    ax.add_patch(Rectangle((cx + (x - w/2)*k, cy + (y - h/2)*k), w*k, h*k, fc=c, ec=INK, lw=THIN, ls=ls, alpha=0.9))
    label(ax, cx + x*k, cy + y*k, txt, fs=4.3, ha='center', va='center')
box(-12, 0, 34, 25, 'LiPo 502535\n3.7 V 400 mAh', '#dbeafe')
box(18, 0, 24, 29, '', '#d1fae5')
box(18, 4.5, 22.5, 18, 'ESP32-S3\nSuper Mini', '#a7f3d0', '-')
box(11, -9.5, 7, 7, 'ECG\nAFE', '#fde68a', '-')
box(24.5, -9.5, 9, 9, 'buzzer', '#fecaca', '-')
label(ax, cx + 18*k, cy - 14.5*k + 1.2, 'carrier PCB 24 × 29', fs=4.0, ha='center', color='#065f46')
# lid-mounted parts (dotted)
for (x, y, d, t) in [(-6, 6, 10, 'haptic Ø10\n(on lid)'), (-W/2 + 10, 0, 7.6, 'button'), (W/2 - 9, 0, 3.2, '')]:
    circ(ax, cx + x*k, cy + y*k, d, s=k, lw=0.5, ls=':', ec=ACC)
    if t: label(ax, cx + x*k, cy + y*k - (d*k/2 + 3.5), t, fs=4.0, ha='center', va='center', color=ACC)
for sx in (-W/2 + 6, W/2 - 6): circ(ax, cx + sx*k, cy, 2.2, s=k, lw=THIN)
label(ax, cx - W/2*k, cy - H/2*k - 6, 'Legend: dashed = internal (in tray) · dotted orange = mounted on lid', fs=4.4)
leader(ax, (cx + (W/2 - 9)*k, cy + 2), (cx + 80, cy + 50), 'LED light pipe Ø3.2 (lid)', fs=4.6)
leader(ax, (cx + (-W/2 + 10)*k, cy + 6), (cx - 85, cy + 50), 'Button Ø7.6 (acknowledge alert)', fs=4.6)
dimh(ax, cx - W/2*k, cx + W/2*k, cy + H/2*k, cy + H/2*k, cy + H/2*k + 8, s=k); dimv(ax, cy - H/2*k, cy + H/2*k, cx - W/2*k, cx - W/2*k, cx - W/2*k - 8, s=k)
# front view (section) and side view
fx, fy = 95, 118
view_title(ax, fx, 152, 'FRONT VIEW', 'scale 2:1')
pts = [(fx - W/2*k, fy), (fx + W/2*k, fy), (fx + W/2*k, fy + (T - 3)*k), (fx + (W/2 - 3)*k, fy + T*k), (fx - (W/2 - 3)*k, fy + T*k), (fx - W/2*k, fy + (T - 3)*k)]
poly(ax, pts, lw=THICK); ax.plot([fx - W/2*k, fx + W/2*k], [fy + 9*k, fy + 9*k], lw=THIN, color=INK)
for px in (np.arange(6) - 2.5)*4: ax.add_patch(Rectangle((fx + px*k - 1, fy - 1.5*k), 2, 1.5*k, fc='#d4a017', ec=INK, lw=0.2))
dimv(ax, fy, fy + T*k, fx + W/2*k, fx + W/2*k, fx + W/2*k + 8, s=k); dimv(ax, fy, fy + 9*k, fx - W/2*k, fx - W/2*k, fx - W/2*k - 8, s=k, prefix='tray ')
label(ax, fx, fy - 8, 'pogo pins protrude 1.5 below base', fs=4.4, ha='center')
sx_, sy_ = 230, 118
view_title(ax, sx_, 152, 'SIDE VIEW', 'scale 2:1')
pts = [(sx_ - H/2*k, sy_), (sx_ + H/2*k, sy_), (sx_ + H/2*k, sy_ + (T - 3)*k), (sx_ + (H/2 - 3)*k, sy_ + T*k), (sx_ - (H/2 - 3)*k, sy_ + T*k), (sx_ - H/2*k, sy_ + (T - 3)*k)]
poly(ax, pts, lw=THICK); dimh(ax, sx_ - H/2*k, sx_ + H/2*k, sy_, sy_, sy_ - 8, s=k)
# bottom view
bx, by = 290, 205
view_title(ax, bx, 272, 'BOTTOM VIEW (dock face)', 'scale 2:1')
rr(ax, bx, by, W, H, R, s=k, lw=THICK)
for i, (px, pin) in enumerate(zip((np.arange(6) - 2.5)*4, POGO_PINS)):
    circ(ax, bx + px*k, by - 6*k, 2.2, s=k, lw=THIN, fc='#d4a017')
    ax.text(bx + px*k, by - 6*k - 6.5, pin, fontsize=3.9, ha='center', rotation=90, va='top')
for mx in (-22, 22): circ(ax, bx + mx*k, by + 4*k, 8, s=k, lw=THIN, fc='#9aa0a6');
label(ax, bx, by + 4*k, 'alignment magnets Ø8 ×2 (opposite polarity = keyed)', fs=4.2, ha='center', va='center')
dimh(ax, bx - 10*k, bx + 10*k, by - 6*k, by - 6*k, by + H/2*k + 8, s=k, text='5 × 4.0 = 20')
rows = [('Item', 'Part', 'Spec / suggested part', 'Qty'), ('1', 'Base tray', 'PETG/ABS, 1.8 wall; M2_hub_pod_base_tray.stl', '1'), ('2', 'Lid', 'PETG/ABS 2.0 + locating lip; M2_hub_pod_lid.stl', '1'),
        ('3', 'MCU + radio', 'ESP32-S3 Super Mini (BLE 5 to commander app)', '1'), ('4', 'ECG front end', 'MAX30003 (2-electrode ECG, R-R output)', '1'),
        ('5', 'Battery', 'LiPo 502535, 400 mAh (target ≥ 10 h)', '1'), ('6', 'Charger / power', 'Li-ion charger + 3.3 V LDO, charge via pogo', '1'),
        ('7', 'Haptic', 'Coin ERM Ø10 × 2.7 (Level 1 vibration)', '1'), ('8', 'Buzzer', '9 × 9 mm, ≥ 85 dB (Levels 2–4 beeps)', '1'),
        ('9', 'Pogo connector', '6-pin, 4.0 pitch, spring-loaded, gold', '1'), ('10', 'Fasteners', 'M2 × 8 self-tapping', '2')]
table(ax, 14, 95, [9, 30, 92, 9], rows, fs=4.5)
notes(ax, 165, 95, 'NOTES', ['Mass target ≤ 35 g. Sits on back yoke above the M1 dock, below the collar band.',
    'Alert outputs: L1 vibration; L2 2 beeps; L3 3 beeps + orange LED; L4 repeated 4–5 beeps + red LED\nand BLE push to commander and medic.',
    'Pogo dock pinout matches sheet 4; pins 1–4 are the I²C bus shared with M1.',
    'Charge pod off-body; keyed magnets prevent reversed docking.'], fs=4.6, lh=3.0)
sheets.append(fig)

# ============ SHEET 4: INTERFACES & ELECTRICAL ============
fig, ax = sheet('INTERFACES, PINOUT AND SYSTEM BLOCK DIAGRAM', 'UROP-HSS-004', 4, N, '1:1 / NTS')
cx, cy = 75, 200
view_title(ax, cx, 283, 'M1 DOCK ON SHIRT (outside view)', 'scale 1:1')
rr(ax, cx, cy, DOCK["w"], DOCK["h"], DOCK["r"], lw=THICK, fc='#eceee9')
circ(ax, cx, cy, PATCH["window_d"], lw=MED, fc='#bbb', hatch='xxxx')
rr(ax, cx, cy, PATCH["w"], PATCH["h"], PATCH["r"], lw=THIN, ls=(0, (2, 1.5)))
for (sx, sy), pin in zip([(-30, 39), (30, 39), (-30, -39), (30, -39)], ['S1 3V3', 'S2 GND', 'S3 SDA', 'S4 SCL']):
    circ(ax, cx + sx, cy + sy, 12, lw=MED, fc='#c7cbd1'); label(ax, cx + sx, cy + sy, pin.split()[0], fs=4.4, ha='center', va='center')
    label(ax, cx + sx + (8 if sx > 0 else -8), cy + sy + 6.5, pin.split()[1], fs=4.6, ha='center', color=ACC)
dimh(ax, cx - 55, cx + 55, cy + 60, cy + 60, cy + 68); dimv(ax, cy - 60, cy + 60, cx - 55, cx - 55, cx - 63)
dimh(ax, cx - 30, cx + 30, cy - 39, cy - 39, cy - 70); dimv(ax, cy - 39, cy + 39, cx + 30, cx + 30, cx + 64)
dimd(ax, cx, cy, PATCH["window_d"], ang=210, out=8)
label(ax, cx, cy - 80, 'Dashed: M1 patch outline when attached', fs=4.4, ha='center')
# block diagram
bx = 160
def blk(x, y, w, h, title, lines, c):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.6,rounding_size=2', fc=c, ec=INK, lw=0.4))
    ax.text(x + w/2, y + h - 2.5, title, fontsize=5.6, fontweight='bold', ha='center', va='top', color=INK)
    ax.text(x + 2, y + h - 8, '\n'.join(lines), fontsize=4.5, va='top', color=INK, linespacing=1.3)
view_title(ax, 285, 272, 'SYSTEM BLOCK DIAGRAM', 'not to scale')
blk(bx, 205, 62, 52, 'M1 BACK PATCH', ['TMP117 skin temp (insulated)', 'IMU 6-axis @128 Hz (gait)', 'ADS1115: textile RTD bridge,', '  sweat/wetness, contact', 'Status LED'], '#e5e7eb')
blk(bx + 85, 205, 70, 52, 'M2 HUB POD', ['ESP32-S3 (BLE 5)', 'MAX30003 ECG → R-R → HR', 'Algorithms: ECTemp (+skin), PSI,', '  gait regularity, alert levels', 'Haptic · buzzer · LED · button', 'LiPo 400 mAh + charger'], '#d1fae5')
blk(bx + 178, 205, 50, 52, 'PHONE / C2 APP', ['Section commander +', 'medic dashboard', 'Soldier symptom', '  one-tap report', 'Location on L4'], '#dbeafe')
blk(bx + 85, 150, 70, 34, 'M3 ECG ELECTRODES', ['Ag-knit, inside front', '±95 from CF at xiphoid level', 'Passive – washable'], '#fde68a')
blk(bx, 150, 62, 34, 'M4 ARM HR (OPTION)', ['Optical upper-arm HR', 'BLE direct to hub'], '#f3f4f6')
def arr(p, q, t='', c=INK):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=6, lw=0.6, color=c))
    if t: ax.text((p[0] + q[0])/2, (p[1] + q[1])/2 + 2, t, fontsize=4.4, ha='center', color=c, bbox=dict(fc='white', ec='none', pad=0.2))
arr((bx + 62.6, 231), (bx + 84.4, 231), 'I²C ×4 snaps', ACC)
arr((bx + 120, 184.6), (bx + 120, 204.4), 'ECG_R / ECG_L', ACC)
arr((bx + 155.6, 231), (bx + 177.4, 231), 'BLE', BLUE)
arr((bx + 62.6, 167), (bx + 84.4, 200), 'BLE', BLUE)
# pinout tables
rows = [('Pogo pin', 'Signal', 'Source / dest.', 'Trace'), ('1', '3V3', 'M2 → M1 snap S1', 'Ag thread ×2 strands'), ('2', 'GND', 'M2 ↔ M1 snap S2', 'Ag thread ×2 strands'),
        ('3', 'SDA', 'M2 ↔ M1 snap S3', 'Ag thread, 4.7 kΩ pull-up in M2'), ('4', 'SCL', 'M2 → M1 snap S4', 'Ag thread, 4.7 kΩ pull-up in M2'),
        ('5', 'ECG_R', 'M3 right electrode', 'Ag thread, routed R side, ≥ 8 mm from I²C'), ('6', 'ECG_L', 'M3 left electrode', 'Ag thread, routed L side')]
table(ax, 160, 140, [16, 16, 38, 62], rows, fs=4.6)
rows = [('Alert level', 'Output on M2', 'Who is notified'), ('0 Normal', '—', '—'), ('1 Advisory', 'Vibration', 'Soldier'), ('2 Caution', '2 beeps + vibration', 'Soldier, commander'),
        ('3 Warning', '3 beeps + orange LED', 'Soldier, commander, medic'), ('4 Emergency', 'Repeated 4–5 beeps + red LED', 'Commander + medic first, with location')]
table(ax, 300, 140, [24, 38, 46], rows, fs=4.6)
notes(ax, 14, 108, 'TRACE AND CONNECTOR SPECIFICATION', [
    'Traces: silver-coated polyamide thread couched (zig-zag) for stretch, laminated under 10 mm TPU hot-melt tape on the inside face.',
    'Target ≤ 10 Ω per trace after 50 wash cycles; test per sheet 1 note 4. Keep ECG leads ≥ 8 mm from I²C lines and route symmetrically.',
    'Snaps (M1) and pogo (M2) are the only wet-mating contacts: gold/nickel plated, wipe-clean, magnet retention ≥ 10 N per snap.',
    'Shirt carries no batteries or electronics → machine-washable at 40 °C with modules removed.',
    'Female snaps riveted through dock + fabric with a backing washer; strain-relief stitch loop on every trace end.',
], fs=4.6, lh=3.0)
sheets.append(fig)

# ============ SHEET 5: EXPLODED ISOMETRIC ============
fig, ax = sheet('EXPLODED ISOMETRIC ASSEMBLY', 'UROP-HSS-005', 5, N, 'NTS')
sys.path.insert(0, os.path.dirname(__file__))
from render import exploded_image
pts = exploded_image(os.path.join(D, 'exploded.png'), explode=2.2, azim=-140, elev=18)
img = mpimg.imread(os.path.join(D, 'exploded.png'))
x0, y0, sz = 20, 40, 215
ax.imshow(img, extent=(x0, x0 + sz, y0, y0 + sz), zorder=1)
calls = [(("M1_Back_patch_housing", "Skin_temperature_pod_housing"), 1, (250, 225)), (("M2_Hub_pod",), 2, (250, 260)), (("M3_ECG_electrode_R",), 3, (250, 150)),
         (("M4_Optional_arm_optical_HR_pod",), 4, (14 + 8, 250)), (("Conductive_thread_traces_TPU_taped",), 5, (250, 120)), (("Dock_M1_Back_patch", "Dock_Skin_temperature_pod"), 6, (250, 190)),
         (("M1_Back_patch_sensing_boss", "Gait_IMU_pod_housing"), 7, (250, 205)), (("Shirt_body",), 8, (30, 70))]
for names_, n, q in calls:
    nm = next((x for x in names_ if x in pts), None)
    if nm is None: continue
    fx, fy = pts[nm]; p = (x0 + fx*sz, y0 + fy*sz)
    balloon(ax, p, q, n)
rows = [('No.', 'Item', 'Detachable?', 'Drawing'), ('1', 'M1 back thermal-gait patch', 'Yes – 4 magnetic snaps', '002'), ('2', 'M2 collar hub pod', 'Yes – magnetic pogo dock', '003'),
        ('3', 'M3 textile ECG electrodes', 'No – knitted in, washable', '001'), ('4', 'M4 arm optical HR pod (option)', 'Yes – sleeve pocket', '001'),
        ('5', 'Conductive-thread traces', 'No – TPU-taped', '004'), ('6', 'Dock panel + female snaps + window', 'No – laminated', '004'),
        ('7', 'Sensing boss (skin side of 1)', 'With M1', '002'), ('8', 'Base shirt, compression knit', '—', '001')]
table(ax, 262, 270, [9, 58, 52, 16], rows, fs=4.8)
notes(ax, 262, 215, 'WHY THIS LAYOUT (evidence)', [
    'Gait + ECTemp flagged 6/6 heat strokes ≥ 3.5 min early with 0.9–6.1% false\npositives using a TRUNK accelerometer (Buller et al., 2022) → M1 on the back.',
    'HR + insulated upper-back skin temperature estimated core within\n0.25–0.29 °C (Eggenberger et al., 2018; Welles et al., 2018) → M1 boss + foam.',
    'Upper-arm optical HR is accurate (MAPE 1.35%) (Schweizer & Gilgen-Ammann,\n2025) → optional M4 if ECG electrodes prove unreliable under load.',
    'Removing all electronics lets the shirt be laundered and the modules\nswabbed and shared between soldiers (RSAF detachability requirement).',
    'Open risk: upper-back gait site not yet validated against L5/chest under\na rucksack – see literature review Section 9 test protocol.',
], fs=4.8, lh=3.1)
label(ax, x0 + 4, y0 + 4, 'Rendered from RSAF_HeatStrain_Shirt_Assembly.glb (shirt shown translucent; modules exploded)', fs=4.4, color='#555')
sheets.append(fig)

with PdfPages(os.path.join(DW, 'RSAF_HeatStrain_Shirt_Drawing_Set_UROP-HSS-001-005.pdf')) as pdf:
    for i, f in enumerate(sheets):
        pdf.savefig(f); f.savefig(os.path.join(DW, f'sheet{i+1}.png'), dpi=110)
print('ok')

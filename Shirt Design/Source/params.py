"""Design parameters (mm) for the RSAF heat-strain shirt with detachable sensing patches.
Size M (chest 960 mm body / 1000 mm garment, compression fit with 4% negative-to-zero ease)."""
import numpy as np

# ---- Garment body (half-width a, half-depth b of torso cross-section vs height z above hem) ----
# z = 0 hem, z = 700 back neck point (BNP, ~C7)
TORSO_Z = np.array([0, 120, 260, 400, 470, 530, 590, 640, 675, 700])
TORSO_A = np.array([172, 165, 170, 182, 186, 188, 196, 150, 95, 72])
TORSO_B = np.array([118, 112, 118, 128, 130, 126, 112, 95, 72, 62])
SUPER_N = 2.6           # superellipse exponent (boxier than ellipse)
FABRIC_T = 0.8          # base fabric thickness (80/20 polyester/elastane knit)
SLEEVE = dict(root_z=560, root_x=185, length=210, r0=78, r1=66, droop_deg=28)
BNP_Z = 700

# ---- Module M1: back thermal-gait-sweat patch (detachable, external mount, through-window sensing) ----
PATCH = dict(
    w=84, h=104, r=14,            # outer footprint (rounded rectangle)
    t=6.0,                        # total thickness above shirt surface
    centre_below_bnp=100,         # centre 100 mm below BNP -> over T2-T4 between scapulae
    boss_d=46, boss_proj=2.5,     # sensing boss through the shirt window, projects 2.5 mm to skin
    window_d=50,                  # elastic-bound mesh window in shirt
    snap_pitch_x=60, snap_pitch_y=78, snap_d=12, snap_h=3.2,   # 4 magnetic snaps (also electrical)
    foam_t=3.0,                   # closed-cell insulation over the skin sensor (after Richmond et al., 2015)
    laby_w=65.0, laby_h=73.6,     # Prototype 1 labyrinth RTD footprint (Ink/Stitch file)
)
DOCK = dict(w=110, h=120, r=16, t=0.6)   # TPU-laminated reinforcement panel on shirt carrying female snaps

# ---- Module M2: collar hub pod (ESP32-S3, battery, ECG AFE, haptic, buzzer) ----
POD = dict(w=64, h=34, t=13.0, r=8, centre_below_bnp=20)   # sits on back yoke just under collar band
POGO_PINS = ["3V3", "GND", "SDA", "SCL", "ECG_R", "ECG_L"]

# ---- Module M3: textile ECG electrodes (inside, passive, washable silver knit) ----
ECG = dict(w=42, h=78, r=10, z=385, s_from_cf=95)   # z above hem (xiphoid level), +/- from centre front

# ---- Module M4 (optional): upper-arm optical HR pod in sleeve pocket ----
ARMPOD = dict(w=36, h=36, t=10, r=9)

SNAP_PINS = {"S1 (top-left)": "3V3", "S2 (top-right)": "GND", "S3 (bottom-left)": "SDA", "S4 (bottom-right)": "SCL"}

COLORS = {
    "shirt": (0.30, 0.34, 0.24, 0.55),     # olive, semi-transparent
    "collar": (0.22, 0.25, 0.18, 1.0),
    "dock": (0.62, 0.64, 0.60, 1.0),
    "patch": (0.13, 0.14, 0.15, 1.0),
    "boss": (0.85, 0.85, 0.82, 1.0),
    "window": (0.10, 0.10, 0.10, 0.65),
    "snap": (0.80, 0.80, 0.82, 1.0),
    "trace": (0.80, 0.45, 0.20, 1.0),
    "pod": (0.08, 0.08, 0.09, 1.0),
    "pod_led": (0.10, 0.75, 0.30, 1.0),
    "ecg": (0.78, 0.80, 0.84, 1.0),
    "armpod": (0.15, 0.15, 0.17, 1.0),
    "foam": (0.30, 0.55, 0.85, 1.0),
    "pcb": (0.05, 0.40, 0.20, 1.0),
}

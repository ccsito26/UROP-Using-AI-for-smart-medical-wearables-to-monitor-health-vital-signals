"""Load placement.json (from the Sensor Placement Configurator) and score it with placement_rules.json."""
import json, os, numpy as np
from params import *
from geom import circumference

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = json.load(open(os.path.join(HERE, 'placement_rules.json')))

def default_placement():
    Cx = circumference(385)
    return {"version": 1, "size": "M", "bundleM1": True, "modules": {
        "m1": {"kind": "torso", "s": 0, "z": 600}, "temp": {"kind": "torso", "s": 0, "z": 615},
        "imu": {"kind": "torso", "s": 0, "z": 560}, "sweat": {"kind": "torso", "s": 0, "z": 560},
        "hub": {"kind": "torso", "s": 0, "z": 680},
        "ecgR": {"kind": "torso", "s": round(Cx/2 - 95, 1), "z": 385}, "ecgL": {"kind": "torso", "s": round(-(Cx/2 - 95), 1), "z": 385},
        "hr": {"kind": "sleeve", "side": "L", "t": 0.5, "ang_deg": 0}}}

def load():
    p = os.path.join(HERE, 'placement.json')
    if os.path.exists(p):
        return json.load(open(p))
    d = default_placement(); json.dump(d, open(p, 'w'), indent=1); return d

def where(s, z):
    C = circumference(z); dcb = abs(s); dcf = C/2 - abs(s)
    return dict(C=C, dcb=dcb, dcf=dcf, back=dcb < C/4)

def _in(v, r): return r is None or (r[0] <= v <= r[1])

def region(s, z):
    w = where(s, z)
    for r in RULES["regions"]:
        if r["side"] == "back" and not w["back"]: continue
        if r["side"] == "front" and w["back"]: continue
        if not _in(z, r.get("z")): continue
        if "dcb" in r and not _in(w["dcb"], r["dcb"]): continue
        if "dcf" in r and not _in(w["dcf"], r["dcf"]): continue
        return r
    return RULES["regions"][-1]

def gear(s, z, which=("rucksack",)):
    w = where(s, z); out = []
    for gk in which:
        for zn in RULES["gear"][gk]["zones"]:
            if zn["side"] == "back" and not w["back"]: continue
            if zn["side"] == "front" and w["back"]: continue
            if not _in(z, zn.get("z")): continue
            if "dcb" in zn and not _in(w["dcb"], zn["dcb"]): continue
            if "dcf" in zn and not _in(w["dcf"], zn["dcf"]): continue
            out.append(zn)
    return out

def score(key, p):
    S = RULES["sensors"]["ecgR" if key == "ecgL" else key]
    if p["kind"] == "sleeve":
        if key == "hr":
            a = p["ang_deg"] % 360; rid = "upper_arm_outer" if (a <= 110 or a >= 250) else "upper_arm_inner"
            v = S["scores"][rid]; name = [r["name"] for r in RULES["sleeve_regions"] if r["id"] == rid][0]
        else:
            v = S["scores"].get("sleeve", [0, "Belongs on the torso.", "-"]); name = "Sleeve"
        return dict(score=v[0], why=v[1], cite=v[2], region=name)
    r = region(p["s"], p["z"])
    v = S["scores"]["torso"] if key == "hr" else S["scores"].get(r["id"], [0.3, "No specific evidence for this site.", "team assessment"])
    return dict(score=v[0], why=v[1], cite=v[2], region=r["name"])

def label(x): return 'Strong' if x >= .85 else 'Moderate' if x >= .65 else 'Weak' if x >= .45 else 'Avoid'

def effective(P, key):
    if key in ("temp", "imu", "sweat") and P["bundleM1"]: return P["modules"]["m1"]
    return P["modules"][key]

def manhattan(a, b, lane=None):
    """trace path in (s, z): horizontal at a.z (short way round) to a vertical lane (default b.s), up/down, then across to b"""
    tgt = b["s"] if lane is None else lane
    C = circumference(a["z"]); ds = tgt - a["s"]
    if ds > C/2: ds -= C
    if ds < -C/2: ds += C
    pts = [(a["s"], a["z"]), (a["s"] + ds, a["z"]), (a["s"] + ds, b["z"])]
    if lane is not None: pts.append((b["s"], b["z"]))
    return pts

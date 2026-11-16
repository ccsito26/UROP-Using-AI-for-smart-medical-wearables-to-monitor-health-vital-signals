import numpy as np, json, struct
from params import *

# ---------------- mesh container ----------------
class Mesh:
    def __init__(self, v, f, name, color, metallic=0.0, rough=0.7, explode=(0, 0, 0), group=None):
        self.v = np.asarray(v, float); self.f = np.asarray(f, np.int64)
        self.name, self.color, self.metallic, self.rough = name, color, metallic, rough
        self.explode = list(map(float, explode)); self.group = group or name

def merge(meshes, name, color, **kw):
    vs, fs, off = [], [], 0
    for m in meshes:
        vs.append(m.v); fs.append(m.f + off); off += len(m.v)
    return Mesh(np.vstack(vs), np.vstack(fs), name, color, **kw)

# ---------------- torso surface ----------------
def _interp(z, arr): return np.interp(z, TORSO_Z, arr)

def torso_point(z, th):
    a, b = _interp(z, TORSO_A), _interp(z, TORSO_B)
    c, s = np.cos(th), np.sin(th); e = 2.0 / SUPER_N
    return np.stack([a * np.sign(c) * np.abs(c) ** e, b * np.sign(s) * np.abs(s) ** e, np.broadcast_to(z, np.shape(th)).astype(float)], -1)

_TH = np.linspace(-np.pi / 2, 3 * np.pi / 2, 2001)   # theta from back midline (-pi/2) round both ways
from functools import lru_cache
def _arc_table(z):
    return _arc_cached(round(float(z), 1))
@lru_cache(maxsize=None)
def _arc_cached(z):
    p = torso_point(np.full_like(_TH, z), _TH)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    return d   # arc length from back midline going toward +x side (subject's left when facing +y?)

def circumference(z): return _arc_table(z)[-1]

def surf(s, z, off=0.0):
    """(s = signed arc length from centre back, + toward +x), z -> 3D point offset along outward normal."""
    s = np.asarray(s, float); z = np.asarray(z, float)
    out = np.zeros(np.broadcast(s, z).shape + (3,))
    for idx in np.ndindex(out.shape[:-1]):
        si = float(np.broadcast_to(s, out.shape[:-1])[idx]); zi = float(np.broadcast_to(z, out.shape[:-1])[idx])
        d = _arc_table(zi); C = d[-1]
        si = (si + C) % C
        th = np.interp(si, d, _TH)
        p = torso_point(zi, th); n = normal(zi, th)
        out[idx] = p + off * n
    return out

def normal(z, th, h=1e-3, hz=0.5):
    p1, p2 = torso_point(z, th + h), torso_point(z, th - h)
    q1, q2 = torso_point(z + hz, th), torso_point(z - hz, th)
    n = np.cross(p1 - p2, q1 - q2); n = n / np.linalg.norm(n)
    c = torso_point(z, th); c2 = c.copy(); c2[2] = 0
    if np.dot(n, c2) < 0: n = -n
    return n

def surf_frame(s, z):
    """origin, tangent_s (unit), tangent_z (unit), normal"""
    o = surf(s, z); ts = surf(s + 0.5, z) - surf(s - 0.5, z); tz = surf(s, z + 0.5) - surf(s, z - 0.5)
    ts /= np.linalg.norm(ts); n = np.cross(ts, tz); n /= np.linalg.norm(n)
    c = o.copy(); c[2] = 0
    if np.dot(n, c) < 0: n = -n
    tz = np.cross(n, ts)
    return o, ts, tz, n

# ---------------- primitives ----------------
def grid_surface(fn, nu, nv, closed_u=False):
    """fn(u,v)->(nu,nv,3) points; returns verts, faces"""
    P = fn; nu_, nv_ = P.shape[:2]
    v = P.reshape(-1, 3); f = []
    U = nu_ if closed_u else nu_ - 1
    for i in range(U):
        i2 = (i + 1) % nu_
        for j in range(nv_ - 1):
            a, b, c, d = i * nv_ + j, i2 * nv_ + j, i2 * nv_ + j + 1, i * nv_ + j + 1
            f += [(a, b, c), (a, c, d)]
    return v, np.array(f)

def rrect(w, h, r, n=10):
    """rounded rectangle polygon CCW centred at 0"""
    pts = []
    for cx, cy, a0 in [(w/2-r, h/2-r, 0), (-w/2+r, h/2-r, 90), (-w/2+r, -h/2+r, 180), (w/2-r, -h/2+r, 270)]:
        for k in range(n + 1):
            a = np.radians(a0 + 90 * k / n); pts.append((cx + r*np.cos(a), cy + r*np.sin(a)))
    return np.array(pts)

def circle(rad, n=40):
    a = np.linspace(0, 2*np.pi, n, endpoint=False); return np.c_[rad*np.cos(a), rad*np.sin(a)]

def slab_from_poly(poly, place, h0, h1, fillet=1.0, rings=4):
    """Closed slab: poly (2D, convex) -> place(x,y,offset)->3D. Bottom at offset h0, top at h1, top edge rounded."""
    levels = []  # (scale_inset, offset)
    levels.append((0.0, h0))
    for k in range(rings + 1):
        a = np.pi/2 * k / rings
        levels.append((fillet * (1 - np.cos(a)), h1 - fillet + fillet*np.sin(a)))
    cen = poly.mean(0)
    def inset(p, d):
        v = p - cen; L = np.linalg.norm(v, axis=1, keepdims=True); return p - v / np.maximum(L, 1e-9) * d
    rings_pts = [place(inset(poly, d), off) for d, off in levels]
    n = len(poly); V = np.vstack(rings_pts); F = []
    for r in range(len(rings_pts) - 1):
        for i in range(n):
            a, b = r*n + i, r*n + (i+1) % n; c, d = b + n, a + n
            F += [(a, b, c), (a, c, d)]
    # caps with concentric rings for conformal curvature
    def cap(base_pts2d, off, flip):
        nonlocal V
        start = len(V); ringsN = 5; idx = []
        for k in range(ringsN):
            sc = 1 - k / ringsN
            pts = cen + (base_pts2d - cen) * sc
            V = np.vstack([V, place(pts, off)]); idx.append(start + k*n)
        V = np.vstack([V, place(cen[None], off)]); ci = len(V) - 1
        fs = []
        for k in range(ringsN - 1):
            for i in range(n):
                a, b = idx[k] + i, idx[k] + (i+1) % n; c, d = idx[k+1] + (i+1) % n, idx[k+1] + i
                fs += [(a, c, b), (a, d, c)] if flip else [(a, b, c), (a, c, d)]
        for i in range(n):
            a, b = idx[-1] + i, idx[-1] + (i+1) % n
            fs.append((a, ci, b) if flip else (a, b, ci))
        return fs
    F += cap(poly, h0, True)
    F += cap(inset(poly, fillet), h1, False)
    return V, np.array(F)

def tube(path, r, n=10):
    path = np.asarray(path, float); V = []; F = []
    for i, p in enumerate(path):
        t = path[min(i+1, len(path)-1)] - path[max(i-1, 0)]; t /= np.linalg.norm(t)
        a = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(t, a); u /= np.linalg.norm(u); w = np.cross(t, u)
        for k in range(n):
            ang = 2*np.pi*k/n; V.append(p + r*(np.cos(ang)*u + np.sin(ang)*w))
    m = len(path)
    for i in range(m - 1):
        for k in range(n):
            a, b = i*n + k, i*n + (k+1) % n; F += [(a, b, b+n), (a, b+n, a+n)]
    V = np.array(V); c0 = len(V); V = np.vstack([V, path[0], path[-1]])
    for k in range(n):
        F.append((c0, (k+1) % n, k)); F.append((c0+1, (m-1)*n + k, (m-1)*n + (k+1) % n))
    return V, np.array(F)

def cylinder(origin, axis, r, h, n=28):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    return tube([np.asarray(origin, float), np.asarray(origin, float) + axis*h], r, n)

# ---------------- heightfield solid (printable, watertight) ----------------
def heightfield(mask_fn, height_fn, w, h, res=0.4):
    """Watertight 2.5-D solid: columns of height H over a grid; holes where H<=0. Walls split at all
    break heights on each vertical grid line (no T-junctions)."""
    nx, ny = int(round(w/res)), int(round(h/res))
    xs = -w/2 + (np.arange(nx) + 0.5)*res; ys = -h/2 + (np.arange(ny) + 0.5)*res
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    H = np.where(mask_fn(X, Y), height_fn(X, Y), 0.0); H = np.round(H, 4); M = H > 1e-6
    verts = {}; V = []; F = []
    def vid(i, j, z):
        key = (i, j, z)
        if key not in verts:
            verts[key] = len(V); V.append((-w/2 + i*res, -h/2 + j*res, z))
        return verts[key]
    walls = []; breaks = {}
    def hb(i, j):
        return H[i, j] if (0 <= i < nx and 0 <= j < ny and M[i, j]) else 0.0
    for i in range(nx):
        for j in range(ny):
            if not M[i, j]: continue
            z = H[i, j]
            a, b, c, d = vid(i, j, z), vid(i+1, j, z), vid(i+1, j+1, z), vid(i, j+1, z)
            F += [(a, b, c), (a, c, d)]
            a, b, c, d = vid(i, j, 0.0), vid(i+1, j, 0.0), vid(i+1, j+1, 0.0), vid(i, j+1, 0.0)
            F += [(a, c, b), (a, d, c)]
            for di, dj, p, q in [(1, 0, (i+1, j), (i+1, j+1)), (-1, 0, (i, j+1), (i, j)), (0, 1, (i+1, j+1), (i, j+1)), (0, -1, (i, j), (i+1, j))]:
                zn = hb(i+di, j+dj)
                if zn < z:
                    walls.append((p, q, zn, z))
                    for pt in (p, q): breaks.setdefault(pt, set()).update((zn, z))
    for p, q, z0, z1 in walls:
        L = sorted(b for b in breaks[p] if z0 <= b <= z1); R = sorted(b for b in breaks[q] if z0 <= b <= z1)
        Lv = [vid(p[0], p[1], b) for b in L]; Rv = [vid(q[0], q[1], b) for b in R]
        li = ri = 0
        while li < len(Lv) - 1 or ri < len(Rv) - 1:
            if ri < len(Rv) - 1 and (li == len(Lv) - 1 or R[ri+1] <= L[li+1]):
                F.append((Lv[li], Rv[ri], Rv[ri+1])); ri += 1
            else:
                F.append((Lv[li], Rv[ri], Lv[li+1])); li += 1
    # top faces also need splitting where a lower neighbour top edge meets taller walls: handled since top edges are horizontal
    return np.array(V, float), np.array(F)

def rrect_mask(w, h, r):
    def m(X, Y):
        dx = np.maximum(np.abs(X) - (w/2 - r), 0); dy = np.maximum(np.abs(Y) - (h/2 - r), 0)
        return (np.abs(X) <= w/2) & (np.abs(Y) <= h/2) & (dx**2 + dy**2 <= r**2)
    return m

# ---------------- exporters ----------------
def vertex_normals(v, f):
    n = np.zeros_like(v); fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3): np.add.at(n, f[:, k], fn)
    L = np.linalg.norm(n, axis=1, keepdims=True); return n / np.maximum(L, 1e-12)

def write_stl(path, v, f, name="part"):
    v = np.asarray(v, np.float32); tri = v[f]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); L = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = nrm / np.maximum(L, 1e-12)
    with open(path, 'wb') as fh:
        fh.write(name.encode()[:80].ljust(80, b' ')); fh.write(struct.pack('<I', len(f)))
        rec = np.zeros(len(f), dtype=[('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
        rec['n'] = nrm; rec['v'] = tri; fh.write(rec.tobytes())

def write_glb(path, meshes, scale=0.001):
    """meshes -> GLB (metres, Y-up). Our frame: x right, y front, z up -> glTF: x, z_up->y, y_front->z"""
    buf = bytearray(); bviews = []; accs = []; gl_meshes = []; mats = []; nodes = []; groups = {}
    def add_view(data, target):
        while len(buf) % 4: buf.append(0)
        off = len(buf); buf.extend(data); bviews.append({"buffer": 0, "byteOffset": off, "byteLength": len(data), "target": target}); return len(bviews) - 1
    for m in meshes:
        v = m.v[:, [0, 2, 1]].copy(); v[:, 2] *= 1; v = (v * scale).astype(np.float32)
        f = m.f.astype(np.uint32)
        nrm = vertex_normals(v, f).astype(np.float32)
        bv = add_view(v.tobytes(), 34962); accs.append({"bufferView": bv, "componentType": 5126, "count": len(v), "type": "VEC3", "min": v.min(0).tolist(), "max": v.max(0).tolist()}); pa = len(accs) - 1
        bv = add_view(nrm.tobytes(), 34962); accs.append({"bufferView": bv, "componentType": 5126, "count": len(v), "type": "VEC3"}); na = len(accs) - 1
        bv = add_view(f.reshape(-1).tobytes(), 34963); accs.append({"bufferView": bv, "componentType": 5125, "count": int(f.size), "type": "SCALAR"}); ia = len(accs) - 1
        r, g, b, a = m.color
        mat = {"name": m.name + "_mat", "pbrMetallicRoughness": {"baseColorFactor": [r, g, b, a], "metallicFactor": m.metallic, "roughnessFactor": m.rough}, "doubleSided": True}
        if a < 1: mat["alphaMode"] = "BLEND"
        mats.append(mat)
        gl_meshes.append({"name": m.name, "primitives": [{"attributes": {"POSITION": pa, "NORMAL": na}, "indices": ia, "material": len(mats) - 1}]})
        nodes.append({"name": m.name, "mesh": len(gl_meshes) - 1})
        ex = np.array(m.explode)[[0, 2, 1]] * scale
        groups.setdefault(m.group, {"children": [], "explode": ex.tolist()})["children"].append(len(nodes) - 1)
    root_children = []
    for gname, g in groups.items():
        nodes.append({"name": gname, "children": g["children"], "extras": {"explode": g["explode"]}}); root_children.append(len(nodes) - 1)
    nodes.append({"name": "RSAF_HeatStrain_Shirt_Assembly", "children": root_children}); root = len(nodes) - 1
    gltf = {"asset": {"version": "2.0", "generator": "UROP procedural CAD (numpy)"}, "scene": 0, "scenes": [{"nodes": [root]}], "nodes": nodes,
            "meshes": gl_meshes, "materials": mats, "accessors": accs, "bufferViews": bviews, "buffers": [{"byteLength": len(buf)}]}
    js = json.dumps(gltf).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    while len(buf) % 4: buf.append(0)
    total = 12 + 8 + len(js) + 8 + len(buf)
    with open(path, 'wb') as fh:
        fh.write(struct.pack('<III', 0x46546C67, 2, total)); fh.write(struct.pack('<II', len(js), 0x4E4F534A)); fh.write(js)
        fh.write(struct.pack('<II', len(buf), 0x004E4942)); fh.write(bytes(buf))

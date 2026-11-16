import numpy as np, json, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
D = os.path.join(os.path.dirname(__file__), 'out')
meta = json.load(open(os.path.join(D, 'meshes.json'))); npz = np.load(os.path.join(D, 'meshes.npz'))

def collect(explode=0.0, hide=(), alpha_shirt=None, light=(0.3, -0.8, 0.6)):
    polys, cols = [], []
    L = np.array(light); L /= np.linalg.norm(L)
    for i, m in enumerate(meta):
        if any(h in m["name"] for h in hide): continue
        v = npz[f"{i}_v"] + explode*np.array(m["explode"]); f = npz[f"{i}_f"]
        tri = v[f]; n = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        sh = 0.45 + 0.55*np.abs(n @ L)
        r, g, b, a = m["color"]
        if alpha_shirt is not None and m["group"] == "Shirt": a = alpha_shirt
        c = np.c_[np.clip(np.outer(sh, [r, g, b]), 0, 1), np.full(len(f), a)]
        polys.append(tri); cols.append(c)
    return np.vstack(polys), np.vstack(cols)

def render(ax, elev, azim, explode=0.0, hide=(), alpha_shirt=None, zoom=None, light=(0.3, -0.8, 0.6)):
    P, Cc = collect(explode, hide, alpha_shirt, light)
    pc = Poly3DCollection(P, facecolors=Cc, edgecolors='none', linewidths=0)
    ax.add_collection3d(pc)
    if zoom is None:
        lo, hi = P.reshape(-1, 3).min(0), P.reshape(-1, 3).max(0)
    else:
        lo, hi = np.array(zoom[0]), np.array(zoom[1])
    c = (lo + hi)/2; r = (hi - lo).max()/2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()

if __name__ == '__main__':
    fig = plt.figure(figsize=(16, 8), dpi=110)
    for k, (el, az, ex, al, title) in enumerate([(12, -90, 0, None, 'Back'), (12, 90, 0, None, 'Front (shirt semi-transparent)'), (18, -125, 1, None, 'Exploded, back-left'), (5, -90, 0, None, 'Back patch close-up')]):
        ax = fig.add_subplot(1, 4, k+1, projection='3d')
        zoom = ([-90, -200, 520], [90, -60, 720]) if k == 3 else None
        render(ax, el, az, explode=ex, zoom=zoom); ax.set_title(title)
    plt.tight_layout(); plt.savefig(os.path.join(D, 'preview.png'))

def exploded_image(path, explode=1.6, elev=16, azim=-128, alpha_shirt=0.35):
    from mpl_toolkits.mplot3d import proj3d
    fig = plt.figure(figsize=(7, 7), dpi=300); ax = fig.add_axes([0, 0, 1, 1], projection='3d')
    render(ax, elev, azim, explode=explode, alpha_shirt=alpha_shirt)
    fig.canvas.draw(); M = ax.get_proj(); pts = {}
    for i, m in enumerate(meta):
        v = npz[f"{i}_v"] + explode*np.array(m["explode"]); c = v.mean(0)
        if m["name"] in ("Shirt_body",): c = np.array([150, 60, 300])
        x, y, _ = proj3d.proj_transform(c[0], c[1], c[2], M)
        X, Y = ax.transData.transform((x, y)); W, H = fig.canvas.get_width_height()
        pts[m["name"]] = (X/W, Y/H)
    fig.savefig(path, transparent=True); plt.close(fig)
    return pts

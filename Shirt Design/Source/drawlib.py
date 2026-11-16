import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle, FancyBboxPatch, Arc
from geom import rrect, circle

A3 = (420, 297)
INK = '#1b2430'; THIN = 0.25; MED = 0.5; THICK = 0.8; ACC = '#c2410c'; BLUE = '#1f5f8b'

def sheet(title, dwg_no, sheet_no, n_sheets, scale, rev='A'):
    fig = plt.figure(figsize=(A3[0]/25.4, A3[1]/25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, A3[0]); ax.set_ylim(0, A3[1]); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=THICK, ec=INK))
    ax.add_patch(Rectangle((5, 5), 410, 287, fill=False, lw=THIN, ec=INK))
    for k in range(8):   # zone marks
        x = 10 + 50*k + 25; ax.text(x, 7.5, str(k+1), ha='center', va='center', fontsize=5, color=INK); ax.text(x, 289.5, str(k+1), ha='center', va='center', fontsize=5, color=INK)
    for k, L in enumerate('ABCDEF'):
        y = 287 - 46.17*k - 23; ax.text(7.5, y, L, ha='center', va='center', fontsize=5, color=INK); ax.text(412.5, y, L, ha='center', va='center', fontsize=5, color=INK)
    # title block (bottom right) 180 x 36
    x0, y0, w, h = 230, 10, 180, 36
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=MED, ec=INK))
    rows = [(x0, y0+24, 180, 12), (x0, y0+12, 120, 12), (x0+120, y0+12, 60, 12), (x0, y0, 60, 12), (x0+60, y0, 40, 12), (x0+100, y0, 40, 12), (x0+140, y0, 40, 12)]
    for r in rows: ax.add_patch(Rectangle(r[:2], r[2], r[3], fill=False, lw=THIN, ec=INK))
    def cell(x, y, lab, val, fs=7, bold=False):
        ax.text(x+1.5, y+9.5, lab, fontsize=4.2, color='#555', va='top')
        ax.text(x+1.5, y+3.0, val, fontsize=fs, color=INK, va='bottom', fontweight='bold' if bold else 'normal')
    cell(x0, y0+24, 'TITLE', title, 8.5, True)
    cell(x0, y0+12, 'PROJECT', 'NUS UROP · RSAF heat-strain shirt with detachable sensing patches', 6.2)
    cell(x0+120, y0+12, 'DRAWING NO. / REV', f'{dwg_no}  /  {rev}', 7, True)
    cell(x0, y0, 'SUPERVISOR / DRAWN', 'Prof Tang Kok Zuea / UROP team', 5.6)
    cell(x0+60, y0, 'SCALE (A3)', scale, 6.5)
    cell(x0+100, y0, 'DATE', '10 Nov 2026', 6.5)
    cell(x0+140, y0, 'SHEET', f'{sheet_no} of {n_sheets}', 6.5)
    # units / projection box
    ax.add_patch(Rectangle((x0-50, y0), 50, 18, fill=False, lw=THIN, ec=INK))
    ax.text(x0-48.5, y0+15.5, 'UNITS mm  ·  GEN. TOL. ±0.5 (rigid) / ±3 (garment)', fontsize=3.6, color=INK, va='top')
    proj_symbol(ax, x0-38, y0+6)
    ax.text(x0-27, y0+6, 'THIRD-ANGLE\nPROJECTION', fontsize=3.8, color=INK, va='center')
    ax.add_patch(Rectangle((x0-50, y0+18), 50, 18, fill=False, lw=THIN, ec=INK))
    ax.text(x0-48.5, y0+33.5, 'STATUS', fontsize=4.2, color='#555', va='top')
    ax.text(x0-48.5, y0+21, 'CONCEPT – FOR\nRSAF REVIEW WK 13', fontsize=5.6, color=ACC, va='bottom', fontweight='bold')
    return fig, ax

def proj_symbol(ax, x, y):
    ax.add_patch(Polygon([(x-7, y-2.5), (x-7, y+2.5), (x-1, y+3.5), (x-1, y-3.5)], closed=True, fill=False, lw=THIN, ec=INK))
    ax.add_patch(Circle((x+5, y), 3.5, fill=False, lw=THIN, ec=INK)); ax.add_patch(Circle((x+5, y), 1.6, fill=False, lw=THIN, ec=INK))
    ax.plot([x-8, x+10], [y, y], lw=0.15, color=INK, dashes=(4, 1, 1, 1))

def poly(ax, pts, lw=MED, ec=INK, fc='none', ls='-', z=2, alpha=1, hatch=None):
    p = Polygon(pts, closed=True, fill=fc != 'none', fc=fc, ec=ec, lw=lw, ls=ls, zorder=z, alpha=alpha, hatch=hatch); ax.add_patch(p); return p

def rr(ax, cx, cy, w, h, r, s=1.0, **kw):
    return poly(ax, rrect(w*s, h*s, r*s, 8) + [cx, cy], **kw)

def circ(ax, cx, cy, d, s=1.0, **kw):
    return poly(ax, circle(d*s/2, 60) + [cx, cy], **kw)

def cl(ax, p0, p1, lw=0.18):   # centre line
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], lw=lw, color=INK, dashes=(6, 1.5, 1.2, 1.5), zorder=1)

def _ext(ax, p, q, color):
    e = np.array(q, float) - np.array(p, float); L = np.linalg.norm(e)
    if L > 0.3:
        e = e/L; ax.plot([p[0] + e[0]*0.8, q[0] + e[0]*1.5], [p[1] + e[1]*0.8, q[1] + e[1]*1.5], lw=0.15, color=color)

def _dimtext(ax, x, y, t, rot, fs, color):
    ax.text(x, y, t, fontsize=fs, ha='center', va='center', rotation=rot, color=color, bbox=dict(fc='white', ec='none', pad=0.25), zorder=8)

def _fmt(val):
    return f'{val:.0f}' if abs(val - round(val)) < 0.05 else f'{val:.1f}'

def dimh(ax, x0, x1, y0, y1, yl, s=1.0, text=None, fs=5.0, color=INK, prefix=''):
    """horizontal dim between points (x0,y0),(x1,y1) drawn at y = yl; value = |x1-x0|/s"""
    _ext(ax, (x0, y0), (x0, yl), color); _ext(ax, (x1, y1), (x1, yl), color)
    ax.annotate('', xy=(x1, yl), xytext=(x0, yl), arrowprops=dict(arrowstyle='<|-|>', lw=0.25, color=color, mutation_scale=4, shrinkA=0, shrinkB=0))
    _dimtext(ax, (x0 + x1)/2, yl, prefix + (text or _fmt(abs(x1 - x0)/s)), 0, fs, color)

def dimv(ax, y0, y1, x0, x1, xl, s=1.0, text=None, fs=5.0, color=INK, prefix=''):
    _ext(ax, (x0, y0), (xl, y0), color); _ext(ax, (x1, y1), (xl, y1), color)
    ax.annotate('', xy=(xl, y1), xytext=(xl, y0), arrowprops=dict(arrowstyle='<|-|>', lw=0.25, color=color, mutation_scale=4, shrinkA=0, shrinkB=0))
    _dimtext(ax, xl, (y0 + y1)/2, prefix + (text or _fmt(abs(y1 - y0)/s)), 90, fs, color)

def dimd(ax, cx, cy, d, s=1.0, ang=45, fs=5.0, color=INK, out=6):
    """diameter leader"""
    a = np.radians(ang); p = np.array([cx + d*s/2*np.cos(a), cy + d*s/2*np.sin(a)]); q = p + out*np.array([np.cos(a), np.sin(a)])
    ax.annotate('', xy=p, xytext=q, arrowprops=dict(arrowstyle='-|>', lw=0.25, color=color, mutation_scale=4))
    ax.text(q[0] + 0.5, q[1], f'Ø{_fmt(d)}', fontsize=fs, color=color, va='center', ha='left')

def label(ax, x, y, text, fs=6, **kw):
    ax.text(x, y, text, fontsize=fs, color=kw.pop('color', INK), **kw)

def balloon(ax, p, q, n, fs=5.5, color=ACC):
    ax.plot([p[0], q[0]], [p[1], q[1]], lw=0.3, color=color); ax.add_patch(Circle(p, 0.6, color=color))
    ax.add_patch(Circle(q, 3.2, fc='white', ec=color, lw=0.5, zorder=5)); ax.text(*q, str(n), fontsize=fs, ha='center', va='center', color=color, zorder=6, fontweight='bold')

def leader(ax, p, q, text, fs=5.2, ha='left', color=INK):
    ax.annotate(text, xy=p, xytext=q, fontsize=fs, color=color, ha=ha, va='center',
                arrowprops=dict(arrowstyle='-|>', lw=0.25, color=color, mutation_scale=4, shrinkA=0.5, shrinkB=0.3))

def table(ax, x, y, col_w, rows, fs=5.0, header=True, row_h=4.6, wrap=None):
    """rows: list of tuples. x,y = top-left."""
    yy = y
    for i, r in enumerate(rows):
        hgt = row_h * max(1, max(str(c).count('\n') + 1 for c in r))
        xx = x
        for j, c in enumerate(r):
            fc = '#1b2430' if (header and i == 0) else ('#f3f1ec' if i % 2 == 0 else 'white')
            ax.add_patch(Rectangle((xx, yy - hgt), col_w[j], hgt, fc=fc, ec='#9aa0a6', lw=0.2))
            ax.text(xx + 1.0, yy - hgt/2, str(c), fontsize=fs, va='center', ha='left', color='white' if (header and i == 0) else INK,
                    fontweight='bold' if (header and i == 0) else 'normal')
            xx += col_w[j]
        yy -= hgt
    return yy

def notes(ax, x, y, title, lines, fs=5.2, width=None, lh=3.4):
    ax.text(x, y, title, fontsize=fs + 1, fontweight='bold', color=INK, va='top'); y -= lh*1.6
    for i, l in enumerate(lines):
        ax.text(x, y, f'{i+1}.', fontsize=fs, color=INK, va='top')
        ax.text(x + 4, y, l, fontsize=fs, color=INK, va='top', linespacing=1.25)
        y -= lh * (l.count('\n') + 1) + 0.6
    return y

def hatch_poly(ax, pts, fc='white', hatch='////', ec=INK, lw=THIN, z=3):
    p = Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z); ax.add_patch(p); return p

def view_title(ax, x, y, text, sub=None):
    ax.text(x, y, text, fontsize=7, fontweight='bold', color=INK, ha='center', va='top')
    if sub: ax.text(x, y - 3.6, sub, fontsize=5, color='#555', ha='center', va='top')

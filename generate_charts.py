import os, re, collections, math

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "cool")
os.makedirs(OUT, exist_ok=True)


def parse_file(path, name):
    with open(path, encoding='utf-8', errors='ignore') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]
    third = lines[2] if len(lines) >= 3 else ''
    m = re.match(r'^\s*([\d,]+)', third)
    score = int(m.group(1).replace(',', '')) if m else 0
    pm = re.search(r'top\s+(\d+)%', third)
    pct = int(pm.group(1)) if pm else None
    date_label = lines[0].split('·')[-1].strip() if '·' in lines[0] else name
    month, day = map(int, name.split('_'))
    emoji_line = lines[1] if len(lines) >= 2 else ''
    return dict(file=name, month=month, day=day, date_label=date_label, score=score, pct=pct, emoji=emoji_line)


entries = []
_month_names = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
                7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"}
for _mnum, _mname in _month_names.items():
    _folder = os.path.join(ROOT, _mname)
    if os.path.isdir(_folder):
        for _fname in os.listdir(_folder):
            if re.match(r'^\d+_\d+$', _fname):
                _p = os.path.join(_folder, _fname)
                if os.path.isfile(_p):
                    entries.append(parse_file(_p, _fname))
        continue

_data_dir = os.path.join(ROOT, "data")
if os.path.isdir(_data_dir):
    for _sub in os.listdir(_data_dir):
        _subdir = os.path.join(_data_dir, _sub)
        if not os.path.isdir(_subdir):
            continue
        for _fname in os.listdir(_subdir):
            if re.match(r'^\d+_\d+$', _fname):
                _p = os.path.join(_subdir, _fname)
                if os.path.isfile(_p):
                    entries.append(parse_file(_p, _fname))

for name in os.listdir(ROOT):
    p = os.path.join(ROOT, name)
    if os.path.isfile(p) and re.match(r'^\d+_\d+$', name):
        try:
            _mm = int(name.split('_')[0])
            if _mm in _month_names and os.path.isdir(os.path.join(ROOT, _month_names[_mm])):
                continue
        except Exception:
            pass
        entries.append(parse_file(p, name))

entries.sort(key=lambda e: (e['month'], e['day']))

n = len(entries)
scores = [e['score'] for e in entries]
pcts = [e['pct'] or 0 for e in entries]
avg = sum(scores) / n
avg_pct = sum(pcts) / n

print("== MONTHLY ==")
months = {}
for e in entries:
    months.setdefault(e['month'], []).append(e)
mnames = {8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec', 1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul'}
for m in sorted(months):
    es = months[m]
    ms = [e['score'] for e in es]
    mp = [e['pct'] for e in es if e['pct'] is not None]
    best = max(es, key=lambda x: x['score'])
    worst = min(es, key=lambda x: x['score'])
    print(f"| {mnames[m]} 2026 | {len(es)} | {sum(ms)/len(ms):,.0f} | {best['score']:,} (`{best['file']}`) | {worst['score']:,} (`{worst['file']}`) | top {sum(mp)/len(mp):.0f}% |")

print("== TOP5 ==")
for rank, e in enumerate(sorted(entries, key=lambda x: -x['score'])[:5], 1):
    print(f"| {rank} | {e['date_label']} | `{e['file']}` | {e['score']:,} | top {e['pct']}% |")

# ---------------------------------------------------------------- svg helpers
W = 860
H = 420
ML, MR, MT, MB = 74, 40, 56, 58
PW = W - ML - MR
PH = H - MT - MB


def x_pos(i, count):
    if count == 1:
        return ML + PW / 2
    return ML + i * PW / (count - 1)


def header(x, y, w, h, title):
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#0d1117" stroke="#1f2937" stroke-width="1"/>',
        f'<text x="{x + w/2}" y="{y + 34}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="15" font-weight="600" fill="#e5e7eb" letter-spacing="2">{title.upper()}</text>',
    ]


# ------------------------------------------------ chart 1: score trend
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Score trend">']
y_min, y_max = 38000, 86000


def y_s(v):
    return MT + PH - (v - y_min) / (y_max - y_min) * PH


svg += header(0, 0, W, H, "score trend")
svg.append(f'<defs>'
           f'<filter id="glow1" x="-40%" y="-40%" width="180%" height="180%">'
           f'<feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
for t in [40000, 50000, 60000, 70000, 80000]:
    yy = y_s(t)
    svg.append(f'<line x1="{ML}" x2="{W - MR}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#1c2431" stroke-width="1"/>')
    svg.append(f'<text x="{ML - 10}" y="{yy + 4:.1f}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="11" fill="#64748b">{t//1000}k</text>')
pts = [(x_pos(i, n), y_s(v)) for i, v in enumerate(scores)]
d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
area = d + f" L {pts[-1][0]:.1f},{MT + PH:.1f} L {pts[0][0]:.1f},{MT + PH:.1f} Z"
# average is shown below the graph in the README caption
# trend line (line of best fit)
_xs = list(range(n))
_mx = sum(_xs) / n
_my = sum(scores) / n
_num = sum((x - _mx) * (y - _my) for x, y in zip(_xs, scores))
_den = sum((x - _mx) ** 2 for x in _xs) or 1
_m = _num / _den
_b = _my - _m * _mx
_y_end = _m * (n - 1) + _b
_x_end = x_pos(n - 1, n)
# glow pass so the trend line reads at a glance, then solid dashed line
svg.append(f'<line x1="{x_pos(0, n):.1f}" x2="{_x_end:.1f}" y1="{y_s(_b):.1f}" y2="{y_s(_y_end):.1f}" stroke="#fbbf24" stroke-width="4" opacity="0.3"/>')
svg.append(f'<line x1="{x_pos(0, n):.1f}" x2="{_x_end:.1f}" y1="{y_s(_b):.1f}" y2="{y_s(_y_end):.1f}" stroke="#fbbf24" stroke-width="1.8" stroke-dasharray="9 7"/>')
# glow line then real line
svg.append(f'<path d="{d}" fill="none" stroke="#22d3ee" stroke-width="6" opacity="0.35" filter="url(#glow1)" stroke-linecap="round" stroke-linejoin="round"/>')
svg.append(f'<path d="{area}" fill="#22d3ee" opacity="0.10"/>')
svg.append(f'<path d="{d}" fill="none" stroke="#22d3ee" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
i_max = scores.index(max(scores))
i_min = scores.index(min(scores))
for i, color, dy, anchor in [(i_max, "#4ade80", -16, "middle"), (i_min, "#f87171", 20, "middle")]:
    xx, yy = pts[i]
    svg.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="10" fill="none" stroke="{color}" stroke-width="1.4" opacity="0.8"/>')
    svg.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="4.5" fill="{color}"/>')
    label = f"{scores[i]:,}"
    svg.append(f'<text x="{xx:.1f}" y="{yy + dy:.1f}" text-anchor="{anchor}" font-family="Segoe UI, sans-serif" font-size="12.5" font-weight="700" fill="{color}">{label}</text>')
# x axis ticks every 5 games
for i in range(0, n, 5):
    xx = x_pos(i, n)
    e = entries[i]
    svg.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{MT + PH}" y2="{MT + PH + 5}" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{xx:.1f}" y="{H - 18}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10.5" fill="#64748b">{e["month"]}/{e["day"]}</text>')
svg.append('</svg>')
open(os.path.join(OUT, "score_trend.svg"), "w", encoding="utf-8").write("\n".join(svg))

# ------------------------------------------------ chart 2: percentile
W2, H2 = 860, 340
ML2, MT2, MB2 = 74, 56, 58
PW2, PH2 = W2 - ML2 - MR, H2 - MT2 - MB2
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}" role="img" aria-label="Percentile trend">']
p_min, p_max = 5, 95


def y_p(v):
    return MT2 + PH2 - (v - p_min) / (p_max - p_min) * PH2


svg += header(0, 0, W2, H2, "percentile trend")
svg.append(f'<defs>'
           f'<filter id="glow2" x="-40%" y="-40%" width="180%" height="180%">'
           f'<feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
for t in [20, 40, 60, 80]:
    yy = y_p(t)
    svg.append(f'<line x1="{ML2}" x2="{W2 - MR}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#1c2431" stroke-width="1"/>')
    svg.append(f'<text x="{ML2 - 10}" y="{yy + 4:.1f}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="11" fill="#64748b">top {t}%</text>')
svg.append(f'<text x="{ML2}" y="{MT2 - 14}" font-family="Segoe UI, sans-serif" font-size="11" fill="#94a3b8">percentile of players today — lower is better</text>')
pts2 = [(x_pos(i, n), y_p(v)) for i, v in enumerate(pcts)]
d2 = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts2)
area2 = d2 + f" L {pts2[-1][0]:.1f},{MT2 + PH2:.1f} L {pts2[0][0]:.1f},{MT2 + PH2:.1f} Z"
avy2 = y_p(avg_pct)
svg.append(f'<line x1="{ML2}" x2="{W2 - MR}" y1="{avy2:.1f}" y2="{avy2:.1f}" stroke="#475569" stroke-width="1.4" stroke-dasharray="6 6"/>')
svg.append(f'<text x="{W2 - MR - 6}" y="{avy2 - 7:.1f}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="11" fill="#94a3b8">avg top {avg_pct:.0f}%</text>')
svg.append(f'<path d="{d2}" fill="none" stroke="#34d399" stroke-width="6" opacity="0.3" filter="url(#glow2)" stroke-linecap="round" stroke-linejoin="round"/>')
svg.append(f'<path d="{area2}" fill="#34d399" opacity="0.10"/>')
svg.append(f'<path d="{d2}" fill="none" stroke="#34d399" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
i_best = pcts.index(min(pcts))
i_worst = pcts.index(max(pcts))
for i, color, dy in [(i_best, "#4ade80", -16), (i_worst, "#f87171", 20)]:
    xx, yy = pts2[i]
    svg.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="10" fill="none" stroke="{color}" stroke-width="1.4" opacity="0.8"/>')
    svg.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="4.5" fill="{color}"/>')
    svg.append(f'<text x="{xx:.1f}" y="{yy + dy:.1f}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="12.5" font-weight="700" fill="{color}">top {pcts[i]}%</text>')
for i in range(0, n, 5):
    xx = x_pos(i, n)
    epsilon = entries[i]
    svg.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{MT2 + PH2}" y2="{MT2 + PH2 + 5}" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{xx:.1f}" y="{H2 - 18}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10.5" fill="#64748b">{epsilon["month"]}/{epsilon["day"]}</text>')
svg.append('</svg>')
open(os.path.join(OUT, "percentile.svg"), "w", encoding="utf-8").write("\n".join(svg))

# ------------------------------------------------ chart 2b: average percentile over time
W2b, H2b = 860, 340
ML2b, MT2b, MB2b = 74, 56, 58
PW2b, PH2b = W2b - ML2b - MR, H2b - MT2b - MB2b
cum_pct = []
_s = 0
for i, v in enumerate(pcts):
    _s += v
    cum_pct.append(_s / (i + 1))
c_min, c_max = 45, 70


def y_c(v):
    return MT2b + PH2b - (v - c_min) / (c_max - c_min) * PH2b


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2b}" height="{H2b}" viewBox="0 0 {W2b} {H2b}" role="img" aria-label="Average percentile over time">']
svg += header(0, 0, W2b, H2b, "average percentile over time (lower is better)")
svg.append(f'<defs><filter id="glow3" x="-40%" y="-40%" width="180%" height="180%">'
           f'<feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
for t in [50, 55, 60, 65, 70]:
    yy = y_c(t)
    svg.append(f'<line x1="{ML2b}" x2="{W2b - MR}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#1c2431" stroke-width="1"/>')
    svg.append(f'<text x="{ML2b - 10}" y="{yy + 4:.1f}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="11" fill="#64748b">top {t}%</text>')
pts3 = [(x_pos(i, n), y_c(v)) for i, v in enumerate(cum_pct)]
d3 = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts3)
area3 = d3 + f" L {pts3[-1][0]:.1f},{MT2b + PH2b:.1f} L {pts3[0][0]:.1f},{MT2b + PH2b:.1f} Z"
svg.append(f'<path d="{area3}" fill="#34d399" opacity="0.10"/>')
svg.append(f'<path d="{d3}" fill="none" stroke="#34d399" stroke-width="6" opacity="0.3" filter="url(#glow3)" stroke-linecap="round" stroke-linejoin="round"/>')
svg.append(f'<path d="{d3}" fill="none" stroke="#34d399" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
xx, yy = pts3[-1]
svg.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="4.5" fill="#34d399"/>')
svg.append(f'<text x="{xx:.1f}" y="{yy - 12:.1f}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="12.5" font-weight="700" fill="#34d399">{cum_pct[-1]:.1f}%</text>')
for i in range(0, n, 5):
    xxx = x_pos(i, n)
    e3 = entries[i]
    svg.append(f'<line x1="{xxx:.1f}" x2="{xxx:.1f}" y1="{MT2b + PH2b}" y2="{MT2b + PH2b + 5}" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{xxx:.1f}" y="{H2b - 18}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10.5" fill="#64748b">{e3["month"]}/{e3["day"]}</text>')
svg.append('</svg>')
open(os.path.join(OUT, "percentile_cumulative.svg"), "w", encoding="utf-8").write("\n".join(svg))

# ------------------------------------------------ chart 3: recent 14 bars
W3, H3 = 860, 380
ML3, MT3, MB3 = 90, 56, 58
PW3, PH3 = W3 - ML3 - MR, H3 - MT3 - MB3
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W3}" height="{H3}" viewBox="0 0 {W3} {H3}" role="img" aria-label="Scores from last 14 games">']
svg += header(0, 0, W3, H3, "scores from last 14 games")
recent = entries[-14:]
slot = PW3 / 14
bar_w = 34
for i, e in enumerate(recent):
    xx = ML3 + i * slot + (slot - bar_w) / 2
    v = e['score']
    bh = (v - 38000) / (86000 - 38000) * PH3
    yy = MT3 + PH3 - bh
    svg.append(f'<rect x="{xx:.1f}" y="{yy:.1f}" width="{bar_w}" height="{bh:.1f}" rx="7" fill="#22d3ee" opacity="0.92"/>')
    svg.append(f'<text x="{xx + bar_w/2:.1f}" y="{yy - 8:.1f}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="11" font-weight="600" fill="#e5e7eb">{v//1000}k</text>')
    svg.append(f'<text x="{xx + bar_w/2:.1f}" y="{H3 - 18}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10.5" fill="#64748b">{e["month"]}/{e["day"]}</text>')
svg.append('</svg>')
open(os.path.join(OUT, "recent_bars.svg"), "w", encoding="utf-8").write("\n".join(svg))

# ------------------------------------------------ chart 4: tile donut
W4, H4 = 860, 300
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W4}" height="{H4}" viewBox="0 0 {W4} {H4}" role="img" aria-label="Tile percentages">']
svg += header(0, 0, W4, H4, "tile percentages")
emoji_to_info = {'🟨': ('Yellow', '#eab308'), '🟩': ('Green', '#22c55e'), '🟦': ('Blue', '#3b82f6'), '🟥': ('Red', '#ef4444')}
cc = collections.Counter()
for e in entries:
    cc.update(ch for ch in e['emoji'] if ch in emoji_to_info)
total = sum(cc.values())
segs = []
for em, (label, hexc) in emoji_to_info.items():
    segs.append((label, cc[em] / total * 100, cc[em], hexc, em))
segs.sort(key=lambda s: -s[1])
cx, cy, r, sw = 190, 170, 92, 30
circ = 2 * math.pi * r
offset = 0
gap = 4
for label, pct_v, cnt, hexc, em in segs:
    ln = circ * pct_v / 100 - gap
    if ln <= 0:
        continue
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{hexc}" stroke-width="{sw}" '
               f'stroke-dasharray="{ln:.2f} {circ - ln:.2f}" stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>')
    offset += circ * pct_v / 100
svg.append(f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="30" font-weight="700" fill="#e5e7eb">{total}</text>')
svg.append(f'<text x="{cx}" y="{cy + 22}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="12" fill="#64748b">TILES</text>')
lx = 400
ly = 96
for i, (label, pct_v, cnt, hexc, em) in enumerate(segs):
    yy = ly + i * 40
    svg.append(f'<rect x="{lx}" y="{yy - 11}" width="14" height="14" rx="4" fill="{hexc}"/>')
    svg.append(f'<text x="{lx + 24}" y="{yy + 2}" font-family="Segoe UI, sans-serif" font-size="14" fill="#e5e7eb">{em} {label} <tspan fill="#64748b">— {cnt} tiles</tspan></text>')
    svg.append(f'<text x="{lx + 300}" y="{yy + 2}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="13" font-weight="700" fill="#e5e7eb">{pct_v:.1f}%</text>')
svg.append('</svg>')
open(os.path.join(OUT, "tiles_donut.svg"), "w", encoding="utf-8").write("\n".join(svg))

print("total tiles:", total)
for label, pct_v, cnt, hexc, em in segs:
    print(f"  {label}: {cnt} ({pct_v:.1f}%)")
print("wrote charts to", OUT)

import os, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))

def svg_line_chart(labels, values, title="", y_min=None, y_max=None, y_ticks=None, extra_lines=None, height=340, width=780, show_dots=True, y_label="Score"):
    margin = dict(left=62, right=18, top=30, bottom=48)
    plot_w = width - margin['left'] - margin['right']
    plot_h = height - margin['top'] - margin['bottom']
    n = len(labels)
    if y_min is None: y_min = min(values) * 0.9
    if y_max is None: y_max = max(values) * 1.1
    if y_ticks is None:
        y_ticks = [y_min + i*(y_max - y_min)/4 for i in range(5)]
    def x_pos(i):
        if n == 1: return margin['left'] + plot_w/2
        return margin['left'] + i * plot_w / (n-1)
    def y_pos(v):
        return margin['top'] + plot_h - (v - y_min) / (y_max - y_min) * plot_h
    points = [(x_pos(i), y_pos(v)) for i,v in enumerate(values)]
    path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x,y in points)
    svg = []
    svg.append(f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">')
    svg.append(f'<rect width="{width}" height="{height}" fill="#0f1115" rx="12"/>')
    if title:
        svg.append(f'<text x="{width/2:.1f}" y="20" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="600" fill="#e6e6e6">{title}</text>')
    for yt in y_ticks:
        y = y_pos(yt)
        svg.append(f'<line x1="{margin["left"]}" x2="{width - margin["right"]}" y1="{y:.1f}" y2="{y:.1f}" stroke="#2a2f3a" stroke-width="1" stroke-dasharray="4 6"/>')
        label = f"{int(yt):,}" if yt >= 1000 else f"{yt:.0f}"
        svg.append(f'<text x="{margin["left"]-8}" y="{y+4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#9aa0ad">{label}</text>')
    for i, lab in enumerate(labels):
        x = x_pos(i)
        svg.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{margin["top"]+plot_h}" y2="{margin["top"]+plot_h+4}" stroke="#3a4150" stroke-width="1"/>')
        svg.append(f'<text x="{x:.1f}" y="{height - 14}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#9aa0ad">{lab}</text>')
    svg.append(f'<line x1="{margin["left"]}" x2="{margin["left"]}" y1="{margin["top"]}" y2="{margin["top"]+plot_h}" stroke="#3a4150" stroke-width="1.2"/>')
    svg.append(f'<line x1="{margin["left"]}" x2="{width - margin["right"]}" y1="{margin["top"]+plot_h}" y2="{margin["top"]+plot_h}" stroke="#3a4150" stroke-width="1.2"/>')
    svg.append(f'<text x="14" y="{margin["top"]+plot_h/2:.1f}" text-anchor="middle" transform="rotate(-90,14,{margin["top"]+plot_h/2:.1f})" font-family="sans-serif" font-size="11" fill="#9aa0ad">{y_label}</text>')
    if extra_lines:
        for el in extra_lines:
            ev = el["values"]
            pts = [(x_pos(i), y_pos(v)) for i,v in enumerate(ev)]
            d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x,y in pts)
            dash = f' stroke-dasharray="{el["dash"]}"' if el.get("dash") else ""
            svg.append(f'<path d="{d}" fill="none" stroke="{el.get("color","#888")}" stroke-width="{el.get("width",2)}" opacity="{el.get("opacity",0.9)}"{dash} stroke-linecap="round" stroke-linejoin="round"/>')
    svg.append(f'<path d="{path_d}" fill="none" stroke="#7aa5ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    area_d = path_d + f' L {points[-1][0]:.1f},{margin["top"]+plot_h:.1f} L {points[0][0]:.1f},{margin["top"]+plot_h:.1f} Z'
    svg.append(f'<path d="{area_d}" fill="#7aa5ff" opacity="0.08"/>')
    if show_dots:
        for (x,y), v, lab in zip(points, values, labels):
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#7aa5ff" stroke="#0f1115" stroke-width="1.5"><title>{lab}: {v:,}</title></circle>')
    max_v = max(values); min_v = min(values)
    for (x,y), v in zip(points, values):
        if v == max_v or v == min_v:
            dy = -10 if v==max_v else 14
            svg.append(f'<text x="{x:.1f}" y="{y+dy:.1f}" text-anchor="middle" font-family="sans-serif" font-size="10" font-weight="700" fill="#e6e6e6">{v:,}</text>')
    svg.append('</svg>')
    return "\n".join(svg)

def svg_bar_histogram(categories, title="Tile Color Distribution (160 tiles total)", width=780, height=300):
    # categories: list of dict {label, emoji, count, pct, color}
    margin = dict(left=90, right=30, top=36, bottom=30)
    plot_w = width - margin['left'] - margin['right']
    plot_h = height - margin['top'] - margin['bottom']
    bar_h = 36
    gap = 14
    total_h = len(categories)*(bar_h+gap)
    # centered vertically
    start_y = margin['top'] + (plot_h - total_h)/2 + 8
    max_pct = max(c['pct'] for c in categories) if categories else 100
    # round max to nice 50
    x_max = 50  # percentages go up to 50
    if max_pct > 50:
        x_max = 60
    svg=[]
    svg.append(f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">')
    svg.append(f'<rect width="{width}" height="{height}" fill="#0f1115" rx="12"/>')
    svg.append(f'<text x="{width/2:.1f}" y="22" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="600" fill="#e6e6e6">{title}</text>')
    # x axis grid
    for pct in [0,10,20,30,40,50]:
        x = margin['left'] + pct/x_max * plot_w
        svg.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{margin["top"]}" y2="{margin["top"]+plot_h}" stroke="#2a2f3a" stroke-width="1" stroke-dasharray="4 6"/>')
        svg.append(f'<text x="{x:.1f}" y="{margin["top"]+plot_h+14}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#9aa0ad">{pct}%</text>')
    for i, cat in enumerate(categories):
        y = start_y + i*(bar_h+gap)
        bar_w = cat['pct']/x_max * plot_w
        # label left
        svg.append(f'<text x="{margin["left"]-12}" y="{y+bar_h/2+4:.1f}" text-anchor="end" font-family="sans-serif" font-size="13" fill="#e6e6e6">{cat["emoji"]} {cat["label"]}</text>')
        # bar background
        svg.append(f'<rect x="{margin["left"]}" y="{y}" width="{plot_w}" height="{bar_h}" rx="6" fill="#1a1d24"/>')
        # bar foreground
        svg.append(f'<rect x="{margin["left"]}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="6" fill="{cat["color"]}" />')
        # text inside/outside
        label = f"{cat['count']} tiles · {cat['pct']:.1f}%"
        if bar_w > 140:
            svg.append(f'<text x="{margin["left"]+bar_w-8:.1f}" y="{y+bar_h/2+4:.1f}" text-anchor="end" font-family="sans-serif" font-size="12" font-weight="600" fill="#0f1115">{label}</text>')
        else:
            svg.append(f'<text x="{margin["left"]+bar_w+8:.1f}" y="{y+bar_h/2+4:.1f}" text-anchor="start" font-family="sans-serif" font-size="12" font-weight="600" fill="#e6e6e6">{label}</text>')
    svg.append('</svg>')
    return "\n".join(svg)

# --- parse data ---
entries=[]
for name in os.listdir(ROOT):
    p=os.path.join(ROOT,name)
    if os.path.isfile(p) and re.match(r'^\d+_\d+$', name):
        with open(p, encoding='utf-8', errors='ignore') as f:
            lines=[l.rstrip('\n') for l in f.readlines()]
        third=lines[2] if len(lines)>=3 else ''
        m=re.match(r'^\s*([\d,]+)', third)
        score=int(m.group(1).replace(',','')) if m else 0
        pm=re.search(r'top\s+(\d+)%',third)
        pct=int(pm.group(1)) if pm else None
        date_label=lines[0].split('·')[-1].strip() if '·' in lines[0] else name
        month,day=map(int,name.split('_'))
        emoji_line=lines[1] if len(lines)>=2 else ''
        entries.append(dict(file=name, month=month, day=day, date_label=date_label, score=score, pct=pct, emoji=emoji_line))
entries.sort(key=lambda e:(e['month'],e['day']))

labels=[f"{e['month']}/{e['day']}" for e in entries]
scores=[e['score'] for e in entries]
avg=sum(scores)/len(scores)
cum=[sum(scores[:i+1])/(i+1) for i in range(len(scores))]

# percentile handling
pcts = [e['pct'] for e in entries if e['pct'] is not None]
avg_pct = sum(pcts)/len(pcts) if pcts else 0
cum_pct = []
s=0
for i, v in enumerate(pcts):
    s+=v
    cum_pct.append(s/(i+1))

# tile colors
emoji_to_info = {
    '🟩': ('green', '#43a047'),
    '🟨': ('yellow', '#fdd835'),
    '🟦': ('blue', '#1e88e5'),
    '🟥': ('red', '#e53935'),
}
color_counts = collections.Counter()
per_file_colors=[]
for e in entries:
    c = collections.Counter(ch for ch in e['emoji'] if ch in emoji_to_info)
    per_file_colors.append(c)
    color_counts.update(c)
total_tiles = sum(color_counts.values())
# order for histogram: green, yellow, blue, red sorted by count desc? keep logical yellow, green, blue, red
color_order = ['🟨','🟩','🟦','🟥']
categories=[]
for em in color_order:
    label, col = emoji_to_info[em]
    cnt = color_counts.get(em, 0)
    pct = cnt/total_tiles*100 if total_tiles else 0
    categories.append(dict(emoji=em, label=label.capitalize(), count=cnt, pct=pct, color=col))

# --- generate SVGs ---
y_min, y_max = 35000, 80000
y_ticks = [35000,45000,55000,65000,75000]
avg_line = [avg]*len(labels)
svg_scores = svg_line_chart(
    labels, scores,
    title="Anthropeum — Score Over Time",
    y_min=y_min, y_max=y_max, y_ticks=y_ticks,
    extra_lines=[dict(values=avg_line, color="#f2c14e", dash="8 6", width=1.8, opacity=0.95)],
    y_label="Score"
)
cum_min, cum_max = 58000, 67000
cum_ticks = [58000,60000,62000,64000,66000]
svg_cum = svg_line_chart(
    labels, [round(c) for c in cum],
    title="Cumulative Average Score Over Time",
    y_min=cum_min, y_max=cum_max, y_ticks=cum_ticks,
    extra_lines=[dict(values=avg_line, color="#f2c14e", dash="8 6", width=1.8)],
    y_label="Avg Score"
)
svg_combined = svg_line_chart(
    labels, scores,
    title="Scores vs. Cumulative Average (overall avg dashed)",
    y_min=y_min, y_max=y_max, y_ticks=y_ticks,
    extra_lines=[
        dict(values=[round(c) for c in cum], color="#5ee1a8", dash="", width=2.2),
        dict(values=avg_line, color="#f2c14e", dash="8 6", width=1.6),
    ],
    y_label="Score"
)

# percentile chart: daily percentile (inverted y? lower is better so maybe invert, but keep normal with note)
# For percentile, 19 is best (top). We'll keep y 0(best) at top? Instead conventional y increases upward, so lower % at top is better. Let's invert: y_min 0, y_max 100, but display with 0 at top by setting y_min 100? Simpler: keep normal 0 bottom, but note gold avg line.
# We'll create a chart where y 20-95
pct_y_min, pct_y_max = 15, 95
pct_ticks = [20,40,60,80,90]
avg_pct_line = [avg_pct]*len(labels)
svg_pct_daily = svg_line_chart(
    labels, pcts,
    title="Percentile Over Time (lower is better)",
    y_min=pct_y_min, y_max=pct_y_max, y_ticks=pct_ticks,
    extra_lines=[dict(values=avg_pct_line, color="#f2c14e", dash="8 6", width=1.8)],
    y_label="Top %"
)
svg_pct_cum = svg_line_chart(
    labels, [round(v,1) for v in cum_pct],
    title="Cumulative Average Percentile Over Time",
    y_min=50, y_max=70, y_ticks=[50,55,60,65,70],
    extra_lines=[dict(values=avg_pct_line, color="#f2c14e", dash="8 6", width=1.8)],
    y_label="Avg Top %"
)

svg_colors = svg_bar_histogram(categories, title=f"Tile Color Distribution — {total_tiles} tiles total")

# write assets (only those used in README)
assets_dir = os.path.join(ROOT, "assets")
os.makedirs(assets_dir, exist_ok=True)
open(os.path.join(assets_dir, "scores.svg"), "w", encoding="utf-8").write(svg_scores)
open(os.path.join(assets_dir, "percentile.svg"), "w", encoding="utf-8").write(svg_pct_daily)
open(os.path.join(assets_dir, "percentile_cumulative.svg"), "w", encoding="utf-8").write(svg_pct_cum)
open(os.path.join(assets_dir, "colors.svg"), "w", encoding="utf-8").write(svg_colors)
# remove orphan cumulative score assets if they exist
for _orphan in ["cumulative.svg", "combined.svg"]:
    _p = os.path.join(assets_dir, _orphan)
    if os.path.exists(_p):
        try:
            os.remove(_p)
        except:
            pass

# --- build README ---
min_e = min(entries, key=lambda x:x['score'])
max_e = max(entries, key=lambda x:x['score'])
best_pct_e = min((e for e in entries if e['pct'] is not None), key=lambda x:x['pct'])
worst_pct_e = max((e for e in entries if e['pct'] is not None), key=lambda x:x['pct'])

table_rows = "\n".join(
    f"| {e['date_label']} | `{e['file']}` | {e['emoji']} | **{e['score']:,}** | top {e['pct']}% | {e['score']-avg:+,.0f} | "
    + " | ".join(str(per_file_colors[i].get(em, 0)) for em in color_order) + " |"
    for i, e in enumerate(entries)
)

# percentile table rows
pct_rows = "\n".join(
    f"| {e['date_label']} | top {e['pct']}% | {cum_pct[i]:.1f}% | {e['pct']-avg_pct:+.1f} |"
    for i, e in enumerate(entries)
)

# color distribution table rows
color_rows = "\n".join(
    f"| {c['emoji']} {c['label']} | {c['count']} | {c['pct']:.1f}% | `{c['color']}` |"
    for c in categories
)

readme = f"""# Anthropeum — Score History

Daily scores scraped from the files in this repo. Each file is named `M_D` (e.g. `8_13` → Aug 13) and line 3 holds the score (`64,497 · top 63% ...`). This README is auto-generated by `generate_readme.py` — re-run it after adding a new day.

## Data Table

| Date | File | Tiles | Score | Percentile | Δ vs Avg | 🟨 Yellow | 🟩 Green | 🟦 Blue | 🟥 Red |
|------|------|-------|-------|------------|----------|-----------|----------|---------|--------|
{table_rows}

## Scores Over Time

![Scores over time](assets/scores.svg)


## Percentile Over Time


![Percentile over time](assets/percentile.svg)


## Tile Color Distribution

![Tile colors](assets/colors.svg)




## Cumulative Average Percentile

![Cumulative percentile](assets/percentile_cumulative.svg)


## At a Glance

- **Average score:** **{avg:,.2f}**
- **Average percentile:** **top {avg_pct:.1f}%**
- **Best score:** **{max_e['score']:,}** (`{max_e['file']}`) — top {max_e['pct']}% 
- **Worst score:** **{min_e['score']:,}** (`{min_e['file']}`) — top {min_e['pct']}%
- **Best percentile:** top {best_pct_e['pct']}% (`{best_pct_e['file']}`) — {best_pct_e['score']:,}
- **Worst percentile:** top {worst_pct_e['pct']}% (`{worst_pct_e['file']}`) — {worst_pct_e['score']:,}
- **Median score:** {sorted(scores)[len(scores)//2]:,}
- **Range:** {max_e['score']-min_e['score']:,} ( {min_e['score']:,} → {max_e['score']:,})


## Raw Stats Dump

```
Count: {len(entries)}
Scores: {', '.join(f'{s:,}' for s in scores)}
Min: {min_e['score']:,} ({min_e['file']})  Max: {max_e['score']:,} ({max_e['file']})
Overall avg score: {avg:.2f}
Overall avg percentile: top {avg_pct:.2f}%
Cumulative avgs: {', '.join(f'{c:,.0f}' for c in cum)}
Cumulative avg percentiles: {', '.join(f'{c:.1f}%' for c in cum_pct)}
Tiles: {', '.join(f"{c['emoji']} {c['label']} {c['count']} ({c['pct']:.1f}%)" for c in categories)} — {total_tiles} total
```

---
*Generated from {len(entries)} files on disk. See `generate_readme.py` for logic.*
"""

with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write(readme)


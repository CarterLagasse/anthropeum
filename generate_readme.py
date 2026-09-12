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

def best_fit_line(values):
    n = len(values)
    if n < 2:
        return values[:]
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(values) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, values))
    den = sum((x - mx) ** 2 for x in xs) or 1
    m = num / den
    b = my - m * mx
    return [m * x + b for x in xs]

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
def _parse_file(p, name):
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
    return dict(file=name, month=month, day=day, date_label=date_label, score=score, pct=pct, emoji=emoji_line)

_month_names = {1:"january",2:"february",3:"march",4:"april",5:"may",6:"june",7:"july",8:"august",9:"september",10:"october",11:"november",12:"december"}

def load_entries(root):
    """All M_D files under root: month folders first, then root-level files for months without a folder."""
    entries=[]
    for _mnum, _mname in _month_names.items():
        _folder = os.path.join(root, _mname)
        if os.path.isdir(_folder):
            for _fname in os.listdir(_folder):
                if re.match(r'^\d+_\d+$', _fname):
                    _p = os.path.join(_folder, _fname)
                    if os.path.isfile(_p):
                        entries.append(_parse_file(_p, _fname))
    for name in os.listdir(root):
        p=os.path.join(root,name)
        if os.path.isfile(p) and re.match(r'^\d+_\d+$', name):
            try:
                _mm = int(name.split('_')[0])
                if _mm in _month_names and os.path.isdir(os.path.join(root, _month_names[_mm])):
                    continue
            except:
                pass
            entries.append(_parse_file(p, name))
    entries.sort(key=lambda e:(e['month'],e['day']))
    return entries

entries = load_entries(ROOT)

# other players keep the same file layout in a subfolder named after them
PLAYERS = [("Carter", ROOT), ("Ryan", os.path.join(ROOT, "ryan"))]

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
best_scores = best_fit_line(scores)
svg_scores = svg_line_chart(
    labels, scores,
    title="Anthropeum — Score Over Time",
    y_min=y_min, y_max=y_max, y_ticks=y_ticks,
    extra_lines=[dict(values=best_scores, color="#f2c14e", dash="8 6", width=1.8, opacity=0.95)],
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
best_pct = best_fit_line(pcts)
svg_pct_daily = svg_line_chart(
    labels, pcts,
    title="Percentile Over Time (lower is better)",
    y_min=pct_y_min, y_max=pct_y_max, y_ticks=pct_ticks,
    extra_lines=[dict(values=best_pct, color="#f2c14e", dash="8 6", width=1.8)],
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

# --- head to head ---
def _h2h_section(me_name, me_entries, others):
    out=[]
    for name, theirs in others:
        if not theirs:
            continue
        mine_by={(e['month'],e['day']):e for e in me_entries}
        theirs_by={(e['month'],e['day']):e for e in theirs}
        shared=sorted(set(mine_by)&set(theirs_by))
        t_scores=[e['score'] for e in theirs]
        t_pcts=[e['pct'] for e in theirs if e['pct'] is not None]
        t_best=max(theirs,key=lambda e:e['score'])
        t_avg=sum(t_scores)/len(t_scores)
        t_avg_pct=sum(t_pcts)/len(t_pcts) if t_pcts else 0
        lines=[f"## Head to Head — {me_name} vs {name}", "",
               f"{name}'s files live in `{name.lower()}/` with the same `M_D` layout. "
               f"{name}: **{len(theirs)}** games, avg **{t_avg:,.0f}**, avg percentile **top {t_avg_pct:.1f}%**, best **{t_best['score']:,}** (`{t_best['file']}`).", ""]
        if not shared:
            out.append("\n".join(lines)); continue
        labels=[f"{m}/{d}" for m,d in shared]
        mine=[mine_by[k]['score'] for k in shared]; other=[theirs_by[k]['score'] for k in shared]
        wins=sum(a>b for a,b in zip(mine,other)); losses=sum(a<b for a,b in zip(mine,other)); ties=len(shared)-wins-losses
        margin=[a-b for a,b in zip(mine,other)]
        m_avg=sum(mine)/len(mine); o_avg=sum(other)/len(other)
        m_pct=[mine_by[k]['pct'] for k in shared if mine_by[k]['pct'] is not None]
        o_pct=[theirs_by[k]['pct'] for k in shared if theirs_by[k]['pct'] is not None]
        big_w=max(range(len(shared)),key=lambda i:margin[i]); big_l=min(range(len(shared)),key=lambda i:margin[i])
        # streak of current leader
        streak=0; leader=None
        for a,b in reversed(list(zip(mine,other))):
            w = me_name if a>b else name if b>a else None
            if w is None: break
            if leader is None: leader=w
            if w!=leader: break
            streak+=1
        svg=svg_line_chart(labels, mine, title=f"{me_name} (blue) vs {name} (green) — days both played",
                           y_min=35000, y_max=90000, y_ticks=[35000,45000,55000,65000,75000,85000],
                           extra_lines=[dict(values=other, color="#5ee1a8", width=2.2, opacity=0.95)], y_label="Score")
        fname=f"h2h_{name.lower()}.svg"
        open(os.path.join(assets_dir, fname), "w", encoding="utf-8").write(svg)
        rows="\n".join(
            f"| {mine_by[k]['date_label']} | **{a:,}** (top {mine_by[k]['pct']}%) | **{b:,}** (top {theirs_by[k]['pct']}%) | {a-b:+,} | {me_name if a>b else name if b>a else 'tie'} |"
            for k,a,b in zip(shared,mine,other))
        lines += [f"![{me_name} vs {name}](assets/{fname})", "",
                  f"- **Record ({me_name}–{name}):** **{wins}–{losses}**" + (f"–{ties}" if ties else "") + f" over {len(shared)} shared days",
                  f"- **Average on shared days:** {me_name} {m_avg:,.0f} · {name} {o_avg:,.0f} ({m_avg-o_avg:+,.0f})",
                  f"- **Average percentile on shared days:** {me_name} top {sum(m_pct)/len(m_pct):.1f}% · {name} top {sum(o_pct)/len(o_pct):.1f}%" if m_pct and o_pct else "",
                  f"- **Biggest {me_name} win:** {margin[big_w]:+,} on {mine_by[shared[big_w]]['date_label']} · **Biggest {name} win:** {-margin[big_l]:+,} on {mine_by[shared[big_l]]['date_label']}",
                  f"- **Current run:** {leader} has won the last {streak}" if leader and streak>1 else "",
                  "", "<details>", f"<summary>Day by day — {len(shared)} shared days (click to expand)</summary>", "",
                  f"| Date | {me_name} | {name} | Δ | Winner |", "|------|------|------|---|--------|", rows, "", "</details>", ""]
        out.append("\n".join(l for l in lines if l is not None))
    return "\n".join(out)

_others=[(n, load_entries(pth)) for n,pth in PLAYERS[1:] if os.path.isdir(pth)]
h2h_section=_h2h_section(PLAYERS[0][0], entries, _others)

readme = f"""# Anthropeum — Score History

Daily scores scraped from the files in this repo. Each file is named `M_D` (e.g. `8_13` → Aug 13) and line 3 holds the score (`64,497 · top 63% ...`). Other players keep the same layout in a subfolder (e.g. `ryan/`). This README is auto-generated by `generate_readme.py` — re-run it after adding a new day.

## Data Table

<details>
<summary>Data Table — {len(entries)} rows (click to expand)</summary>

| Date | File | Tiles | Score | Percentile | Δ vs Avg | 🟨 Yellow | 🟩 Green | 🟦 Blue | 🟥 Red |
|------|------|-------|-------|------------|----------|-----------|----------|---------|--------|
{table_rows}

</details>

## Scores Over Time

![Scores over time](assets/scores.svg)


## Percentile Over Time


![Percentile over time](assets/percentile.svg)


## Tile Color Distribution

![Tile colors](assets/colors.svg)




## Cumulative Average Percentile

![Cumulative percentile](assets/percentile_cumulative.svg)


{h2h_section}
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


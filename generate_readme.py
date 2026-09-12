import os, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))

def svg_line_chart(labels, values, title="", y_min=None, y_max=None, y_ticks=None, extra_lines=None, height=340, width=780, show_dots=True, y_label="Score", color="#7aa5ff"):
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
    label_step = 2 if n > 20 else 1   # thin x labels on long series so they stay legible at half width
    for i, lab in enumerate(labels):
        x = x_pos(i)
        svg.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{margin["top"]+plot_h}" y2="{margin["top"]+plot_h+4}" stroke="#3a4150" stroke-width="1"/>')
        if i % label_step == 0 or i == n - 1:
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
    svg.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    area_d = path_d + f' L {points[-1][0]:.1f},{margin["top"]+plot_h:.1f} L {points[0][0]:.1f},{margin["top"]+plot_h:.1f} Z'
    svg.append(f'<path d="{area_d}" fill="{color}" opacity="0.08"/>')
    if show_dots:
        for (x,y), v, lab in zip(points, values, labels):
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}" stroke="#0f1115" stroke-width="1.5"><title>{lab}: {v:,}</title></circle>')
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
    if max_pct > 60:
        x_max = 100
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

# Players: (name, folder, asset subfolder, line colour). Carter's files stay at the repo root
# and his assets at assets/ so old links keep working; other players use a subfolder of each.
PLAYERS = [
    ("Carter", ROOT, "", "#7aa5ff"),
    ("Ryan", os.path.join(ROOT, "ryan"), "ryan", "#5ee1a8"),
]
PLAYERS = [pl for pl in PLAYERS if os.path.isdir(pl[1])]

emoji_to_info = {
    '🟩': ('green', '#43a047'),
    '🟨': ('yellow', '#fdd835'),
    '🟦': ('blue', '#1e88e5'),
    '🟥': ('red', '#e53935'),
}
color_order = ['🟨','🟩','🟦','🟥']
assets_dir = os.path.join(ROOT, "assets")
os.makedirs(assets_dir, exist_ok=True)

def nice_range(values, step, pad=0.0):
    lo = min(values) - pad; hi = max(values) + pad
    lo = int(lo // step) * step
    hi = int(-(-hi // step)) * step
    if hi == lo: hi = lo + step
    ticks = list(range(lo, hi + 1, step))
    while len(ticks) > 7:            # keep the axis readable
        ticks = ticks[::2]
        if ticks[-1] != hi: ticks.append(hi)
    return lo, hi, ticks

def build_player(name, entries, sub, color, ranges):
    """Compute every stat and write every chart for one player. Returns a dict for the README."""
    P = {}
    P['name']=name; P['entries']=entries; P['color']=color
    P['labels']=[f"{e['month']}/{e['day']}" for e in entries]
    scores=[e['score'] for e in entries]; P['scores']=scores
    P['avg']=sum(scores)/len(scores)
    P['cum']=[sum(scores[:i+1])/(i+1) for i in range(len(scores))]
    pcts=[e['pct'] for e in entries if e['pct'] is not None]; P['pcts']=pcts
    P['avg_pct']=sum(pcts)/len(pcts) if pcts else 0
    cum_pct=[]; s=0
    for i,v in enumerate(pcts):
        s+=v; cum_pct.append(s/(i+1))
    P['cum_pct']=cum_pct
    counts=collections.Counter(); per_file=[]
    for e in entries:
        c=collections.Counter(ch for ch in e['emoji'] if ch in emoji_to_info)
        per_file.append(c); counts.update(c)
    total=sum(counts.values()); P['total_tiles']=total; P['per_file_colors']=per_file
    P['categories']=[dict(emoji=em, label=emoji_to_info[em][0].capitalize(), count=counts.get(em,0),
                          pct=(counts.get(em,0)/total*100 if total else 0), color=emoji_to_info[em][1]) for em in color_order]
    P['min_e']=min(entries,key=lambda x:x['score']); P['max_e']=max(entries,key=lambda x:x['score'])
    with_pct=[e for e in entries if e['pct'] is not None]
    P['best_pct_e']=min(with_pct,key=lambda x:x['pct']); P['worst_pct_e']=max(with_pct,key=lambda x:x['pct'])
    P['median']=sorted(scores)[len(scores)//2]

    d = os.path.join(assets_dir, sub) if sub else assets_dir
    os.makedirs(d, exist_ok=True)
    rel = f"assets/{sub}/" if sub else "assets/"
    P['asset']=lambda f: rel + f

    y0,y1,yt = ranges['score']
    open(os.path.join(d,"scores.svg"),"w",encoding="utf-8").write(svg_line_chart(
        P['labels'], scores, title=f"{name} — Score Over Time", y_min=y0, y_max=y1, y_ticks=yt,
        extra_lines=[dict(values=best_fit_line(scores), color="#f2c14e", dash="8 6", width=1.8, opacity=0.95)], y_label="Score", color=color))
    p0,p1,pt = ranges['pct']
    open(os.path.join(d,"percentile.svg"),"w",encoding="utf-8").write(svg_line_chart(
        P['labels'], pcts, title=f"{name} — Percentile Over Time (lower is better)", y_min=p0, y_max=p1, y_ticks=pt,
        extra_lines=[dict(values=best_fit_line(pcts), color="#f2c14e", dash="8 6", width=1.8)], y_label="Top %", color=color))
    c0,c1,ct = ranges['cum_pct']
    open(os.path.join(d,"percentile_cumulative.svg"),"w",encoding="utf-8").write(svg_line_chart(
        P['labels'], [round(v,1) for v in cum_pct], title=f"{name} — Cumulative Average Percentile", y_min=c0, y_max=c1, y_ticks=ct,
        extra_lines=[dict(values=[P['avg_pct']]*len(pcts), color="#f2c14e", dash="8 6", width=1.8)], y_label="Avg Top %", color=color))
    open(os.path.join(d,"colors.svg"),"w",encoding="utf-8").write(svg_bar_histogram(
        P['categories'], title=f"{name} — Tile Color Distribution — {total} tiles total"))
    for _orphan in ["cumulative.svg", "combined.svg"]:
        _p=os.path.join(d,_orphan)
        if os.path.exists(_p):
            try: os.remove(_p)
            except: pass

    P['table_rows']="\n".join(
        f"| {e['date_label']} | `{e['file']}` | {e['emoji']} | **{e['score']:,}** | top {e['pct']}% | {e['score']-P['avg']:+,.0f} | "
        + " | ".join(str(per_file[i].get(em,0)) for em in color_order) + " |" for i,e in enumerate(entries))
    P['raw']=f"""Count: {len(entries)}
Scores: {', '.join(f'{v:,}' for v in scores)}
Min: {P['min_e']['score']:,} ({P['min_e']['file']})  Max: {P['max_e']['score']:,} ({P['max_e']['file']})
Overall avg score: {P['avg']:.2f}
Overall avg percentile: top {P['avg_pct']:.2f}%
Cumulative avgs: {', '.join(f'{c:,.0f}' for c in P['cum'])}
Cumulative avg percentiles: {', '.join(f'{c:.1f}%' for c in cum_pct)}
Tiles: {', '.join(f"{c['emoji']} {c['label']} {c['count']} ({c['pct']:.1f}%)" for c in P['categories'])} — {total} total"""
    return P

# shared axis ranges so side-by-side charts are directly comparable
_all=[(n, load_entries(pth), sub, col) for n,pth,sub,col in PLAYERS]
_all_scores=[e['score'] for _,es,_,_ in _all for e in es]
_all_pcts=[e['pct'] for _,es,_,_ in _all for e in es if e['pct'] is not None]
_all_cum=[]
for _,es,_,_ in _all:
    ps=[e['pct'] for e in es if e['pct'] is not None]; s=0
    for i,v in enumerate(ps):
        s+=v; _all_cum.append(s/(i+1))
ranges = dict(score=nice_range(_all_scores, 10000, pad=2000), pct=nice_range(_all_pcts, 10, pad=3), cum_pct=nice_range(_all_cum, 5, pad=1))
players=[build_player(n, es, sub, col, ranges) for n,es,sub,col in _all]
me=players[0]

# --- head to head ---
def _h2h_section(me, others):
    out=[]
    for other in others:
        mine_by={(e['month'],e['day']):e for e in me['entries']}
        theirs_by={(e['month'],e['day']):e for e in other['entries']}
        shared=sorted(set(mine_by)&set(theirs_by))
        if not shared:
            continue
        A,B=me['name'],other['name']
        labels=[f"{m}/{d}" for m,d in shared]
        a_s=[mine_by[k]['score'] for k in shared]; b_s=[theirs_by[k]['score'] for k in shared]
        wins=sum(a>b for a,b in zip(a_s,b_s)); losses=sum(a<b for a,b in zip(a_s,b_s)); ties=len(shared)-wins-losses
        margin=[a-b for a,b in zip(a_s,b_s)]
        a_avg=sum(a_s)/len(a_s); b_avg=sum(b_s)/len(b_s)
        a_p=[mine_by[k]['pct'] for k in shared if mine_by[k]['pct'] is not None]
        b_p=[theirs_by[k]['pct'] for k in shared if theirs_by[k]['pct'] is not None]
        big_w=max(range(len(shared)),key=lambda i:margin[i]); big_l=min(range(len(shared)),key=lambda i:margin[i])
        streak=0; leader=None
        for a,b in reversed(list(zip(a_s,b_s))):
            w = A if a>b else B if b>a else None
            if w is None: break
            if leader is None: leader=w
            if w!=leader: break
            streak+=1
        y0,y1,yt=ranges['score']
        fname=f"h2h_{B.lower()}.svg"
        open(os.path.join(assets_dir,fname),"w",encoding="utf-8").write(svg_line_chart(
            labels, a_s, title=f"{A} (blue) vs {B} (green) — days both played", y_min=y0, y_max=y1, y_ticks=yt,
            extra_lines=[dict(values=b_s, color=other['color'], width=2.2, opacity=0.95)], y_label="Score", color=me['color']))
        rows="\n".join(
            f"| {mine_by[k]['date_label']} | **{a:,}** (top {mine_by[k]['pct']}%) | **{b:,}** (top {theirs_by[k]['pct']}%) | {a-b:+,} | {A if a>b else B if b>a else 'tie'} |"
            for k,a,b in zip(shared,a_s,b_s))
        lines=[f"## Head to Head — {A} vs {B}", "",
               f"![{A} vs {B}](assets/{fname})", "",
               f"- **Record ({A}–{B}):** **{wins}–{losses}**" + (f"–{ties}" if ties else "") + f" over {len(shared)} shared days",
               f"- **Average on shared days:** {A} {a_avg:,.0f} · {B} {b_avg:,.0f} ({a_avg-b_avg:+,.0f})"]
        if a_p and b_p:
            lines.append(f"- **Average percentile on shared days:** {A} top {sum(a_p)/len(a_p):.1f}% · {B} top {sum(b_p)/len(b_p):.1f}%")
        lines.append(f"- **Biggest {A} win:** {margin[big_w]:+,} on {mine_by[shared[big_w]]['date_label']} · **Biggest {B} win:** {-margin[big_l]:+,} on {mine_by[shared[big_l]]['date_label']}")
        if leader and streak>1:
            lines.append(f"- **Current run:** {leader} has won the last {streak}")
        lines += ["", "<details>", f"<summary>Day by day — {len(shared)} shared days (click to expand)</summary>", "",
                  f"| Date | {A} | {B} | Δ | Winner |", "|------|------|------|---|--------|", rows, "", "</details>", ""]
        out.append("\n".join(lines))
    return "\n".join(out)

h2h_section=_h2h_section(me, players[1:]) if len(players)>1 else ""

# --- side-by-side helpers ---
def side_by_side(asset_name):
    cells="".join(f'<td width="{100//len(players)}%" valign="top"><img src="{P["asset"](asset_name)}" alt="{P["name"]} {asset_name}" width="100%"></td>' for P in players)
    heads="".join(f'<th align="center">{P["name"]}</th>' for P in players)
    return f'<table width="100%"><tr>{heads}</tr><tr>{cells}</tr></table>'

def glance_table():
    cols=" | ".join(P['name'] for P in players)
    rows=[f"| Metric | {cols} |", "|---|" + "---|"*len(players)]
    def row(label, fn): rows.append(f"| **{label}** | " + " | ".join(fn(P) for P in players) + " |")
    row("Games", lambda P: f"{len(P['entries'])}")
    row("Average score", lambda P: f"**{P['avg']:,.0f}**")
    row("Median score", lambda P: f"{P['median']:,}")
    row("Average percentile", lambda P: f"**top {P['avg_pct']:.1f}%**")
    row("Best score", lambda P: f"**{P['max_e']['score']:,}** (`{P['max_e']['file']}`, top {P['max_e']['pct']}%)")
    row("Worst score", lambda P: f"{P['min_e']['score']:,} (`{P['min_e']['file']}`, top {P['min_e']['pct']}%)")
    row("Best percentile", lambda P: f"top {P['best_pct_e']['pct']}% (`{P['best_pct_e']['file']}`, {P['best_pct_e']['score']:,})")
    row("Worst percentile", lambda P: f"top {P['worst_pct_e']['pct']}% (`{P['worst_pct_e']['file']}`, {P['worst_pct_e']['score']:,})")
    row("Range", lambda P: f"{P['max_e']['score']-P['min_e']['score']:,}")
    for em in color_order:
        lab=emoji_to_info[em][0].capitalize()
        row(f"{em} {lab} tiles", lambda P, em=em: next(f"{c['count']} ({c['pct']:.1f}%)" for c in P['categories'] if c['emoji']==em))
    return "\n".join(rows)

def data_tables():
    out=[]
    for P in players:
        out.append(f"""<details>
<summary>{P['name']} — {len(P['entries'])} rows (click to expand)</summary>

| Date | File | Tiles | Score | Percentile | Δ vs Avg | 🟨 Yellow | 🟩 Green | 🟦 Blue | 🟥 Red |
|------|------|-------|-------|------------|----------|-----------|----------|---------|--------|
{P['table_rows']}

</details>
""")
    return "\n".join(out)

def raw_dumps():
    return "\n".join(f"""<details>
<summary>{P['name']}</summary>

```
{P['raw']}
```

</details>
""" for P in players)

player_note = " · ".join(f"**{P['name']}** — `{'./' if i==0 else PLAYERS[i][2]+'/'}`" for i,P in enumerate(players))
n_files = sum(len(P['entries']) for P in players)

readme = f"""# Anthropeum — Score History

Daily scores scraped from the files in this repo. Each file is named `M_D` (e.g. `8_13` → Aug 13) and line 3 holds the score (`64,497 · top 63% ...`). Players: {player_note}. This README is auto-generated by `generate_readme.py` — re-run it after adding a new day.

{h2h_section}
## At a Glance

{glance_table()}

## Scores Over Time

{side_by_side("scores.svg")}

## Percentile Over Time

{side_by_side("percentile.svg")}

## Tile Color Distribution

{side_by_side("colors.svg")}

## Cumulative Average Percentile

{side_by_side("percentile_cumulative.svg")}

## Data Tables

{data_tables()}
## Raw Stats Dump

{raw_dumps()}
---
*Generated from {n_files} files on disk. See `generate_readme.py` for logic.*
"""

with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write(readme)

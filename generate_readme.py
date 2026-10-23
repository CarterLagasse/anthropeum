import os, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))

# Full year used for the stat-file archive folders. The Archive daily stats
# workflow strips this to two digits when naming folders (data/M_YY).
YEAR = 2026

_MONTH_NAMES = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may",
                6: "june", 7: "july", 8: "august", 9: "september", 10: "october",
                11: "november", 12: "december"}
_ABBR = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
         7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}


def parse_file(path, name):
    with open(path, encoding='utf-8', errors='ignore') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]
    third = lines[2] if len(lines) >= 3 else ''
    m = re.match(r'^\s*([\d,]+)', third)
    score = int(m.group(1).replace(',', '')) if m else 0
    pm = re.search(r'top\s+(\d+)%', third)
    pct = int(pm.group(1)) if pm else None
    date_label = lines[0].split('·')[-1].strip() if '·' in lines[0] else name
    ym = re.search(r'\b(20\d{2})\b', date_label)
    year = int(ym.group(1)) if ym else YEAR
    month, day = map(int, name.split('_'))
    emoji_line = lines[1] if len(lines) >= 2 else ''
    return dict(file=name, month=month, day=day, year=year, date_label=date_label,
                score=score, pct=pct, emoji=emoji_line)


def scan(folder):
    out = []
    for fname in os.listdir(folder):
        if re.match(r'^\d+_\d+$', fname):
            p = os.path.join(folder, fname)
            if os.path.isfile(p):
                out.append(parse_file(p, fname))
    return out


entries, _seen = [], set()
# legacy month-name folders (august/, september/, ...)
for _mnum, _mname in _MONTH_NAMES.items():
    _folder = os.path.join(ROOT, _mname)
    if os.path.isdir(_folder):
        for e in scan(_folder):
            if e['file'] not in _seen:
                _seen.add(e['file'])
                entries.append(e)
# data/ archive subfolders (e.g. data/8_26/, data/10_26/)
_data_dir = os.path.join(ROOT, "data")
if os.path.isdir(_data_dir):
    for _sub in sorted(os.listdir(_data_dir)):
        _subdir = os.path.join(_data_dir, _sub)
        if os.path.isdir(_subdir):
            for e in scan(_subdir):
                if e['file'] not in _seen:
                    _seen.add(e['file'])
                    entries.append(e)
# loose files in root
for e in scan(ROOT):
    if e['file'] not in _seen:
        _seen.add(e['file'])
        entries.append(e)
entries.sort(key=lambda e: (e['year'], e['month'], e['day']))

n = len(entries)
scores = [e['score'] for e in entries]
avg = sum(scores) / n
srt = sorted(scores)
median = srt[n // 2]

best_e = max(entries, key=lambda e: e['score'])
worst_e = min(entries, key=lambda e: e['score'])

# percentiles: the running average ends at its lowest point (lower is better)
pct_entries = [e for e in entries if e['pct'] is not None]
avg_pct = sum(e['pct'] for e in pct_entries) / len(pct_entries)
first_pct_e = pct_entries[0] if pct_entries else None
best_pct_e = min(pct_entries, key=lambda e: e['pct'])


def dmon(e):
    """'Aug 13' style short date."""
    return f"{_ABBR[e['month']]} {e['day']}"


# --- personal bests (top 5 scores) ---
best_rows = "\n".join(
    f"| {i + 1} | {dmon(e)} | {e['emoji']} | **{e['score']:,}** | top {e['pct']}% |"
    for i, e in enumerate(sorted(entries, key=lambda e: e['score'], reverse=True)[:5])
)

# --- month by month table ---
month_rows = []
_groups = collections.OrderedDict()
for e in entries:
    _groups.setdefault((e['year'], e['month']), []).append(e)
for (yr, mo), es in _groups.items():
    mscores = [e['score'] for e in es]
    mpcts = [e['pct'] for e in es if e['pct'] is not None]
    m_best = max(es, key=lambda e: e['score'])
    m_worst = min(es, key=lambda e: e['score'])
    m_avgpct = f"top {round(sum(mpcts) / len(mpcts))}%" if mpcts else "—"
    month_rows.append(
        f"| {_ABBR[mo]} {yr} | {len(es)} | {round(sum(mscores) / len(es)):,} "
        f"| {m_best['score']:,} (`{m_best['file']}`) "
        f"| {m_worst['score']:,} (`{m_worst['file']}`) | {m_avgpct} |"
    )
month_rows = "\n".join(month_rows)

# --- game log ---
log_rows = "\n".join(
    f"| {dmon(e)} | {e['emoji']} | {e['score']:,} | top {e['pct']}% |" for e in entries
)

readme = f"""## This repo tracks my [`Anthropeum`](https://anthropeum.com) scores

### Avg score: **{avg:,.0f}** · Best score: **{best_e['score']:,}** · Best percentile: **top {best_pct_e['pct']}%**

## Personal bests

| # | Date | Tiles | Score | Percentile |
|:-:|:-----|:------|------:|:----------:|
{best_rows}

---

## The trail

![Score trend](assets/charts/score_trend.svg)

*Best: {best_e['score']:,} on {dmon(best_e)} (top {best_e['pct']}%) · Worst: {worst_e['score']:,} on {dmon(worst_e)} · Average: {avg:,.0f} · Range: {best_e['score'] - worst_e['score']:,}.*

![Average percentile over time](assets/charts/percentile_cumulative.svg)

*Avg percentile: top {first_pct_e['pct']}% on {dmon(first_pct_e)} → top {round(avg_pct)}% now.*

---

## Recent form

![Recent form](assets/charts/recent_bars.svg)

*All-time average: {avg:,.0f} · Median: {median:,}.*

---

## Month by month

| Month | Games | Avg Score | Best | Worst | Avg Percentile |
|:------|:-----:|----------:|------|-------|---------------:|
{month_rows}

---

## Artifact breakdown

![Artifact breakdown](assets/charts/tiles_donut.svg)

---

## Game log

<details>
<summary>All {n} games</summary>

| Date | Tiles | Score | Percentile |
|:-----|:------|------:|:----------:|
{log_rows}

</details>
"""

with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write(readme)
print(f"README.md written from {n} games")

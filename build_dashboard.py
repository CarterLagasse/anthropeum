"""Update the game data inside index.html from the daily stat files. Standard library only.

Only the `const GAMES = ...` line changes, so hand edits to the page are kept.

    python build_dashboard.py
"""
import datetime, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, 'index.html')
TILES = {'🟦': 'B', '🟩': 'G', '🟨': 'Y', '🟥': 'R'}
BAND = {'B': (9000, 10000), 'G': (6000, 8999), 'Y': (3000, 5999), 'R': (0, 2999)}


def parse_game(path):
    """Return one game, or raise ValueError saying what is wrong with the file."""
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    if len(lines) < 3:
        raise ValueError('expected 3 lines')
    date = re.search(r'·\s*([A-Z][a-z]{2} \d{1,2} \d{4})', lines[0])
    result = re.match(r'\s*([\d,]+)\s*·\s*top (\d+)%', lines[2])
    tiles = ''.join(TILES[c] for c in lines[1] if c in TILES)
    if not date or not result or len(tiles) != 10:
        raise ValueError('could not read the date, tiles or score')
    score = int(result.group(1).replace(',', ''))
    low = sum(BAND[t][0] for t in tiles)
    high = sum(BAND[t][1] for t in tiles)
    if not low <= score <= high:
        raise ValueError(f'score {score:,} is outside the {low:,} to {high:,} its tiles allow')
    return dict(date=datetime.datetime.strptime(date.group(1), '%b %d %Y').date().isoformat(),
                tiles=tiles, score=score, pct=int(result.group(2)))


def find_stat_files():
    folders = [ROOT]
    for folder, _, _ in os.walk(os.path.join(ROOT, 'data')):
        folders.append(folder)
    for folder in folders:
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if re.fullmatch(r'\d+_\d+', name) and os.path.isfile(path):
                yield path


def main():
    games, problems = {}, []
    for path in find_stat_files():
        try:
            game = parse_game(path)
        except ValueError as err:
            problems.append(f'{os.path.relpath(path, ROOT)}: {err}')
            continue
        if game['date'] in games:
            problems.append(f"{os.path.relpath(path, ROOT)}: second file for {game['date']}")
            continue
        games[game['date']] = game
    if problems:
        sys.exit('Fix these stat files, then rebuild:\n  ' + '\n  '.join(problems))
    if not games:
        sys.exit('No stat files found')

    ordered = [games[d] for d in sorted(games)]
    with open(PAGE, encoding='utf-8', newline='') as f:
        page = f.read()
    line = 'const GAMES = ' + json.dumps(ordered, separators=(',', ':')) + ';'
    page, found = re.subn(r'^const GAMES = .*;(?=\r?$)', lambda _: line, page, count=1, flags=re.M)
    if not found:
        sys.exit('Could not find the "const GAMES = ..." line in index.html')
    with open(PAGE, 'w', encoding='utf-8', newline='') as f:
        f.write(page)
    print(f"Updated index.html: {len(ordered)} games, {ordered[0]['date']} to {ordered[-1]['date']}")


if __name__ == '__main__':
    main()

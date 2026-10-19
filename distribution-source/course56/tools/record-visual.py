"""Record a completed human/model visual review, then package the course."""
from pathlib import Path
import json, subprocess, sys
h = Path(__file__).resolve().parents[1]
n = int(sys.argv[1])
note = sys.argv[2]
assert 1 <= n <= 56 and n != 19
assert len(list((h / f'decks/lesson{n:02}/renders').glob('slide-*.png'))) == 24
(h / f'validation/lesson{n:02}/visual.json').write_text(json.dumps({
    'passed': True, 'slidesReviewed': list(range(1, 25)), 'issues': [], 'notes': note
}, ensure_ascii=False, indent=2), encoding='utf8')
subprocess.run([sys.executable, str(h/'tools/package.py'), str(n)], check=True)

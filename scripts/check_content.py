"""Offline checks for links, source records and publication hygiene."""
from pathlib import Path
from urllib.parse import unquote
import json
import re

root = Path(__file__).resolve().parents[1]
errors = []
sources = json.loads((root / 'data/sources.json').read_text(encoding='utf-8'))
ids = [s['id'] for s in sources]
if len(ids) != len(set(ids)):
    errors.append('Duplicate source IDs')
required = {'id', 'publisher', 'title', 'published_date', 'data_period', 'checked_at', 'verification', 'url', 'summary', 'boundary'}
for source in sources:
    if not required.issubset(source):
        errors.append(f'Missing fields: {source.get("id")}')
    if source['verification'] not in {'A', 'B', 'C'}:
        errors.append(f'Invalid status: {source["id"]}')
    if not source['url'].startswith('https://'):
        errors.append(f'Invalid URL: {source["id"]}')
for path in root.rglob('*.md'):
    text = path.read_text(encoding='utf-8')
    if re.search(r'(?:[A-Z]:[\\/]|/Users/|/mnt/|\ue200|\ue202)', text):
        errors.append(f'Private path or tool token: {path.relative_to(root)}')
    for link in re.findall(r'\]\(([^)]+)\)', text):
        if re.match(r'^(?:https?://|mailto:)', link):
            continue
        target, _, anchor = unquote(link).partition('#')
        linked = (path.parent / target).resolve() if target else path
        if not linked.exists():
            errors.append(f'Broken link {path.relative_to(root)} -> {link}')
        elif anchor and linked.suffix == '.md' and re.fullmatch(r's\d+', anchor):
            if f'id="{anchor}"' not in linked.read_text(encoding='utf-8'):
                errors.append(f'Broken source anchor: {link}')
for report in ['automation-survey-v0.1.docx', 'automation-survey-v0.1.pdf']:
    if not (root / 'reports' / report).is_file():
        errors.append(f'Missing report: {report}')
if list(root.glob('LICENSE*')):
    errors.append('Unexpected license file')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(sources)} sources, all local links and source anchors valid; reports present.')

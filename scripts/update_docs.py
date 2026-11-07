#!/usr/bin/env python3
"""Generate traceability navigation from stable Python symbols; --check verifies it."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/verification/coverage.md'
REGISTRY = ROOT / 'docs/verification/traceability.json'


def link(path, label, fragment=''):
    target = ROOT / path
    if not target.is_file():
        raise ValueError(f'Missing file: {path}')
    relative = os.path.relpath(target, OUTPUT.parent).replace(os.sep, '/')
    return f'[{label}]({relative}{fragment})'


def source_link(entry):
    path, symbol = entry['path'], entry.get('symbol')
    if not symbol:
        return link(path, f'`{Path(path).name}`')
    node = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    for name in symbol.split('.'):
        matches = [child for child in node.body
                   if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                   and child.name == name]
        if len(matches) != 1:
            raise ValueError(f'Unknown or ambiguous symbol: {path}:{symbol}')
        node = matches[0]
    return link(path, f'`{symbol}`', f'#L{node.lineno}')


def render(entries):
    lines = [
        '# Vazby požadavků, implementace a testů', '',
        'Generováno z [traceability.json](traceability.json) příkazem '
        '`python3 scripts/update_docs.py`. Tento soubor neupravujte ručně.', '',
        'Vazba na test označuje související ověření, nikoli výsledek jeho posledního běhu. '
        'Mapování vychází ze stávající dokumentace a symbolů v kódu; '
        'kontrola platnosti požadavků podle zadání je samostatný další krok.', '',
        '[Požadavky](../requirements/README.md) · [Ověřování](README.md) · '
        '[Zpětné vazby z kódu a testů](#zpětné-vazby-z-kódu-a-testů)', '',
    ]
    reverse = {}
    seen = set()
    for entry in entries:
        identifier = entry['id']
        if identifier in seen:
            raise ValueError(f'Duplicate requirement ID: {identifier}')
        seen.add(identifier)
        lines += [f'## {identifier}', '', link(entry['page'], entry['title']), '',
                  '**Pravidla:** ' + (', '.join(link('docs/requirements/business-rules.md', rule, '#'+rule.lower()) for rule in entry['rules']) or 'Podmínky a oprávnění jsou uvedené přímo u požadavku.'), '',
                  '**Návrh:** ' + ' · '.join(link(path, Path(path).stem) for path in entry['design']), '']
        for category, title in [('implementation', 'Implementace'), ('tests', 'Testy')]:
            lines += [f'### {title}', '']
            for source in entry[category]:
                rendered = source_link(source)
                lines.append('- ' + rendered)
                key = (source['path'], source.get('symbol', '(celý soubor)'))
                reverse.setdefault(key, {'link': rendered, 'ids': []})
                if identifier not in reverse[key]['ids']:
                    reverse[key]['ids'].append(identifier)
            lines.append('')
    lines += ['## Zpětné vazby z kódu a testů', '',
              'Vyhledejte název metody nebo testu a otevřete související požadavek.', '',
              '| Soubor | Symbol | Požadavky |', '| --- | --- | --- |']
    pages = {entry['id']: entry['page'] for entry in entries}
    for (path, symbol), item in sorted(reverse.items()):
        ids = ', '.join(link(pages[identifier], identifier) for identifier in item['ids'])
        lines.append(f'| {link(path, Path(path).name)} | {item["link"]} | {ids} |')
    return '\n'.join(lines) + '\n'


def check_links():
    errors = []
    for page in [ROOT / 'README.md', ROOT / 'assigments/README.md', *(ROOT / 'docs').rglob('*.md')]:
        for raw in re.findall(r'\]\(([^)]+)\)', page.read_text(encoding='utf-8')):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', raw):
                continue
            path, _, fragment = unquote(raw).partition('#')
            target = (page.parent / path).resolve() if path else page
            if not target.is_file():
                errors.append(f'{page.relative_to(ROOT)}: missing {raw}')
                continue
            if fragment and target.suffix == '.py':
                match = re.fullmatch(r'L(\d+)', fragment)
                if not match or not 1 <= int(match[1]) <= len(target.read_text().splitlines()):
                    errors.append(f'{page.relative_to(ROOT)}: invalid source location {raw}')
            elif fragment and target.suffix == '.md':
                text = target.read_text(encoding='utf-8')
                anchors = set(re.findall(r'<a id="([^"]+)"', text))
                counts = {}
                for heading in re.findall(r'^#{1,6}\s+(.+)', text, re.M):
                    slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
                    count = counts.get(slug, 0)
                    counts[slug] = count + 1
                    anchors.add(slug + (f'-{count}' if count else ''))
                if fragment not in anchors:
                    errors.append(f'{page.relative_to(ROOT)}: missing anchor {raw}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify without writing files')
    args = parser.parse_args()
    try:
        content = render(json.loads(REGISTRY.read_text(encoding='utf-8')))
        if args.check:
            if not OUTPUT.is_file() or OUTPUT.read_text(encoding='utf-8') != content:
                raise ValueError('coverage.md is stale; run python3 scripts/update_docs.py')
        else:
            OUTPUT.write_text(content, encoding='utf-8')
        errors = check_links()
        if errors:
            raise ValueError('\n'.join(errors))
    except (ValueError, OSError, KeyError, SyntaxError) as error:
        print(error, file=sys.stderr)
        return 1
    print('Documentation links and traceability are up to date.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

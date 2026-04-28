#!/usr/bin/env python3
"""Rebuild _all_notes.json from individual JSON files in data/"""
import json, os, re
from pathlib import Path

data_dir = Path('data')
output_file = data_dir / '_all_notes.json'

# Find all individual note JSONs (exclude _all_notes.json)
files = sorted([f for f in data_dir.glob('*.json') if f.name != '_all_notes.json'])

notes = []
for f in files:
    try:
        with open(f) as fp:
            note = json.load(fp)
        # Validate required fields
        if not all(k in note for k in ('nid', 'title', 'body_html')):
            print(f'WARNING: {f.name} missing required fields, skipping')
            continue
        notes.append(note)
    except json.JSONDecodeError as e:
        print(f'ERROR: {f.name} is invalid JSON: {e}')

with open(output_file, 'w') as fp:
    json.dump(notes, fp, indent=2)

print(f'Rebuilt {output_file} with {len(notes)} notes')

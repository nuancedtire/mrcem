#!/usr/bin/env python3
"""
Resequence sort_order values in affected subcategories.
Preserves relative order; renumbers from 1 with no gaps.
"""
import json
import glob
import os

BASE = '/home/user/mrcem/data'

DIRS = [
    # Pathology subcategories with changes
    f'{BASE}/pathology/neurology-and-neurosurgery',
    f'{BASE}/pathology/cardiorespiratory-pathology',
    f'{BASE}/pathology/infectious-disease-and-immunology',
    f'{BASE}/pathology/haematology-and-oncology',
    # Physiology subcategories with changes
    f'{BASE}/physiology/endocrine-physiology',
    f'{BASE}/physiology/renal-physiology',
    f'{BASE}/physiology/gi-physiology',
]

for dirpath in DIRS:
    files = glob.glob(f'{dirpath}/*.json')
    if not files:
        continue

    # Load and sort by current sort_order
    notes = []
    for fpath in files:
        with open(fpath) as f:
            data = json.load(f)
        notes.append((data.get('sort_order', 0), fpath, data))

    notes.sort(key=lambda x: x[0])

    # Renumber from 1
    changed = 0
    for new_sort, (old_sort, fpath, data) in enumerate(notes, start=1):
        if old_sort != new_sort:
            data['sort_order'] = new_sort
            with open(fpath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            changed += 1

    label = dirpath.split('/data/')[1]
    print(f'{label}: {len(notes)} notes, {changed} resequenced')

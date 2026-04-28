#!/usr/bin/env python3
"""
Sort order cleanup:
1. In key subcategories, move "basic introduction" and overview notes to sort=1,2,3
2. Resequence all subcategories that had notes added/removed in phases A-F
"""
import json, glob, os, re

BASE = '/home/user/mrcem/data'

def resequence(dirpath, priority_nids=None):
    """
    Renumber sort_orders from 1 with no gaps.
    priority_nids: list of nids to place first (in given order), rest follows original order.
    """
    files = glob.glob(f'{dirpath}/*.json')
    if not files:
        print(f'  (empty): {dirpath.split("/data/")[1]}')
        return

    notes = []
    for fpath in files:
        with open(fpath) as f:
            d = json.load(f)
        notes.append((d.get('sort_order', 0), d.get('nid', ''), fpath, d))

    notes.sort(key=lambda x: x[0])

    if priority_nids:
        priority_set = {n: i for i, n in enumerate(priority_nids)}
        priority_notes = [n for n in notes if n[1] in priority_set]
        priority_notes.sort(key=lambda n: priority_set[n[1]])
        rest = [n for n in notes if n[1] not in priority_set]
        notes = priority_notes + rest

    changed = 0
    for new_sort, (old_sort, nid, fpath, data) in enumerate(notes, start=1):
        if old_sort != new_sort:
            data['sort_order'] = new_sort
            with open(fpath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            changed += 1

    label = dirpath.split('/data/')[1]
    print(f'  {label}: {len(notes)} notes, {changed} resequenced')


# ─── Subcategories with intro notes to front-prioritise ─────────────────────

# Cardiorespiratory: basic intro notes should be first
resequence(f'{BASE}/pathology/cardiorespiratory-pathology',
    priority_nids=['2_2425', '2_2421', '2_2422'])  # ACS, Asthma, Pneumonia intros

# GI & Endocrine: basic intro notes should be first
resequence(f'{BASE}/pathology/gi-and-endocrine-pathology',
    priority_nids=['2_2419', '2_2423', '2_2429'])  # Abdominal pain, DM, Thyroid intros

# Neurology & Neurosurgery: stroke and epilepsy intros first
resequence(f'{BASE}/pathology/neurology-and-neurosurgery',
    priority_nids=['2_2433', '2_2434'])  # Stroke intro, Epilepsy intro

# ─── All other affected subcategories: just resequence ──────────────────────

dirs_to_resequence = [
    f'{BASE}/pathology/renal-and-urological-pathology',
    f'{BASE}/pathology/infectious-disease-and-immunology',
    f'{BASE}/pathology/haematology-and-oncology',
    f'{BASE}/pathology/rheumatology-dermatology-and-women-s-health',
    f'{BASE}/microbiology/bacteriology',
]
for d in dirs_to_resequence:
    resequence(d)

print('\nSort order fixes complete.')

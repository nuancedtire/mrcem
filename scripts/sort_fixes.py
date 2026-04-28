#!/usr/bin/env python3
"""
Sort order fixes identified by audit:
  1. Bacteriology: Staphylococci overview buried at position 24 → move to front with S.aureus/S.epidermidis
  2. Pharmacology/Neuropsych: General anaesthetics overview at position 19 → move to front with anaesthetic agents
  3. GI & Endocrine: DM type 2 diagnosis at position 74 → move to position 3 (after DM intro)
"""
import json, glob, os

BASE = '/home/user/mrcem/data'

def resequence(dirpath, priority_nids=None):
    files = glob.glob(f'{dirpath}/*.json')
    if not files:
        print(f'  (empty): {dirpath}')
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


# 1. Bacteriology: group staphylococci together at the top
print('1. Bacteriology — Staphylococci overview to front...')
resequence(f'{BASE}/microbiology/bacteriology',
    priority_nids=[
        '2_737',   # Staphylococci: overview
        '1_293',   # Staphylococcus aureus
        '1_2897',  # Staphylococcus epidermidis
    ])

# 2. Pharmacology/Neuropsych: general anaesthetics overview first, then anaesthetic agents
print('2. Pharmacology/Neuropsych — General anaesthetics to front...')
resequence(f'{BASE}/pharmacology/neuropsych-and-anaesthesia',
    priority_nids=[
        '2_2048',  # General anaesthetics (overview)
        '1_85',    # Etomidate
        '1_2779',  # Ketamine
        '1_219',   # Nitrous oxide
        '1_254',   # Propofol
        '1_349',   # Thiopental sodium
        '1_41',    # Local anaesthesia
        '1_204',   # Muscle relaxants
        '1_298',   # Suxamethonium
        '2_2080',  # Neuromuscular blocking drugs
    ])

# 3. GI & Endocrine: DM T2 diagnosis pulled up to position 3
print('3. GI & Endocrine — DM type 2 diagnosis after DM intro...')
resequence(f'{BASE}/pathology/gi-and-endocrine-pathology',
    priority_nids=[
        '2_2419',  # Abdominal pain: a very basic introduction (existing pos 1)
        '2_2423',  # Diabetes mellitus: a very basic introduction (existing pos 2)
        '2_624',   # Diabetes mellitus (type 2): diagnosis  ← promoted from pos 74
        '2_1134',  # Diabetic ketoacidosis
        '2_1186',  # DVLA: diabetes mellitus
        '2_2429',  # Thyroid intro (was in original priority list)
    ])

print('\nSort fixes complete.')

#!/usr/bin/env python3
"""
Assign subcategories to the 31 Evidence-Based Medicine notes.
Updates subcategorynum, subcategoryname in body_html and sort_order in each JSON.
"""
import json
import re
import os
import glob

BASE = '/home/user/mrcem/data/evidenced-based-medicine'

# Map: nid → (subcategorynum, subcategoryname, new_sort_order)
EBM_ASSIGNMENTS = {
    # Subcategory 1 — Foundational Concepts
    '1_76':   (1, 'Foundational Concepts', 1),   # EBM Definitions
    '1_2907': (1, 'Foundational Concepts', 2),   # Data types
    '1_132':  (1, 'Foundational Concepts', 3),   # Hierarchy of evidence
    '1_34':   (1, 'Foundational Concepts', 4),   # Bias
    '1_189':  (1, 'Foundational Concepts', 5),   # Measures of central tendency
    '1_2908': (1, 'Foundational Concepts', 6),   # Measures of variation
    '1_2906': (1, 'Foundational Concepts', 7),   # Standard deviation / empirical rule

    # Subcategory 2 — Distributions & Descriptive Statistics
    '2_793':  (2, 'Distributions & Descriptive Statistics', 8),   # Normal distribution
    '2_797':  (2, 'Distributions & Descriptive Statistics', 9),   # Skewed distributions
    '2_1886': (2, 'Distributions & Descriptive Statistics', 10),  # Statistical terms
    '2_794':  (2, 'Distributions & Descriptive Statistics', 11),  # Confidence interval & SEM
    '2_1639': (2, 'Distributions & Descriptive Statistics', 12),  # Correlation & regression

    # Subcategory 3 — Hypothesis Testing & Study Design
    '1_2909': (3, 'Hypothesis Testing & Study Design', 13),  # Sample size & power
    '2_795':  (3, 'Hypothesis Testing & Study Design', 14),  # Significance tests: type I & II
    '2_796':  (3, 'Hypothesis Testing & Study Design', 15),  # Significance tests: parametric
    '2_1638': (3, 'Hypothesis Testing & Study Design', 16),  # Study design
    '1_2911': (3, 'Hypothesis Testing & Study Design', 17),  # Observational studies
    '2_1558': (3, 'Hypothesis Testing & Study Design', 18),  # Intention to treat

    # Subcategory 4 — Risk, Screening & Diagnostic Tests
    '1_2914': (4, 'Risk, Screening & Diagnostic Tests', 19),  # ROC curve
    '2_496':  (4, 'Risk, Screening & Diagnostic Tests', 20),  # Screening test statistics
    '1_169':  (4, 'Risk, Screening & Diagnostic Tests', 21),  # Statistics: sensitivity/specificity
    '2_1642': (4, 'Risk, Screening & Diagnostic Tests', 22),  # Absolute risk / RRR / NNT
    '2_1620': (4, 'Risk, Screening & Diagnostic Tests', 23),  # NNT, NNH, ARR
    '2_1641': (4, 'Risk, Screening & Diagnostic Tests', 24),  # Odds & odds ratio

    # Subcategory 5 — Epidemiology & Evidence Synthesis
    '1_2912': (5, 'Epidemiology & Evidence Synthesis', 25),  # Incidence / prevalence
    '1_2910': (5, 'Epidemiology & Evidence Synthesis', 26),  # Survival analysis
    '1_2915': (5, 'Epidemiology & Evidence Synthesis', 27),  # Systematic review
    '1_2913': (5, 'Epidemiology & Evidence Synthesis', 28),  # Forest plot
    '2_1795': (5, 'Epidemiology & Evidence Synthesis', 29),  # Funnel plot
    '2_1872': (5, 'Epidemiology & Evidence Synthesis', 30),  # Scoring systems
    '2_1631': (5, 'Epidemiology & Evidence Synthesis', 31),  # Evidence-based recovery times
}

def update_meta(html: str, subcategorynum: int, subcategoryname: str) -> str:
    html = re.sub(
        r'(<div id="subcategorynum">)[^<]*(</div>)',
        rf'\g<1>{subcategorynum}\g<2>',
        html
    )
    html = re.sub(
        r'(<div id="subcategoryname">)[^<]*(</div>)',
        rf'\g<1>{subcategoryname}\g<2>',
        html
    )
    return html

files = glob.glob(f'{BASE}/*.json')
matched = 0

for fpath in files:
    with open(fpath) as f:
        data = json.load(f)

    nid = data.get('nid', '')
    if nid not in EBM_ASSIGNMENTS:
        print(f'  WARNING: unrecognised nid {nid} in {os.path.basename(fpath)}')
        continue

    subcat_num, subcat_name, new_sort = EBM_ASSIGNMENTS[nid]
    data['body_html'] = update_meta(data['body_html'], subcat_num, subcat_name)
    data['sort_order'] = new_sort

    with open(fpath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'  [{subcat_num}] sort={new_sort:2d} | {data["title"][:55]}')
    matched += 1

print(f'\nUpdated {matched}/{len(files)} EBM notes.')

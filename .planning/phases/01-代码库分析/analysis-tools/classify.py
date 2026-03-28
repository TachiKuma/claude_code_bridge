#!/usr/bin/env python3
import json
import re
from pathlib import Path

PROTOCOL_PATTERNS = [
    r'^[A-Z_]{3,}$',
    r'^CCB_[A-Z_]+$',
    r'^GSD_[A-Z_]+$',
    r'_DONE$',
    r'^ask\.[a-z_]+$',
    r'^\.[a-z]+$',
]

def classify_string(text):
    """Classify string as 'protocol' or 'human'"""
    if not text.strip() or len(text) == 1:
        return None

    for pattern in PROTOCOL_PATTERNS:
        if re.match(pattern, text):
            return 'protocol'

    return 'human'

def main():
    results_dir = Path(__file__).parent.parent / 'results'

    ccb_file = results_dir / 'ccb_strings.json'
    gsd_file = results_dir / 'gsd_strings.json'

    all_strings = []

    if ccb_file.exists():
        with open(ccb_file, 'r', encoding='utf-8') as f:
            all_strings.extend(json.load(f))

    if gsd_file.exists():
        with open(gsd_file, 'r', encoding='utf-8') as f:
            all_strings.extend(json.load(f))

    protocol = []
    human = []

    for item in all_strings:
        category = classify_string(item['value'])
        if category == 'protocol':
            protocol.append(item)
        elif category == 'human':
            human.append(item)

    output = {
        'protocol': protocol,
        'human': human,
        'stats': {
            'total': len(all_strings),
            'protocol': len(protocol),
            'human': len(human)
        }
    }

    output_file = results_dir / 'classified.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Classification complete:")
    print(f"  Total: {output['stats']['total']}")
    print(f"  Protocol: {output['stats']['protocol']}")
    print(f"  Human: {output['stats']['human']}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Dyadic entry point to the shared PSC-1.5.1 group processor.

Use the same analysis engine as six-beetle runs so pile, movement, fungus,
paired raw/PSC tables, and PDF rules cannot silently diverge.
"""
from persistent_groups import MODEL_VERSION
from six_beetle_processor import SCRIPT_VERSION, main


if __name__ == '__main__':
    if MODEL_VERSION != '1.5.1' or SCRIPT_VERSION != '0.8.1-group':
        raise SystemExit(f'Outdated dyadic PSC code: {MODEL_VERSION} / {SCRIPT_VERSION}')
    main()

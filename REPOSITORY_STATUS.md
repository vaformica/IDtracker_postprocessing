# Repository status · 2026-09-28

The **current** pipeline is the shared PSC model 1.5.1 with group processor 0.8.1-group. It supports dyadic and larger groups. `processor.py` and `VERSION=0.8.1` are the historical standalone prototype; do not use that version label to describe current PSC releases.

The official 2024 GroupTrial collection has 26 six-beetle trials of 9,000 frames from each TOML start. The official 2026 dyadic collection has 99 eligible trials of 7,200 frames from each TOML start. Both have release receipts, manifests, raw/PSC data, PDFs, and viewer videos. The automatic inferences are **UNREVIEWED**. The dyadic set excludes four incompatible TOMLs and one TOML for which IDtracker found no blobs. See [the project handoff](reports/PROJECT_HANDOFF_2026-09-28.md) for exact paths and hashes.

`persistent_groups.py` implements the shared PSC rules; `six_beetle_processor.py` is the current analysis implementation, also used by `dyadic_processor.py`. `group_firebird_gui.py` is the general GUI, `dyadic_firebird_gui.py` opens its dyad filter, and `idtracker_toml_gui.py` submits IDtracker tracking jobs. [GROUP_PIPELINE_README.md](GROUP_PIPELINE_README.md) contains the CLI and review workflow. [DATA_DICTIONARY.md](DATA_DICTIONARY.md) describes raw and PSC fields.

The 2026-09-28 local software check passed 133 `unittest` tests. The parity receipt confirms identical PSC core code and parameters for the two official releases. This is software/provenance parity, not independent biological validation. Per-run human review remains the next scientific step.

Git tracks source and small guidance. `outputs/`, `tmp/`, local annotations, videos, caches and downloaded ZIPs are working data and ignored for new files. Three earlier small `outputs/` records remain tracked; the older 71 MB derived video was removed from the current Git index while its local copy and provenance record were preserved. Historical commits still contain it, so this does not by itself recover local Git-object space. Do not rewrite history or delete source data as part of ordinary repository cleanup.
